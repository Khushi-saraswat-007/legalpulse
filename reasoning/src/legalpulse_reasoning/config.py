"""Tunable constants. Keep every magic number here so it is easy to defend and tune."""

# Edge weights: how strongly a change travels along each edge type (0..1)
EDGE_WEIGHTS = {
    "cross_reference": 0.9,   # clause explicitly cites another clause
    "shared_term": 0.6,       # clauses use the same defined term
    "shared_party": 0.5,      # clauses involve the same party (via party node)
}

MAX_DEPTH = 3           # how many hops a change may propagate
MIN_IMPACT_SCORE = 0.2  # ignore weaker impacts

# Version comparison thresholds (tune on labeled pairs; see evaluate_alignment.py)
SIM_MATCH_THRESHOLD = 0.80   # cosine similarity needed to call two clauses "the same clause"
HEADING_BONUS = 0.15         # added to the match score when headings are identical
SIM_HEADING_MIN = 0.50       # same heading + at least this similarity is also accepted as a match
SIM_PART_MIN = 0.40          # a clause must be at least this similar to count as a split/merge part
SPLIT_MERGE_MARGIN = 0.10    # two parts together must beat the best single part by this much

# Uneven splits/merges (one half is tiny, so its own similarity is too low to notice)
ADJ_MIN_COMBINED = 0.90      # best part + its neighbour must reproduce the other side this closely...
ADJ_MARGIN = 0.02            # ...and beat the single clause by at least this much
CONTAIN_MIN = 0.80           # share of a leftover clause's NEW words that must appear in the merged/split text
CONTAIN_MIN_WORDS = 3        # a leftover must bring at least this many words its neighbour did not already have

SEVERITY_BANDS = [(0.75, "critical"), (0.5, "high"), (0.25, "medium"), (0.0, "low")]
