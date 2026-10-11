import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from legalpulse_reasoning.comparison.aligner import align_versions
from legalpulse_reasoning.comparison.embedders import BagOfWordsEmbedder
from legalpulse_reasoning.comparison.textdiff import meaning_changed
from legalpulse_reasoning import pipeline

EMB = BagOfWordsEmbedder()
MOCK = ROOT / "data" / "mock"


def load(p):
    return [json.loads((MOCK / f"{p}_{k}.json").read_text()) for k in ("old", "new")]


def by_type(changes, t):
    return [c for c in changes if c["change_type"] == t]


def test_detects_split():
    ch = align_versions(*load("p2"), embedder=EMB)
    s = by_type(ch, "split")
    assert len(s) == 1 and s[0]["old_clause_ids"] == ["p2v1_4"] and s[0]["new_clause_ids"] == ["p2v2_4", "p2v2_5"]


def test_detects_merge():
    ch = align_versions(*load("p2"), embedder=EMB)
    m = by_type(ch, "merged")
    assert len(m) == 1 and m[0]["old_clause_ids"] == ["p2v1_7", "p2v1_8"]


def test_added_and_deleted():
    ch = align_versions(*load("p1"), embedder=EMB)
    assert [c["new_clause_id"] for c in by_type(ch, "added")] == ["p1v2_12"]
    assert [c["old_clause_id"] for c in by_type(ch, "deleted")] == ["p1v1_9"]


def test_renumbered_not_marked_modified():
    ch = align_versions(*load("p1"), embedder=EMB)
    assert {c["new_clause_id"] for c in by_type(ch, "renumbered")} == {"p1v2_10", "p1v2_11"}


def test_one_word_change_is_modified():
    ch = align_versions(*load("p4"), embedder=EMB)
    grant = [c for c in ch if c["old_clause_id"] == "p4v1_2"][0]
    assert grant["change_type"] == "modified"


def test_meaning_changed_helper():
    assert meaning_changed("pay within 30 days", "pay within 60 days")
    assert not meaning_changed("Supplier shall deliver the goods.", "Supplier must deliver the goods.")


def test_pipeline_end_to_end_matches_schema():
    import jsonschema
    schema = json.loads((ROOT.parent / "schemas" / "risk_report.schema.json").read_text())
    report = pipeline.run(*load("p1"), embedder=EMB)
    jsonschema.validate(report, schema)
    top = report["risks"][0]
    assert top["rank"] == 1 and top["trigger_clause"].startswith("p1v2_")
