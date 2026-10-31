"""The semantic layer reaches the report: a cap removal outranks a harmless edit, NLI can clear a rewording."""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from legalpulse_reasoning import pipeline
from legalpulse_reasoning.comparison.aligner import align_versions
from legalpulse_reasoning.comparison.embedders import BagOfWordsEmbedder
from legalpulse_reasoning.risk.scorer import score_risk

EMB = BagOfWordsEmbedder()


def clause(v, k, text, head="Clause"):
    return {"clause_id": f"x{v}_{k}", "number": str(k), "heading": f"{head} {k}", "text": text, "parties": [],
            "obligation_type": "general", "deadline": None, "defined_terms": [], "references": []}


def pair(old_texts, new_texts):
    mk = lambda v, ts: {"contract_id": f"x{v}", "version": v, "clauses": [clause(v, i + 1, t) for i, t in enumerate(ts)], "contradictions": []}
    return mk("v1", old_texts), mk("v2", new_texts)


FILLER = ["Governing law of this agreement is the law of India and the courts at Delhi have exclusive jurisdiction over every dispute.",
          "Each party shall keep the confidential information of the other party secret during the term and for five years afterwards."]
CAP_OLD = "The total liability of the Supplier under this agreement is limited to the fees paid by the Client in the previous twelve months."
CAP_NEW = "The total liability of the Supplier under this agreement is unlimited for all losses suffered by the Client in the previous twelve months."
WORD_OLD = "The Supplier shall promptly notify the Client in writing of any delay in the delivery of the goods ordered under this agreement."
WORD_NEW = "The Supplier shall quickly notify the Client in writing of any delay in the delivery of the goods ordered under this agreement."


def test_semantic_bonus_raises_the_score():
    plain = score_risk({"change_type": "modified"}, [], False)
    sem = score_risk({"change_type": "modified", "semantic": {"severity_hint": 0.95}}, [], False)
    assert sem["score"] > plain["score"] and sem["components"]["semantic"] == round(0.2 * 0.95, 2)
    assert score_risk({"change_type": "deleted", "semantic": {"severity_hint": 1.0}}, [1] * 9, True)["score"] <= 1.0


def test_cap_removal_is_explained_and_ranked_above_a_harmless_edit():
    old, new = pair([CAP_OLD, WORD_OLD] + FILLER, [CAP_NEW, WORD_NEW] + FILLER)
    rep = pipeline.run(old, new, EMB)
    top = rep["risks"][0]
    assert top["trigger_clause"] == "xv2_1" and top["explanation"].startswith("cap removed")
    harmless = next(r for r in rep["risks"] if r["trigger_clause"] == "xv2_2")
    assert top["score"] > harmless["score"]


def test_nli_confirms_a_harmless_rewording():
    old, new = pair([WORD_OLD] + FILLER, [WORD_NEW] + FILLER)
    same = lambda pairs: [{"entailment": 0.97, "neutral": 0.02, "contradiction": 0.01} for _ in pairs]
    ch = [c for c in align_versions(old, new, EMB, semantic_scorer=same) if c["old_clause_ids"] == ["xv1_1"]][0]
    assert ch["change_type"] == "unchanged" and "NLI" in ch["summary"]
    assert not [r for r in pipeline.run(old, new, EMB, semantic_scorer=same)["risks"] if r["trigger_clause"] == "xv2_1"]


def test_nli_contradiction_is_reported_and_raises_severity():
    old, new = pair([WORD_OLD] + FILLER, [WORD_NEW] + FILLER)
    clash = lambda pairs: [{"entailment": 0.02, "neutral": 0.08, "contradiction": 0.90} for _ in pairs]
    ch = [c for c in align_versions(old, new, EMB, semantic_scorer=clash) if c["old_clause_ids"] == ["xv1_1"]][0]
    assert ch["change_type"] == "modified" and ch["semantic"]["severity_hint"] >= 0.8
    assert "contradicts" in ch["semantic"]["reasons"][0]


def test_without_an_nli_scorer_nothing_changes():
    old, new = pair([WORD_OLD] + FILLER, [WORD_NEW] + FILLER)
    ch = [c for c in align_versions(old, new, EMB) if c["old_clause_ids"] == ["xv1_1"]][0]
    assert ch["change_type"] == "modified" and ch["semantic"]["reasons"] == []


def test_a_deleted_clause_with_a_cap_outranks_a_number_change():
    """Removing the liability cap must rank above moving a payment term (it used to rank below it)."""
    cap = "The total liability of the Supplier under this agreement is limited to the fees paid by the Client in the previous twelve months."
    pay = "The Client shall pay each invoice within 30 days of receipt of the invoice issued by the Supplier under this agreement."
    pay2 = pay.replace("30 days", "60 days")
    old, new = pair([pay, cap] + FILLER, [pay2] + FILLER)
    rep = pipeline.run(old, new, EMB)
    removed = next(r for r in rep["risks"] if "removed" in r["explanation"].lower())
    moved = next(r for r in rep["risks"] if r["trigger_clause"] == "xv2_1")
    assert "cap or limit" in removed["explanation"] and removed["score"] > moved["score"]
