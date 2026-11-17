"""Graph ablation + sensitivity (no labels needed).

For every contract in data/mock and data/real, treat each clause as "the changed clause", trace its impact,
and compare settings. Two numbers per setting:
  spread  = average % of the other clauses that one change reaches (high = noisy graph)
  overlap = average Jaccard overlap of the impacted set with the reference setting (1.0 = identical list)
This shows WHAT CHANGES when a weight/edge/depth changes. It cannot say which setting is RIGHT:
that needs human labels (see the labelled-set step).

Run from reasoning/:   python evaluate_graph_ablation.py
"""
import copy, glob, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from legalpulse_reasoning import config                      # noqa: E402
from legalpulse_reasoning.graph.builder import build_graph   # noqa: E402
from legalpulse_reasoning.impact.tracer import trace_impact  # noqa: E402

BASE = copy.deepcopy(config.EDGE_WEIGHTS)


def setting(name, mode="idf", depth=config.MAX_DEPTH, min_score=config.MIN_IMPACT_SCORE, terms="undirected", **w):
    weights = {**BASE, **w}
    return dict(name=name, mode=mode, depth=depth, min_score=min_score, weights=weights, terms=terms)


# The first 18 settings are the ones the labelling candidates were built from: do NOT rename or reorder them.
# They all use undirected term edges (the old behaviour) so their numbers stay comparable.
LEGACY_SETTINGS = [
    setting("fixed 0.9/0.6/0.5 (paper)", mode="fixed"),
    setting("idf on party (current)"),
    setting("no party edges", mode="idf", shared_party=0.0),
    setting("fixed, no party edges", mode="fixed", shared_party=0.0),
    setting("fixed, party 0.3", mode="fixed", shared_party=0.3),
    setting("uniform weights 0.5 (GCN-like)", mode="fixed", cross_reference=0.5, shared_term=0.5, shared_party=0.5),
    setting("cross-reference only", mode="fixed", shared_term=0.0, shared_party=0.0),
    setting("no graph (depth 0)", depth=0),
    setting("depth 1", depth=1),
    setting("depth 2", depth=2),
    setting("sens: cross_ref 0.7", cross_reference=0.7),
    setting("sens: cross_ref 1.0", cross_reference=1.0),
    setting("sens: term 0.4", shared_term=0.4),
    setting("sens: term 0.8", shared_term=0.8),
    setting("sens: party 0.3", shared_party=0.3),
    setting("sens: party 0.7", shared_party=0.7),
    setting("sens: min_score 0.1", min_score=0.1),
    setting("sens: min_score 0.3", min_score=0.3),
]
# New settings: term edges directed (definition clause -> clauses that use the term)
NEW_SETTINGS = [
    setting("directed term edges (new)", terms="directed"),
    setting("directed, term 0.8", terms="directed", shared_term=0.8),
    setting("directed, depth 1", terms="directed", depth=1),
]
SETTINGS = LEGACY_SETTINGS + NEW_SETTINGS
REFERENCE = "idf on party (current)"


def impacted_sets(contract, s):
    config.WEIGHT_MODE = s["mode"]; config.TERM_EDGES = s["terms"]
    config.EDGE_WEIGHTS.clear(); config.EDGE_WEIGHTS.update(s["weights"])
    g = build_graph(contract)
    ids = [x for x, d in g.nodes(data=True) if d["type"] == "clause"]
    return {c: {r["clause_id"] for r in trace_impact(g, c, max_depth=s["depth"], min_score=s["min_score"])} for c in ids}


def main():
    files = sorted(glob.glob(str(ROOT / "data/mock/p*_new.json")) + glob.glob(str(ROOT / "data/real/r*_new.json")))
    contracts = [json.load(open(f)) for f in files]
    ref = next(s for s in SETTINGS if s["name"] == REFERENCE)
    ref_sets = [impacted_sets(c, ref) for c in contracts]
    rows = []
    for s in SETTINGS:
        spreads, overlaps = [], []
        for c, rs in zip(contracts, ref_sets):
            cur = impacted_sets(c, s)
            n = len(cur)
            spreads += [len(v) / max(1, n - 1) for v in cur.values()]
            for k in cur:
                u = cur[k] | rs[k]
                if u:
                    overlaps.append(len(cur[k] & rs[k]) / len(u))
        rows.append({"setting": s["name"], "spread_pct": round(100 * sum(spreads) / len(spreads), 1),
                     "overlap_with_reference": round(sum(overlaps) / max(1, len(overlaps)), 2)})
    config.WEIGHT_MODE = "idf"; config.TERM_EDGES = "directed"; config.EDGE_WEIGHTS.clear(); config.EDGE_WEIGHTS.update(BASE)
    out = {"reference": REFERENCE, "contracts": len(contracts), "rows": rows}
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "graph_ablation.json").write_text(json.dumps(out, indent=2))
    w = max(len(r["setting"]) for r in rows)
    print(f"{'setting':<{w}}  spread%  overlap_with_reference")
    for r in rows:
        print(f"{r['setting']:<{w}}  {r['spread_pct']:>6}   {r['overlap_with_reference']:>5}")
    print(f"\n{len(contracts)} contracts; reference = {REFERENCE}")


if __name__ == "__main__":
    main()
