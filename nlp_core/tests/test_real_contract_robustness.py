"""Regression tests from real CUAD contracts (NLP-EX-06, NLP-EX-07, NLP-EX-08).

Texts are tiny invented snippets that reproduce the failure shape seen in real public contracts.
"""
from legalpulse_nlp.metadata import extract_references
from legalpulse_nlp.segmenter import segment


def _numbers(res):
    return [c.number for c in res.clauses]


# --- NLP-EX-06: table-of-contents lines must not become clauses ---------------------------------
TOC_TEXT = """TABLE OF CONTENTS
1. Definitions 3
2. Licenses 13
3. Payments 21

1. DEFINITIONS
1.1 "Affiliate" means any entity that controls a party.
2. LICENSES
2.1 Licensor grants Licensee a licence.
3. PAYMENTS
3.1 Licensee shall pay fees within 30 days.
"""


def test_table_of_contents_entries_are_not_clauses():
    res = segment(TOC_TEXT)
    assert _numbers(res) == ["1", "1.1", "2", "2.1", "3", "3.1"]
    assert not any("Duplicate clause numbers" in w for w in res.warnings)
    assert not any(c.heading.rstrip()[-1:].isdigit() for c in res.clauses)


def test_heading_ending_in_a_number_is_kept_when_it_is_not_a_toc_duplicate():
    res = segment("1. Term 3\nThe term is three years.\n2. Fees\nFees are due monthly.\n")
    assert _numbers(res) == ["1", "2"]
    assert res.clauses[0].heading == "Term 3"


# --- NLP-EX-07: numbered list items inside a clause are not new clauses -------------------------
LIST_TEXT = """1. Term
1.1 This Agreement lasts two years.
2. Warranties
2.1 Provider warrants that:
1. the services will be performed with reasonable skill; and
2. the deliverables will not infringe any third party right.
2.2 Provider disclaims all other warranties.
3. General
3.1 Governing law is India.
"""


def test_numbered_list_items_stay_inside_their_clause():
    res = segment(LIST_TEXT)
    assert _numbers(res) == ["1", "1.1", "2", "2.1", "2.2", "3", "3.1"]
    c21 = next(c for c in res.clauses if c.number == "2.1")
    assert "reasonable skill" in c21.text and "infringe" in c21.text


def test_a_new_top_level_clause_with_a_capital_title_still_starts_a_clause():
    res = segment("1. Term\nTwo years.\n2. Fees\nMonthly.\n3. General Provisions\nIndia law.\n")
    assert _numbers(res) == ["1", "2", "3"]


# --- NLP-EX-08: citations of external laws are not clause references ----------------------------
IDS = {"5": "c_5", "351": "c_351", "42": "c_42", "505": "c_505"}


def test_external_statute_citations_are_not_clause_references():
    text = ("approved under Section 505(j) of the FD&C Act, Section 351 of the PHSA, Section 5 of the "
            "Securities Exchange Act of 1934 and Section 42 U.S.C.262.")
    assert extract_references(text, "9", IDS) == ([], [])


def test_internal_references_still_resolve():
    for text in ("subject to Clause 5.", "as set out in Section 5 of this Agreement.",
                 "see Section 5 of the Agreement."):
        assert extract_references(text, "9", IDS) == (["c_5"], []), text


# --- NLP-EX-09: EDGAR page footer "Source: ..., 8-K, 8/15/2019" must not leak into clauses ------
def test_edgar_source_footer_is_dropped():
    from legalpulse_nlp.ingest import clean_text
    text = ("1. Term\nThe term is 2 years.\n"
            "Source: ALLIED ESPORTS ENTERTAINMENT, INC., 8-K, 8/15/2019\n"
            "Renewal is automatic.\n")
    out = clean_text(text)
    assert "Source:" not in out
    assert "Renewal is automatic." in out


def test_a_sentence_that_starts_with_source_is_kept():
    from legalpulse_nlp.ingest import clean_text
    text = "Source: the Licensor's own records shall be used to compute fees.\n"
    assert "Source:" in clean_text(text)
