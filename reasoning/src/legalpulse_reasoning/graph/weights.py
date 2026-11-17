"""Edge weights: computed from the contract instead of fixed constants.

shared_party    -> IDF weight. A party that appears in few clauses links them; one that appears in
                   every clause ("Supplier") links nothing (weight 0). This removes the party noise.
shared_term     -> base value, NOT IDF. A defined term used by many clauses is a real dependency:
                   if its definition changes, all of them are affected.
cross_reference -> base value. An explicit citation is a fact, not a statistic.
The base values come from config.EDGE_WEIGHTS, or from weights.json once they have been fitted on
labelled data (see config.WEIGHTS_FILE).
config.WEIGHT_MODE = "fixed" switches everything back to the old constants (reproduces the paper).
"""
import json
import math
import pathlib

from .. import config


def base_weights() -> dict:
    """Ceiling per edge type. Overridden by the fitted file when it exists."""
    w = dict(config.EDGE_WEIGHTS)
    path = pathlib.Path(config.WEIGHTS_FILE) if config.WEIGHTS_FILE else None
    if path and path.exists():
        w.update(json.loads(path.read_text()))
    return w


def idf_factor(df: int, n: int) -> float:
    """0..1. df = number of clauses that contain the party/term, n = number of clauses."""
    if n <= 1 or df >= n:
        return 0.0
    return math.log(n / df) / math.log(n)


def edge_weight(edge_type: str, df: int = 0, n: int = 0) -> float:
    base = base_weights()[edge_type]
    if config.WEIGHT_MODE == "fixed" or edge_type != "shared_party":
        return base
    return round(base * idf_factor(df, n), 3)
