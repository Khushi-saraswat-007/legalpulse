"""Module 6: Risk scoring (basic version, to be extended).

score = 0.5 * change_weight + 0.3 * impact_breadth + 0.2 * contradiction_flag
Every component is returned so the explanation can show WHY a score was given.
"""
from .. import config

CHANGE_WEIGHT = {"deleted": 1.0, "modified": 0.7, "split": 0.6, "merged": 0.6,
                 "added": 0.5, "renumbered": 0.2, "unchanged": 0.0}


def severity_for(score: float) -> str:
    for threshold, label in config.SEVERITY_BANDS:
        if score >= threshold:
            return label
    return "low"


def score_risk(change: dict, impacted: list, has_contradiction: bool) -> dict:
    cw = CHANGE_WEIGHT.get(change["change_type"], 0.5)
    breadth = min(len(impacted) / 5, 1.0)
    score = 0.5 * cw + 0.3 * breadth + 0.2 * (1.0 if has_contradiction else 0.0)
    return {
        "score": round(score, 3),
        "severity": severity_for(score),
        "components": {"change_weight": cw, "impact_breadth": round(breadth, 2),
                       "contradiction": has_contradiction},
    }
