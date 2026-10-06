"""Tunable constants. Keep every magic number here so it is easy to defend and tune."""

# Edge weights: how strongly a change travels along each edge type (0..1)
EDGE_WEIGHTS = {
    "cross_reference": 0.9,   # clause explicitly cites another clause
    "shared_term": 0.6,       # clauses use the same defined term
    "shared_party": 0.5,      # clauses involve the same party (via party node)
}

MAX_DEPTH = 3           # how many hops a change may propagate
MIN_IMPACT_SCORE = 0.2  # ignore weaker impacts

# Version comparison thresholds (tune on labeled pairs)
SIM_MATCH_THRESHOLD = 0.80
SIM_SPLIT_MERGE_THRESHOLD = 0.60

SEVERITY_BANDS = [(0.75, "critical"), (0.5, "high"), (0.25, "medium"), (0.0, "low")]
