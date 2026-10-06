"""Module 5: Impact tracing (rule-based, no ML).

If clause X changes, which clauses are affected?
  - cross_reference edges point source -> cited clause, so a change to the cited
    clause impacts the citing clause: traverse them in REVERSE.
  - shared_term edges are symmetric: traverse forward.
  - shared_party edges go clause -> party: a change reaches other clauses of the
    same party by going clause -> party (forward) then party -> clause (reverse).
Impact score of a path = product of edge weights; each clause keeps its best path.
"""
from .. import config


def _neighbors(g, node):
    """Yield (next_node, edge_type) pairs along which a change propagates."""
    for _, v, d in g.out_edges(node, data=True):
        if d["type"] in ("shared_term", "shared_party"):
            yield v, d["type"]
    for u, _, d in g.in_edges(node, data=True):
        if d["type"] in ("cross_reference", "shared_party"):
            yield u, d["type"]


def trace_impact(g, changed_clause, max_depth=config.MAX_DEPTH, min_score=config.MIN_IMPACT_SCORE):
    """Return impacted clauses sorted by score, each with its explaining path."""
    if changed_clause not in g:
        return []
    best = {changed_clause: (1.0, [changed_clause], [])}
    frontier = [changed_clause]
    for _ in range(max_depth):
        nxt = []
        for node in frontier:
            score, path, etypes = best[node]
            for nb, et in _neighbors(g, node):
                if nb in path:
                    continue
                s = score * config.EDGE_WEIGHTS[et]
                if s >= min_score and (nb not in best or s > best[nb][0]):
                    best[nb] = (s, path + [nb], etypes + [et])
                    nxt.append(nb)
        frontier = nxt
    out = []
    for node, (s, path, etypes) in best.items():
        if node == changed_clause or g.nodes[node]["type"] != "clause":
            continue
        out.append({"clause_id": node, "score": round(s, 3), "path": path, "edge_types": etypes})
    return sorted(out, key=lambda r: -r["score"])
