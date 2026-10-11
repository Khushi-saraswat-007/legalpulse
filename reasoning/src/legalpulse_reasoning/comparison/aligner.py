"""Module 3: Version comparison.

Aligns clauses of an old and a new contract version by MEANING (embeddings), not by position.

Algorithm
  1. Embed every clause; S[i, j] = cosine similarity of old clause i and new clause j.
  2. Split/merge pre-pass: if two new clauses together describe an old clause clearly better than
     any single one does (margin test), it is a SPLIT; the mirror case is a MERGE.
  3. One-to-one matching of the remaining clauses (Hungarian algorithm). A pair is accepted if
     similarity >= SIM_MATCH_THRESHOLD, or the headings are identical and similarity >= SIM_HEADING_MIN.
  4. Unmatched old clauses are DELETED, unmatched new clauses are ADDED.
  5. Each matched pair is classified: modified (meaning changed) / renumbered (only the number
     changed) / unchanged.
"""
from itertools import combinations
import numpy as np
from scipy.optimize import linear_sum_assignment

from .. import config
from .embedders import get_default_embedder
from .textdiff import meaning_changed, summarize_change


def _change(old, new, change_type, summary, renumbered=False):
    return {
        "old_clause_id": old[0]["clause_id"] if old else None,
        "new_clause_id": new[0]["clause_id"] if new else None,
        "old_clause_ids": [c["clause_id"] for c in old],
        "new_clause_ids": [c["clause_id"] for c in new],
        "change_type": change_type,
        "renumbered": renumbered,
        "summary": summary,
    }


def _combo_proposals(src_emb, parts_emb_fn, src_texts, part_texts, S, embedder, by_new):
    """Propose (source index, (part j, part k), combined_sim, margin) for split (by_new=False)
    or merge (by_new=True). For a split, `source` = old clauses and `parts` = new clauses."""
    proposals = []
    n_src = S.shape[1] if by_new else S.shape[0]
    for s in range(n_src):
        col = S[:, s] if by_new else S[s, :]
        cand = [int(p) for p in np.argsort(-col)[:4] if col[p] >= config.SIM_PART_MIN]
        if len(cand) < 2:
            continue
        best_single = max(col[p] for p in cand)
        pairs = [tuple(sorted(pr)) for pr in combinations(cand, 2)]
        texts = [part_texts[a] + " " + part_texts[b] for a, b in pairs]
        sims = embedder.encode(texts) @ src_emb[s]
        k = int(np.argmax(sims))
        c, margin = float(sims[k]), float(sims[k] - best_single)
        if c >= config.SIM_MATCH_THRESHOLD and margin >= config.SPLIT_MERGE_MARGIN:
            proposals.append((s, pairs[k], c, margin))
    return proposals


def align_versions(old_contract: dict, new_contract: dict, embedder=None) -> list:
    embedder = embedder or get_default_embedder()
    old, new = old_contract["clauses"], new_contract["clauses"]
    if not old and not new:
        return []
    o_txt, n_txt = [c["text"] for c in old], [c["text"] for c in new]
    Eo = embedder.encode(o_txt) if old else np.zeros((0, 1))
    En = embedder.encode(n_txt) if new else np.zeros((0, 1))
    S = Eo @ En.T if old and new else np.zeros((len(old), len(new)))

    used_o, used_n, changes = set(), set(), []

    # --- split / merge pre-pass ---
    props = []
    if old and new:
        for i, (a, b), c, m in _combo_proposals(Eo, None, o_txt, n_txt, S, embedder, by_new=False):
            props.append(("split", c, [i], [a, b]))
        for j, (a, b), c, m in _combo_proposals(En, None, n_txt, o_txt, S, embedder, by_new=True):
            props.append(("merged", c, [a, b], [j]))
    for kind, c, oi, nj in sorted(props, key=lambda p: -p[1]):
        if used_o & set(oi) or used_n & set(nj):
            continue
        used_o |= set(oi); used_n |= set(nj)
        oc, nc = [old[i] for i in oi], [new[j] for j in nj]
        summary = (f"Clause {oc[0]['number']} split into clauses {', '.join(c['number'] for c in nc)}"
                   if kind == "split" else
                   f"Clauses {', '.join(c['number'] for c in oc)} merged into clause {nc[0]['number']}")
        changes.append(_change(oc, nc, kind, summary, True))

    # --- one-to-one matching of the rest ---
    ro = [i for i in range(len(old)) if i not in used_o]
    rn = [j for j in range(len(new)) if j not in used_n]
    if ro and rn:
        score = np.zeros((len(ro), len(rn)))
        for a, i in enumerate(ro):
            for b, j in enumerate(rn):
                same_head = old[i].get("heading", "").strip().lower() == new[j].get("heading", "").strip().lower() != ""
                score[a, b] = S[i, j] + (config.HEADING_BONUS if same_head else 0.0)
        rows, cols = linear_sum_assignment(-score)
        for a, b in zip(rows, cols):
            i, j = ro[a], rn[b]
            same_head = old[i].get("heading", "").strip().lower() == new[j].get("heading", "").strip().lower() != ""
            if S[i, j] >= config.SIM_MATCH_THRESHOLD or (same_head and S[i, j] >= config.SIM_HEADING_MIN):
                used_o.add(i); used_n.add(j)
                o, n = old[i], new[j]
                renum = o["number"] != n["number"]
                if meaning_changed(o["text"], n["text"]):
                    ctype, summary = "modified", summarize_change(o["text"], n["text"])
                elif renum:
                    ctype, summary = "renumbered", f"Renumbered {o['number']} -> {n['number']}"
                else:
                    ctype = "unchanged"
                    summary = "No change" if o["text"] == n["text"] else "Reworded, same meaning"
                changes.append(_change([o], [n], ctype, summary, renum))

    for i in range(len(old)):
        if i not in used_o:
            changes.append(_change([old[i]], [], "deleted", f"Clause removed: {old[i].get('heading') or old[i]['number']}"))
    for j in range(len(new)):
        if j not in used_n:
            changes.append(_change([], [new[j]], "added", f"New clause: {new[j].get('heading') or new[j]['number']}"))

    pos_o = {c["clause_id"]: k for k, c in enumerate(old)}
    pos_n = {c["clause_id"]: k for k, c in enumerate(new)}
    changes.sort(key=lambda ch: pos_n[ch["new_clause_ids"][0]] if ch["new_clause_ids"] else pos_o[ch["old_clause_ids"][0]] + 0.5)
    return changes
