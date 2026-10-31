"""compare_clauses: each rule produces a short, checkable reason; harmless rewordings produce none."""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from legalpulse_reasoning.comparison.semantic import compare_clauses, quantities

def cmp(a, b, **extra):
    o = {"text": a, **extra.get("old", {})}; n = {"text": b, **extra.get("new", {})}
    return compare_clauses(o, n)

def has(res, fragment):
    return any(fragment in r for r in res["reasons"])


def test_number_change_reports_direction_and_percentage():
    r = cmp("The Client shall pay within 30 days of the invoice.", "The Client shall pay within 60 days of the invoice.")
    assert has(r, "30 → 60 days (+100%)") and r["severity_hint"] >= 0.9

def test_number_decrease():
    r = cmp("Either party may terminate on 60 days notice.", "Either party may terminate on 7 days notice.")
    assert has(r, "60 → 7 days (-88%)")

def test_percentage_and_currency():
    assert has(cmp("Interest of 2% per month applies.", "Interest of 5% per month applies."), "2 → 5% (+150%)")
    assert has(cmp("A fee of $5,000 is payable.", "A fee of $10,000 is payable."), "5000 → 10000 (+100%)")

def test_cap_removed_and_introduced():
    r = cmp("The liability of the Supplier is limited to the fees paid.", "The liability of the Supplier is unlimited for all losses.")
    assert has(r, "cap removed") and r["severity_hint"] >= 0.9
    assert has(cmp("The liability of the Supplier is unlimited.", "The liability of the Supplier is limited to the fees paid."), "cap introduced")

def test_obligation_weakened_and_strengthened():
    assert has(cmp("The Supplier shall deliver the goods.", "The Supplier may deliver the goods."), "obligation weakened")
    assert has(cmp("The Client may inspect the goods.", "The Client shall inspect the goods."), "permission became an obligation")

def test_prohibition_added_and_removed():
    assert has(cmp("The Client shall disclose the data.", "The Client shall not disclose the data."), "prohibition added")
    assert has(cmp("The Client shall not disclose the data.", "The Client shall disclose the data."), "prohibition removed")

def test_negation_added():
    assert has(cmp("Payment is due on delivery.", "Payment is not due on delivery."), "negation added")

def test_party_and_clause_type_change():
    assert has(cmp("A.", "A.", old={"parties": ["Supplier"]}, new={"parties": ["Supplier", "Subcontractor"]}), "party changed")
    assert has(cmp("A.", "A.", old={"obligation_type": "payment"}, new={"obligation_type": "termination"}), "clause type changed")

def test_harmless_edits_produce_no_reasons():
    assert cmp("Payment is due within thirty (30) days.", "Payment is due no later than 30 days.")["reasons"] == []
    assert cmp("See Clause 4.1 for details.", "See Clause 5.2 for details.")["reasons"] == []      # cross-reference numbers are ignored
    assert cmp("The Supplier shall promptly notify the Client.", "The Supplier shall quickly notify the Client.")["severity_hint"] == 0.0

def test_cross_reference_numbers_are_not_quantities():
    assert quantities("Subject to Section 3.2 and Schedule 4, the fee is 30 days.") == [(30.0, "days")]


def test_ordinals_are_not_quantities():
    assert quantities("interest accrues from the 15th day after the invoice date") == []

def test_removed_and_added_clauses_are_described():
    from legalpulse_reasoning.comparison.semantic import describe_added, describe_removed
    cap = {"text": "The liability of the Supplier is limited to the fees paid."}
    assert "cap or limit" in describe_removed(cap)["reasons"][0] and describe_removed(cap)["severity_hint"] >= 0.9
    assert describe_added({"text": "The Client shall not assign this agreement."})["severity_hint"] >= 0.7
    assert describe_removed({"text": "Headings are for convenience only."})["severity_hint"] == 0.0
