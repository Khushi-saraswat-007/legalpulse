"""A clause that was DELETED in the new version must still produce a ranked risk."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from legalpulse_reasoning import pipeline
from legalpulse_reasoning.comparison.embedders import BagOfWordsEmbedder
from legalpulse_reasoning.ingest.splitter import split_clauses

OLD = """SUPPLY AGREEMENT

1. Payment. The Buyer shall pay each invoice within 30 days of the invoice date.

2. Late Payment. If the Buyer fails to pay under Section 1, interest of 2% per month applies.

3. Liability. The Supplier's liability is limited to the fees paid under Section 1.

4. Termination. Either party may terminate this agreement on 30 days notice.

5. Governing Law. This agreement is governed by the laws of India and the parties submit to its courts.
"""
# the Liability clause (3) is removed entirely
NEW = OLD.replace("3. Liability. The Supplier's liability is limited to the fees paid under Section 1.\n\n", "")


def _run():
    old = split_clauses(OLD, "d1", "v1")
    new = split_clauses(NEW, "d1", "v2")
    return pipeline.run(old, new, BagOfWordsEmbedder())


def test_deleted_clause_gets_a_risk():
    rep = _run()
    kinds = [c["change_type"] for c in rep["changes"]]
    assert kinds.count("deleted") == 1
    deleted = [r for r in rep["risks"] if "removed" in r["explanation"].lower()]
    assert len(deleted) == 1
    assert deleted[0]["severity"] in ("high", "critical")     # deletion has the highest change weight


def test_deleted_clause_impacts_clauses_that_cited_it():
    rep = _run()
    deleted = next(r for r in rep["risks"] if "removed" in r["explanation"].lower())
    # trigger is the OLD id; impacted ids are NEW ids that exist in the new graph
    new_nodes = {n["id"] for n in rep["graph"]["nodes"]}
    assert all(i in new_nodes for i in deleted["impacted_clauses"])
