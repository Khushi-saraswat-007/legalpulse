"""Module 4: Knowledge graph construction.

Nodes: clauses ("clause") and parties ("party").
Edges (source -> target):
  cross_reference : source clause cites target clause
  shared_term     : defining clause -> every clause that uses the term (config.TERM_EDGES = "directed"),
                    or both directions between all users of the term ("undirected", as in the paper)
  shared_party    : clause -> party node (clauses sharing a party connect through it)
"""
import re

import networkx as nx

from .. import config
from .weights import edge_weight


def defining_clause(term: str, member_ids: list, text_by_id: dict) -> str:
    """The clause that DEFINES `term`: the one where it appears in quotes (e.g. "Delivery Date" means ...).
    If no clause quotes it, the first clause (document order) that uses it."""
    quoted = re.compile(r'["\u201c\u201d\u2018\']' + re.escape(term) + r'["\u201d\u2019\']')
    for cid in member_ids:
        if quoted.search(text_by_id[cid]):
            return cid
    return member_ids[0]


def build_graph(contract: dict) -> nx.DiGraph:
    g = nx.DiGraph()
    clauses = contract["clauses"]
    ids = {c["clause_id"] for c in clauses}

    for c in clauses:
        g.add_node(c["clause_id"], type="clause", label=c.get("heading") or c["number"])

    n = len(clauses)
    text_by_id = {c["clause_id"]: c.get("text", "") for c in clauses}
    term_index, party_index = {}, {}
    for c in clauses:
        for term in c.get("defined_terms", []):
            term_index.setdefault(term, []).append(c["clause_id"])
        for p in c.get("parties", []):
            party_index.setdefault(p, []).append(c["clause_id"])

    for c in clauses:
        cid = c["clause_id"]
        for ref in c.get("references", []):
            if ref in ids:
                g.add_edge(cid, ref, type="cross_reference", weight=edge_weight("cross_reference"))
        for p in c.get("parties", []):
            pid = f"party:{p}"
            g.add_node(pid, type="party", label=p)
            g.add_edge(cid, pid, type="shared_party", weight=edge_weight("shared_party", len(party_index[p]), n))

    for term, members in term_index.items():
        w = edge_weight("shared_term", len(members), n)
        if config.TERM_EDGES == "directed":
            d = defining_clause(term, members, text_by_id)
            pairs = [(d, u) for u in members if u != d]          # a changed definition reaches its users, not the reverse
        else:
            pairs = [(a, b) for a in members for b in members if a != b]
        for a, b in pairs:
            g.add_edge(a, b, type="shared_term", term=term, weight=w)
    return g


def graph_to_json(g) -> dict:
    """Serialise to the `graph` part of the risk report schema."""
    return {
        "nodes": [{"id": n, "type": d["type"], "label": d["label"]} for n, d in g.nodes(data=True)],
        "edges": [{"source": u, "target": v, "type": d["type"], "weight": d.get("weight")} for u, v, d in g.edges(data=True)],
    }
