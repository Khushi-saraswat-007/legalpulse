import pytest

from legalpulse_nlp import RuleBasedNLIBackend, detect_contradictions, extract_from_text
from legalpulse_nlp.contradiction import candidate_pairs, is_explicit_carveout
from legalpulse_nlp.errors import NLIModelError
from legalpulse_nlp.nli import HFNLIBackend


def clauses_of(text):
    return extract_from_text(text, "t").contract["clauses"]


class FakeBackend:
    """Scripted model so we can test the plumbing (thresholds, order handling) deterministically."""
    name = "fake"

    def __init__(self, fwd, rev):
        self.fwd, self.rev, self.calls = fwd, rev, 0

    def predict(self, pairs):
        self.calls += 1
        p = self.fwd if self.calls % 2 == 1 else self.rev
        return [{"entailment": 0.0, "contradiction": p, "neutral": 1 - p} for _ in pairs]


LEASE = """1. Termination Notice
Tenant may not terminate during the first 6 months and must give 30 days notice thereafter.
2. Early Exit
Tenant may terminate this lease at any time without notice.
3. Rent
Tenant shall pay Rent of 25,000 rupees monthly.
"""


def test_rule_baseline_flags_real_conflict():
    recs = detect_contradictions(clauses_of(LEASE), backend=RuleBasedNLIBackend())
    pairs = {(r["clause_a"], r["clause_b"]) for r in recs}
    assert ("t_1", "t_2") in pairs
    assert all(r["label"] == "contradiction" and 0 < r["score"] <= 1 for r in recs)
    assert recs[0]["explanation"]


def test_related_but_compatible_clauses_not_flagged():
    txt = ("1. Payment\nBuyer shall pay invoices within 30 days.\n"
           "2. Late Fee\nA late fee applies if Buyer does not pay invoices within 30 days.\n")
    assert detect_contradictions(clauses_of(txt), backend=RuleBasedNLIBackend()) == []


def test_notwithstanding_override_is_not_a_contradiction():
    txt = ("1. Termination\nLicensor may terminate this agreement if Licensee breaches Clause 4.\n"
           "2. Restrictions\nLicensee shall not copy the Software.\n"
           "3. Protection\nNotwithstanding anything in Clause 1, Licensor may not terminate this agreement during the first 12 months.\n")
    cl = clauses_of(txt)
    assert is_explicit_carveout(cl[0], cl[2])
    recs = detect_contradictions(cl, backend=RuleBasedNLIBackend())
    assert not any({"t_1", "t_3"} == {r["clause_a"], r["clause_b"]} for r in recs)
    shown = detect_contradictions(cl, backend=RuleBasedNLIBackend(), emit_labels=("contradiction", "neutral"))
    assert any(r["label"] == "neutral" and "override" in r["explanation"] for r in shown)


def test_order_sensitivity_uses_both_directions():
    cl = clauses_of(LEASE)
    # forward says 0.95, reverse says 0.2 -> mean 0.575 < 0.80 threshold -> NOT reported
    assert detect_contradictions(cl, backend=FakeBackend(0.95, 0.2)) == []
    # both directions agree -> reported
    assert detect_contradictions(cl, backend=FakeBackend(0.95, 0.9))


def test_threshold_is_configurable(monkeypatch):
    from legalpulse_nlp import config
    cl = clauses_of(LEASE)
    monkeypatch.setattr(config, "CONTRADICTION_THRESHOLD", 0.5)
    assert detect_contradictions(cl, backend=FakeBackend(0.6, 0.6))


def test_candidate_filter_skips_unrelated_and_caps_pairs(monkeypatch):
    from legalpulse_nlp import config
    txt = "1. Law\nGoverned by the laws of India.\n2. Colour\nThe widgets are painted blue.\n3. Rent\nTenant pays rent monthly.\n"
    assert candidate_pairs(clauses_of(txt)) == []
    many = "".join(f"{i}. Payment\nBuyer shall pay invoice number {i}.\n" for i in range(1, 30))
    monkeypatch.setattr(config, "MAX_CANDIDATE_PAIRS", 10)
    assert len(candidate_pairs(clauses_of(many))) == 10


