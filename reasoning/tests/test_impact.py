import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from legalpulse_reasoning.graph.builder import build_graph
from legalpulse_reasoning.impact.tracer import trace_impact

MOCK = pathlib.Path(__file__).resolve().parents[1] / "data" / "mock" / "contract_v1.json"


def load():
    return json.loads(MOCK.read_text())


def test_cross_reference_impact():
    g = build_graph(load())
    ids = [r["clause_id"] for r in trace_impact(g, "c001_5")]
    assert "c001_9" in ids      # penalty cites payment
    assert "c001_12" in ids     # termination cites penalty (2 hops)


def test_unrelated_clause_not_impacted():
    g = build_graph(load())
    ids = [r["clause_id"] for r in trace_impact(g, "c001_5")]
    assert "c001_14" not in ids  # governing law has no link


def test_unknown_clause():
    assert trace_impact(build_graph(load()), "nope") == []
