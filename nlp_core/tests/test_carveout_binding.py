"""Regression tests for ISSUES F1: an exception marker ("subject to", "notwithstanding",
"except as provided in") must be bound to the clause it actually points at.

Rule under test (exact clause-number match only; never suppress when the target is unclear):
  a pair (A, B) is an explicit carve-out only if one clause has a marker whose OWN cited clause
  number equals the other clause's number. Otherwise the pair must reach the NLI backend.

Tests use a recording backend, so they prove whether the NLI model was (or was not) called.
"""
from conftest import FIXTURES

from legalpulse_nlp import detect_contradictions, extract_from_text
from legalpulse_nlp.contradiction import is_explicit_carveout


class RecordingBackend:
    """Neutral model that remembers which (premise, hypothesis) pairs it was asked about."""
    name = "recording"

    def __init__(self):
        self.seen = []

    def predict(self, pairs):
        self.seen.extend(pairs)
        return [{"entailment": 0.0, "contradiction": 0.0, "neutral": 1.0} for _ in pairs]


def mk(number, text, cites=()):
    return {"clause_id": f"c_{number}", "number": str(number), "heading": "", "text": text,
            "parties": [], "obligation_type": "general", "deadline": None, "defined_terms": [],
            "references": [f"c_{n}" for n in cites]}


def reached_nli(clauses):
    """Set of frozenset({id_a, id_b}) that the NLI backend was asked about."""
    text_to_id = {c["text"]: c["clause_id"] for c in clauses}
    be = RecordingBackend()
    detect_contradictions(clauses, backend=be)
    return {frozenset((text_to_id[p], text_to_id[h])) for p, h in be.seen}


def pair(a, b):
    return frozenset((f"c_{a}", f"c_{b}"))


# 1 ------------------------------------------------------------------------------------
def test_marker_for_clause_9_does_not_suppress_pair_with_clause_3():
    c3 = mk(3, "A penalty applies if payment under Clause 2 is late.", cites=(2,))
    c42 = mk("4.2", "Clause 3 penalties survive termination, subject to Clause 9.", cites=(3,))
    assert is_explicit_carveout(c3, c42) is None
    assert pair(3, "4.2") in reached_nli([c3, c42])


# 2 ------------------------------------------------------------------------------------
def test_matched_notwithstanding_override_stays_suppressed():
    c9 = mk(9, "Licensor may terminate this agreement if Licensee breaches Clause 4.", cites=(4,))
    c11 = mk(11, "Notwithstanding anything in Clause 9, Licensor may not terminate during the first 12 months.", cites=(9,))
    assert is_explicit_carveout(c9, c11)
    assert pair(9, 11) not in reached_nli([c9, c11])


# 3 ------------------------------------------------------------------------------------
def test_except_as_provided_in_clause_4_stays_suppressed():
    c4 = mk(4, "Licensee shall not copy or modify the Software.")
    c8 = mk(8, "Licensor shall indemnify Licensee against third-party claims, except as provided in Clause 4.", cites=(4,))
    assert is_explicit_carveout(c4, c8)
    assert pair(4, 8) not in reached_nli([c4, c8])


# 4 ------------------------------------------------------------------------------------
def test_subject_to_clause_9_binds_to_9_not_to_clause_2():
    c2 = mk(2, "Buyer shall pay invoices within 30 days.")
    c9 = mk(9, "Buyer may withhold payment during a dispute.")
    c7 = mk(7, "Subject to Clause 9, Buyer shall pay the amount due under Clause 2.", cites=(9, 2))
    assert is_explicit_carveout(c9, c7)                  # target = 9 -> carve-out
    assert is_explicit_carveout(c2, c7) is None          # merely cited -> NOT a carve-out
    reached = reached_nli([c2, c9, c7])
    assert pair(7, 2) in reached and pair(7, 9) not in reached


# 5 ------------------------------------------------------------------------------------
def test_subject_to_list_of_clauses_binds_every_listed_target():
    c3 = mk(3, "Tenant shall not sublet without consent.")
    c5 = mk(5, "Landlord may refuse any subletting request.")
    c6 = mk(6, "Tenant shall keep the premises clean.")
    c8 = mk(8, "Subject to Clauses 3 and 5, Tenant may sublet part of the premises.", cites=(3, 5, 6))
    assert is_explicit_carveout(c3, c8) and is_explicit_carveout(c5, c8)
    assert is_explicit_carveout(c6, c8) is None          # cited later in the clause, not in the list
    assert pair(8, 6) in reached_nli([c3, c5, c6, c8])