def test_single_clause_and_empty():
    assert detect_contradictions([], backend=RuleBasedNLIBackend()) == []
    assert detect_contradictions(clauses_of("1. Payment\nBuyer pays."), backend=RuleBasedNLIBackend()) == []


def test_model_loading_failure_is_clear():
    be = HFNLIBackend("definitely/not-a-real-model-xyz")
    with pytest.raises(NLIModelError):
        be.predict([("a", "b")])


def test_heading_only_parent_clause_is_not_paired():
    from legalpulse_nlp.contradiction import candidate_pairs
    def c(cid, num, heading, text):
        return {"clause_id": cid, "number": num, "heading": heading, "text": text,
                "obligation_type": "termination", "defined_terms": [], "references": []}
    clauses = [c("c_4", "4", "Termination", "Termination"),
               c("c_4.1", "4.1", "", "Either party may terminate with 30 days notice."),
               c("c_4.2", "4.2", "", "Either party may terminate for material breach.")]
    pairs = {(i, j) for i, j, _ in candidate_pairs(clauses)}
    assert not any(0 in p for p in pairs)   # the heading-only parent is never paired
    assert (1, 2) in pairs                  # real sibling clauses still are

# ---- P1: candidate admission must not rely on filler words (model-free) ----
def _mk(cid, num, otype, text, terms=(), refs=()):
    return {"clause_id": cid, "number": num, "heading": "", "text": text,
            "obligation_type": otype, "defined_terms": list(terms), "references": list(refs)}


def _padded(*targets):
    """Targets first (indices 0..n-1), then 4 unrelated clauses so TF-IDF weights are realistic
    (in a 2-clause corpus every shared word has idf 0 and the problem cannot show up)."""
    pad = [
        _mk("pad_1", "91", "insurance", "Contractor maintains public liability cover throughout."),
        _mk("pad_2", "92", "confidentiality", "Secrets remain secret after expiry."),
        _mk("pad_3", "93", "notices", "Letters go to the registered office address."),
        _mk("pad_4", "94", "assignment", "Rights pass only with written consent."),
    ]
    return list(targets) + pad


def _admitted(clauses):
    return {(i, j) for i, j, _ in candidate_pairs(clauses)}


def test_filler_word_overlap_alone_does_not_admit_a_pair():
    # p4v2_3 vs p4v2_7: different topics; they share only "within / days / of / shall / Licensee"
    a = _mk("x_3", "3", "payment", "Within 15 days of receiving an invoice, Licensee shall pay the annual fee.")
    b = _mk("x_7", "7", "data_protection", "Licensor shall delete Licensee data within 30 days of termination.")
    assert (0, 1) not in _admitted(_padded(a, b))


def test_genuinely_related_pairs_are_still_admitted():
    # control 1: text-only link on content words (invoice, receipt, Buyer), different types
    a = _mk("x_1", "1", "payment", "Buyer shall pay the invoice within 30 days of receipt.")
    b = _mk("x_2", "2", "general", "Every invoice is due within 60 days of receipt by Buyer.")
    assert (0, 1) in _admitted(_padded(a, b))
    # control 2: explicit reference, no shared words
    c = _mk("x_3", "3", "general", "Alpha applies.", refs=["x_4"])
    d = _mk("x_4", "4", "general", "Beta applies.")
    assert (0, 1) in _admitted(_padded(c, d))
    # control 3: same obligation type
    e = _mk("x_5", "5", "termination", "Either party may terminate on notice.")
    f = _mk("x_6", "6", "termination", "Licensor may not terminate in the first year.")
    assert (0, 1) in _admitted(_padded(e, f))
    # control 4: shared defined term
    g = _mk("x_7", "7", "grant", "Grant of rights.", terms=["Software"])
    h = _mk("x_8", "8", "restriction", "No copying.", terms=["Software"])
    assert (0, 1) in _admitted(_padded(g, h))
