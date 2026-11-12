from legalpulse_nlp.segmenter import segment

# Unnumbered contract as a PDF extractor returns it: lines wrapped, no blank lines.
WRAPPED = """Confidentiality Agreement
The Disclosee shall keep all Confidential Information secret
and shall not disclose it to any third party without prior
written consent of the Sellers.
This Agreement is governed by Belgian law. Any dispute shall
be submitted to the courts of Brussels.
The Disclosee shall return all documents on first request."""

BLANK_LINES = """The Disclosee shall keep all Confidential Information secret.

This Agreement is governed by Belgian law.

The Disclosee shall return all documents on first request."""


def test_wrapped_unnumbered_text_is_split_into_paragraphs():
    r = segment(WRAPPED)
    assert len(r.clauses) >= 3, [c.text for c in r.clauses]


def test_blank_line_paragraphs_still_split():
    r = segment(BLANK_LINES)
    assert len(r.clauses) == 3


def test_single_short_paragraph_stays_one_clause():
    r = segment("The Disclosee shall keep all information secret.")
    assert len(r.clauses) == 1
