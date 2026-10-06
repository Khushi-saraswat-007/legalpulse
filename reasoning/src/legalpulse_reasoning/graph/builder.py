"""Module 4: Knowledge graph construction.

Nodes: clauses ("clause") and parties ("party").
Edges (source -> target):
  cross_reference : source clause cites target clause
  shared_term     : two clauses use the same defined term (added both directions)
  shared_party    : clause -> party node (clauses sharing a party connect through it)
"""
import networkx as nx


def build_graph(contract: dict) -> nx.DiGraph:
    g = nx.DiGraph()
    clauses = contract["clauses"]
    ids = {c["clause_id"] for c in clauses}

    for c in clauses:
        g.add_node(c["clause_id"], type="clause", label=c.get("heading") or c["number"])

    term_index = {}
    for c in clauses:
        cid = c["clause_id"]
        for ref in c.get("references", []):
            if ref in ids:
                g.add_edge(cid, ref, type="cross_reference")
        for term in c.get("defined_terms", []):
            term_index.setdefault(term, []).append(cid)
        for p in c.get("parties", []):
            pid = f"party:{p}"
            g.add_node(pid, type="party", label=p)
            g.add_edge(cid, pid, type="shared_party")

    for term, members in term_index.items():
        for a in members:
            for b in members:
                if a != b:
                    g.add_edge(a, b, type="shared_term", term=term)
    return g


def graph_to_json(g) -> dict:
    """Serialise to the `graph` part of the risk report schema."""
    return {
        "nodes": [{"id": n, "type": d["type"], "label": d["label"]} for n, d in g.nodes(data=True)],
        "edges": [{"source": u, "target": v, "type": d["type"]} for u, v, d in g.edges(data=True)],
    }
