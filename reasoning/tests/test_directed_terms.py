import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from legalpulse_reasoning import config
from legalpulse_reasoning.graph.builder import build_graph, defining_clause
from legalpulse_reasoning.impact.tracer import trace_impact


def clause(i, text, terms):
    return {"clause_id": f"c{i}", "number": str(i), "heading": "", "text": text,
            "parties": [], "defined_terms": terms, "references": []}


CONTRACT = {"clauses": [
    clause(1, 'The "Delivery Date" means the day goods arrive.', ["Delivery Date"]),
    clause(2, "Payment is due 30 days after the Delivery Date.", ["Delivery Date"]),
    clause(3, "Risk passes on the Delivery Date.", ["Delivery Date"]),
    clause(4, "This agreement is governed by Indian law.", []),
]}


def impacted(g, cid):
    return {r["clause_id"] for r in trace_impact(g, cid)}


def test_changed_definition_reaches_its_users():
    g = build_graph(CONTRACT)
    assert impacted(g, "c1") == {"c2", "c3"}


def test_changed_user_does_not_reach_definition_or_other_users():
    g = build_graph(CONTRACT)
    assert impacted(g, "c2") == set()


def test_undirected_mode_keeps_old_behaviour(monkeypatch):
    monkeypatch.setattr(config, "TERM_EDGES", "undirected")
    g = build_graph(CONTRACT)
    assert impacted(g, "c2") == {"c1", "c3"}


def test_definition_is_the_quoted_clause_not_the_first_one():
    ids = ["c0", "c1", "c2"]
    text = {"c0": "See the Fee below.", "c1": 'The "Fee" means 10 rupees.', "c2": "Pay the Fee."}
    assert defining_clause("Fee", ids, text) == "c1"


def test_without_a_quoted_definition_the_first_user_is_the_definer():
    ids = ["c0", "c1"]
    text = {"c0": "The Fee is 10 rupees.", "c1": "Pay the Fee."}
    assert defining_clause("Fee", ids, text) == "c0"
