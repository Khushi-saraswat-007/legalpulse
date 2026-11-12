import pytest
from conftest import FIXTURES

from legalpulse_nlp import extract, extract_from_text, validate_contract
from legalpulse_nlp import metadata
from legalpulse_nlp.errors import (EmptyDocumentError, ScannedPDFError, SchemaValidationError,
                                   UnsupportedFormatError)
from legalpulse_nlp.ingest import read_text
from legalpulse_nlp.segmenter import segment

TXT = (FIXTURES / "sample_supply.txt").read_text()


def by_number(contract):
    return {c["number"]: c for c in contract["clauses"]}


# ---------------------------------------------------------------- ingestion
@pytest.mark.parametrize("name", ["sample_supply.txt", "sample_supply.docx", "sample_supply.pdf"])
def test_all_formats_give_same_clause_numbers(name):
    c = extract(FIXTURES / name, contract_id="t1", detect_contradictions=False)
    assert [x["number"] for x in c["clauses"]] == ["1", "2", "3", "4", "4.1", "4.2", "5", "6"]


def test_page_furniture_removed():
    assert "Page 2 of 3" not in read_text(FIXTURES / "sample_supply.pdf")


def test_unsupported_format(tmp_path):
    f = tmp_path / "x.xyz"; f.write_text("hi")
    with pytest.raises(UnsupportedFormatError):
        read_text(f)


def test_empty_file(tmp_path):
    f = tmp_path / "e.txt"; f.write_text("   \n\n ")
    with pytest.raises(EmptyDocumentError):
        read_text(f)


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        read_text("nope.pdf")


def test_scanned_pdf_detected():
    with pytest.raises(ScannedPDFError):
        read_text(FIXTURES / "scanned.pdf")


def test_docx_auto_numbering_rebuilt():
    t = read_text(FIXTURES / "autonumbered.docx")
    assert t.splitlines()[0].startswith("1. ") and t.splitlines()[1].startswith("2. ")


# ---------------------------------------------------------------- segmentation
def test_nested_clauses_and_subitems():
    c = by_number(extract_from_text(TXT, "c001").contract)
    assert "4.1" in c and "4.2" in c
    assert "outstanding invoices remain payable" in c["4.2"]["text"]      # (a) stays inside 4.2


def test_heading_forms():
    c = by_number(extract_from_text(TXT, "c001").contract)
    assert c["2"]["heading"] == "Payment"                  # heading on its own line
    assert c["5"]["heading"] == "Confidentiality"          # "5. Heading: body" on one line
    assert c["5"]["text"].startswith("Neither party")
    assert c["4"]["heading"] == "Termination"              # parent that only has a heading


def test_missing_headings():
    r = extract_from_text("1. Buyer shall pay all invoices within 30 days.\n2. Seller shall deliver the goods.", "x")
    assert [c["heading"] for c in r.contract["clauses"]] == ["", ""]


def test_bare_number_in_text_is_not_a_clause():
    r = segment("1. Payment\nBuyer shall pay within\n30 days of the invoice.\n2. Law\nIndia.")
    assert [c.number for c in r.clauses] == ["1", "2"]
    assert "30 days" in r.clauses[0].text


def test_keyword_numbering():
    r = segment("Clause 1: Payment is due.\nClause 2: Delivery is due.")
    assert [c.number for c in r.clauses] == ["1", "2"]


def test_no_numbering_falls_back_to_paragraphs():
    r = segment("Buyer pays.\n\nSeller delivers.")
    assert len(r.clauses) == 2 and r.warnings


def test_duplicate_numbers_warn_and_ids_stay_unique():
    r = extract_from_text("1. A\nBuyer pays.\n1. B\nSeller delivers.", "d")
    ids = [c["clause_id"] for c in r.contract["clauses"]]
    assert len(set(ids)) == 2 and any("Duplicate" in w for w in r.warnings)


def test_preamble_not_a_clause():
    r = extract_from_text(TXT, "c001")
    assert "SUPPLY AGREEMENT" in r.preamble


# ---------------------------------------------------------------- metadata
def test_deadline_extraction():
    d = metadata.extract_deadline
    assert d("Buyer shall pay within 30 days of the Effective Date.") == "30 days"
    assert d("Tenant shall pay on or before the 5th of each month.") == "5th of each month"
    assert d("within thirty (30) days") == "30 days"
    assert d("Delivery by 31 March 2027.") == "31 March 2027"
    assert d("Support is provided 24 hours a day.") is None      # not a deadline
    assert d("Buyer shall pay invoices.") is None                # nothing invented


def test_party_detection():
    c = by_number(extract_from_text(TXT, "c001").contract)
    assert c["2"]["parties"] == ["Buyer"]
    assert set(c["4.1"]["parties"]) == {"Supplier", "Buyer"}     # "Either party"
    assert c["6"]["parties"] == []


def test_defined_terms():
    c = by_number(extract_from_text(TXT, "c001").contract)
    assert c["1"]["defined_terms"] == ["Effective Date", "Goods"]
    assert c["2"]["defined_terms"] == ["Effective Date"]


def test_references_resolved_and_unresolved():
    r = extract_from_text(TXT, "c001")
    c = by_number(r.contract)
    assert c["3"]["references"] == ["c001_2"]
    assert c["4.2"]["references"] == ["c001_3"]                  # Clause 9 does not exist
    assert any("unknown clause" in w for w in r.warnings)


def test_reference_lists_and_ranges():
    ids = {str(i): f"x_{i}" for i in range(1, 9)}
    refs, _ = metadata.extract_references("See Clauses 2 and 4, and Sections 5 to 7.", "1", ids)
    assert refs == ["x_2", "x_4", "x_5", "x_6", "x_7"]
    refs, _ = metadata.extract_references("This Clause 1 applies.", "1", ids)
    assert refs == []                                           # self reference dropped


def test_obligation_types():
    k = metadata.classify_obligation
    assert k("Payment", "") == "payment"
    assert k("", "Licensee shall not copy the Software.") == "restriction"
    assert k("", "This agreement is governed by the laws of India.") == "governing_law"
    assert k("", "Some unrelated sentence.") == "general"


# ---------------------------------------------------------------- output / schema
def test_output_is_schema_valid_and_stable():
    a = extract(FIXTURES / "sample_supply.txt", "c001", detect_contradictions=False)
    b = extract(FIXTURES / "sample_supply.txt", "c001", detect_contradictions=False)
    validate_contract(a)
    assert a == b                                              # deterministic
    assert [c["clause_id"] for c in a["clauses"]][:2] == ["c001_1", "c001_2"]


def test_schema_violation_detected():
    with pytest.raises(SchemaValidationError):
        validate_contract({"contract_id": "x", "version": "v1", "clauses": [{"clause_id": "a"}]})
