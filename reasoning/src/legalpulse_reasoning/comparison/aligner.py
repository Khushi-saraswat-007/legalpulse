"""Module 3: Version comparison (TODO).

Plan:
  1. Embed every clause in old and new versions (sentence-transformers).
  2. Cosine-similarity matrix; match one-to-one above SIM_MATCH_THRESHOLD
     (Hungarian algorithm via scipy.optimize.linear_sum_assignment).
  3. Leftover old clause matching 2+ new clauses  -> "split".
     2+ old clauses matching one new clause       -> "merged".
     Same text, different number                  -> "renumbered".
     No match                                     -> "deleted" / "added".
  4. For matched pairs with changed text, generate a plain-language summary.
Returns a list of change dicts matching risk_report.schema.json `changes`.
"""


def align_versions(old_contract: dict, new_contract: dict) -> list:
    raise NotImplementedError("Build step 4")
