# Test data: old/new contract pairs

Four hand-made version pairs. Files per pair `pN`:
- `pN_old.json`, `pN_new.json`: contracts in `schemas/contract.schema.json` format
  (clause ids look like `p1v1_5` = pair 1, version 1, clause 5)
- `pN_truth.json`: the answer key

## Truth format
Each entry in `changes` maps old clause ids to new clause ids:
- `change_type`: unchanged | modified | renumbered | added | deleted | split | merged
- `unchanged` means SAME MEANING (it may still be reworded: `reworded_only: true`)
- `renumbered: true` means the clause number changed (also set on modified clauses that moved)
- split = 1 old -> 2+ new, merged = 2+ old -> 1 new, added = no old, deleted = no new

`expected_impacts`: if the key clause changes, these clauses must appear in the impact trace.

| Pair | Domain | Covers |
|---|---|---|
| p1 | Supply agreement | modified, reworded, deleted, added, renumbered |
| p2 | Service agreement | split, merge |
| p3 | Lease | deletion, reversed rule, added clause that contradicts another (contradiction included in `p3_new.json`) |
| p4 | Software licence | one-word changes, meaning flip with high text overlap, "except as provided" / "notwithstanding" clauses |

Not for training: this is evaluation data only. Do not tune thresholds on all four and then report the same numbers; hold one pair out.
