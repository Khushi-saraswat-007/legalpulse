"""Structure pass: a heavily rewritten clause that keeps its slot is 'modified', an unrelated replacement is not."""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from legalpulse_reasoning import config
from legalpulse_reasoning.comparison.aligner import align_versions
from legalpulse_reasoning.comparison.embedders import BagOfWordsEmbedder

EMB = BagOfWordsEmbedder()
TEXTS = {
    1: "The Supplier shall provide the software services described in the schedule to the Client during the term of this agreement and shall maintain adequate staff for that purpose.",
    2: "The Client shall pay the Supplier the agreed fees within thirty days of receipt of each invoice issued under this agreement together with applicable taxes.",
    3: "The total liability of the Supplier arising from this agreement shall be limited to the fees paid by the Client during the preceding twelve months before the claim arose.",
    4: "Either party may terminate this agreement by giving sixty days written notice to the other party at the address specified in the notices clause of this agreement.",
    5: "This agreement is governed by the laws of India and the courts at Delhi shall have exclusive jurisdiction over any dispute arising out of or relating to it.",
}
HEADS = {1: "Services", 2: "Payment", 3: "Limitation of Liability", 4: "Termination", 5: "Governing Law"}


def contract(version, overrides=None):
    overrides = overrides or {}
    cl = []
    for k in range(1, 6):
        text, head = overrides.get(k, (TEXTS[k], HEADS[k]))
        cl.append({"clause_id": f"c{version}_{k}", "number": str(k), "heading": head, "text": text,
                   "parties": [], "obligation_type": "general", "deadline": None, "defined_terms": [], "references": []})
    return {"contract_id": f"c{version}", "version": version, "clauses": cl, "contradictions": []}


# a real-looking rewrite: same slot and heading, similarity ~0.37 (above the structure threshold, below the normal one)
REWRITTEN = ("Whatever the cause, the Supplier accepts responsibility for every loss or damage suffered by the Client "
             "in connection with the services and the liability of the Supplier is not limited.")
UNRELATED = ("The Client grants the Supplier a non-exclusive licence to use the Client trademarks solely for the purpose of "
             "identifying the Client as a customer in marketing materials approved in advance in writing.")


def kinds(changes):
    return {tuple(c["old_clause_ids"]): c for c in changes}


def test_rewritten_clause_in_same_slot_is_modified_not_deleted():
    old, new = contract("v1"), contract("v2", {3: (REWRITTEN, "Limitation of Liability")})
    ch = kinds(align_versions(old, new, EMB))
    assert ch[("cv1_3",)]["change_type"] == "modified"
    assert ch[("cv1_3",)]["new_clause_ids"] == ["cv2_3"]
    assert ch[("cv1_3",)]["match_basis"] == "structure"


def test_without_the_structure_pass_the_same_edit_is_deleted_and_added():
    config.USE_STRUCTURE_PASS = False
    try:
        out = align_versions(contract("v1"), contract("v2", {3: (REWRITTEN, "Limitation of Liability")}), EMB)
    finally:
        config.USE_STRUCTURE_PASS = True
    types = sorted(c["change_type"] for c in out if c["change_type"] in ("deleted", "added"))
    assert types == ["added", "deleted"]


def test_unrelated_replacement_stays_deleted_and_added():
    out = align_versions(contract("v1"), contract("v2", {3: (UNRELATED, "Trademark Licence")}), EMB)
    types = sorted(c["change_type"] for c in out if c["change_type"] in ("deleted", "added"))
    assert types == ["added", "deleted"]
    assert all(c.get("match_basis") != "structure" for c in out)


def test_moved_clause_is_not_used_as_an_anchor():
    old = contract("v1")
    new = contract("v2")
    new["clauses"][0], new["clauses"][4] = new["clauses"][4], new["clauses"][0]      # swap clause 1 and 5
    out = align_versions(old, new, EMB)
    assert not [c for c in out if c["change_type"] in ("deleted", "added")]