# 6 ------------------------------------------------------------------------------------
def test_reference_after_comma_is_not_attributed_to_earlier_marker():
    c9 = mk(9, "Licensor may terminate if Licensee breaches this agreement.")
    c12 = mk(12, "Notwithstanding anything contained herein, including Clause 9, Licensor may not terminate in year one.", cites=(9,))
    assert is_explicit_carveout(c9, c12) is None          # target not identified confidently
    assert pair(9, 12) in reached_nli([c9, c12])          # so it must reach NLI


# 7 ------------------------------------------------------------------------------------
def test_sample_fixture_clause_3_vs_4_2_reaches_nli():
    clauses = extract_from_text((FIXTURES / "sample_supply.txt").read_text(), "c001").contract["clauses"]
    by = {c["number"]: c["clause_id"] for c in clauses}
    assert frozenset((by["3"], by["4.2"])) in reached_nli(clauses)


# 8 (extra, from "exact clause-number matching only") ----------------------------------
def test_exact_number_only_clause_4_marker_does_not_cover_clause_4_1():
    c41 = mk("4.1", "Either party may terminate with 30 days notice.")
    c9 = mk(9, "Termination takes effect on the last day of the month, except as provided in Clause 4.", cites=(4, "4.1"))
    assert is_explicit_carveout(c41, c9) is None
    assert pair("4.1", 9) in reached_nli([c41, c9])


# 9 (edge case found in review) ----------------------------------------------------------
def test_subclause_reference_is_not_treated_as_its_parent_clause():
    c9 = mk(9, "Licensor may terminate if Licensee breaches this agreement.")
    c12 = mk(12, "Subject to Clause 9(b), Licensor may not terminate in year one.", cites=(9,))
    assert is_explicit_carveout(c9, c12) is None          # 9(b) is not clause 9 -> exact match fails
    assert pair(9, 12) in reached_nli([c9, c12])


def test_subclause_in_a_list_only_drops_that_entry():
    c3 = mk(3, "Tenant shall not sublet without consent.")
    c5 = mk(5, "Landlord may refuse any subletting request.")
    c8 = mk(8, "Subject to Clauses 3 and 5(a), Tenant may sublet part of the premises.", cites=(3, 5))
    assert is_explicit_carveout(c3, c8)                   # plain "3" still bound
    assert is_explicit_carveout(c5, c8) is None           # "5(a)" is not clause 5

# 10 (gap: filler words) ----------------------------------------------------------------
def test_subject_to_the_terms_of_clause_9_binds_to_9():
    c9 = mk(9, "Buyer may withhold payment during a dispute.")
    c7 = mk(7, "Subject to the terms of Clause 9, Buyer shall pay the amount due within 30 days.", cites=(9,))
    assert is_explicit_carveout(c9, c7)
    assert pair(7, 9) not in reached_nli([c9, c7])


def test_terms_filler_does_not_over_bind_past_a_content_word():
    c9 = mk(9, "Buyer may withhold payment during a dispute.")
    c7 = mk(7, "Subject to the terms of the Licence, Buyer shall pay the sum due under Clause 9.", cites=(9,))
    assert is_explicit_carveout(c9, c7) is None
    assert pair(7, 9) in reached_nli([c9, c7])


def test_subject_to_terms_and_conditions_of_clause_9_binds_to_9():
    c9 = mk(9, "Buyer may withhold payment during a dispute.")
    c7 = mk(7, "Subject to the terms and conditions of Clause 9, Buyer shall pay the amount due within 30 days.", cites=(9,))
    assert is_explicit_carveout(c9, c7)
    assert pair(7, 9) not in reached_nli([c9, c7])


def test_subject_to_applicable_law_and_clause_9_is_not_bound():
    c9 = mk(9, "Buyer may withhold payment during a dispute.")
    c7 = mk(7, "Subject to applicable law and Clause 9, Buyer shall pay the amount due within 30 days.", cites=(9,))
    assert is_explicit_carveout(c9, c7) is None
    assert pair(7, 9) in reached_nli([c9, c7])