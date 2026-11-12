from legalpulse_nlp.segmenter import segment

# Parties listed as "1) ... 2) ..." in the preamble, then the real clauses start again at 1.
PARTIES_THEN_CLAUSES = """TWO-WAY CONFIDENTIALITY AGREEMENT
This Agreement is made by and between:
1) <Research institution name> with registered offices located in Brussels, Tax
registration No 123, represented by John Doe, in the legal capacity as director.
2) <Company name> with registered offices located in Paris, Tax registration No.
456, represented by Jane Roe, in the legal capacity as manager.
1. Definition and interpretation
In this Agreement the following terms will have the respective meanings given below.
2. Exclusions
The obligation of confidentiality shall not apply to public information."""

PLAIN_PAREN_CLAUSES = """1) Payment
The Buyer shall pay each invoice within 30 days.
2) Delivery
The Seller shall deliver the goods within 10 days."""


def test_numbered_parties_in_preamble_are_not_clauses():
    r = segment(PARTIES_THEN_CLAUSES)
    assert [c.number for c in r.clauses] == ["1", "2"], [(c.number, c.text[:30]) for c in r.clauses]
    assert r.clauses[0].heading.startswith("Definition")
    assert "Research institution" in r.preamble
    assert not any("Duplicate" in w for w in r.warnings)


def test_paren_numbered_real_clauses_are_untouched():
    r = segment(PLAIN_PAREN_CLAUSES)
    assert [c.number for c in r.clauses] == ["1", "2"]
    assert r.clauses[0].heading == "Payment"
