import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from legalpulse_reasoning import config
from legalpulse_reasoning.graph.builder import build_graph
from legalpulse_reasoning.graph.weights import idf_factor, edge_weight
from legalpulse_reasoning.impact.tracer import trace_impact

MOCK = pathlib.Path(__file__).resolve().parents[1] / "data" / "mock" / "contract_v1.json"


def test_idf_rare_beats_common():
    assert idf_factor(2, 20) > idf_factor(10, 20) > idf_factor(19, 20)


def test_term_in_every_clause_has_zero_weight():
    assert idf_factor(10, 10) == 0.0


def test_party_in_all_clauses_adds_no_impact():
    contract = {"clauses": [
        {"clause_id": f"c{i}", "number": str(i), "heading": "", "parties": ["Supplier"],
         "defined_terms": [], "references": []} for i in range(8)]}
    assert trace_impact(build_graph(contract), "c0") == []


def test_term_weight_not_scaled_by_idf():
    assert edge_weight("shared_term", df=19, n=20) == config.EDGE_WEIGHTS["shared_term"]


def test_cross_reference_weight_not_scaled():
    assert edge_weight("cross_reference") == config.EDGE_WEIGHTS["cross_reference"]


def test_fixed_mode_reproduces_old_weights(monkeypatch):
    monkeypatch.setattr(config, "WEIGHT_MODE", "fixed")
    g = build_graph(json.loads(MOCK.read_text()))
    assert {d["weight"] for _, _, d in g.edges(data=True) if d["type"] == "shared_party"} == {0.5}


def test_fitted_weights_file_is_used(tmp_path, monkeypatch):
    f = tmp_path / "w.json"
    f.write_text(json.dumps({"cross_reference": 0.77}))
    monkeypatch.setattr(config, "WEIGHTS_FILE", str(f))
    assert edge_weight("cross_reference") == 0.77
