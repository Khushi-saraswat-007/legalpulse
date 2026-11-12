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

# Structure-aware matching: a clause left over between two matched neighbours is paired with the clause that
# sits in the same gap if it has a structural cue (heading, number or clause type) and some text overlap.
USE_STRUCTURE_PASS = True    # switch off to reproduce the similarity-only baseline (ablation)
SIM_STRUCT_MIN = 0.20        # same heading: minimum similarity for a structure-based match (far below SIM_MATCH_THRESHOLD)
SIM_STRUCT_WEAK_MIN = 0.50   # only the same number / clause type (weaker cue): needs more text overlap (0.35 gave 5% false matches)

# Semantic change layer (comparison/semantic.py): what a modification MEANS, added on top of the base score
SEMANTIC_BONUS_MAX = 0.20    # a change with maximal semantic severity adds this much to the risk score
NLI_SAME_MEANING = 0.85      # both directions must entail each other at least this strongly to call a rewording harmless
NLI_CONTRADICTION = 0.60     # old -> new (or new -> old) contradiction probability that is reported
NLI_MAX_PAIRS = 60           # cap on clause pairs sent to the NLI model per analysis (speed)

SEVERITY_BANDS = [(0.75, "critical"), (0.5, "high"), (0.25, "medium"), (0.0, "low")]
