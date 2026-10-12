"""Module 3: Version comparison.

Aligns clauses of an old and a new contract version by MEANING (embeddings), not by position.

Algorithm
  1. Embed every clause; S[i, j] = cosine similarity of old clause i and new clause j.
  2. Split/merge pre-pass: if two new clauses together describe an old clause clearly better than
     any single one does (margin test), it is a SPLIT; the mirror case is a MERGE.
  3. One-to-one matching of the remaining clauses (Hungarian algorithm). A pair is accepted if
     similarity >= SIM_MATCH_THRESHOLD, or the headings are identical and similarity >= SIM_HEADING_MIN.
  4. Leftovers whose words are almost entirely contained in a neighbouring matched clause are
     absorbed (-> merged / split); the remaining leftovers are DELETED (old) or ADDED (new).
  5. Each matched pair is classified: modified (meaning changed) / renumbered (only the number
     changed) / unchanged.
"""
from itertools import combinations
import numpy as np
from scipy.optimize import linear_sum_assignment

from .. import config
from .embedders import get_default_embedder
from .textdiff import meaning_changed, summarize_change, content_words


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


def _combo_proposals(src_emb, part_texts, S, embedder, by_new):
    """Propose (source index, (part a, part b), combined_sim) for splits (by_new=False: one OLD clause
    explained by two NEW clauses) or merges (by_new=True: one NEW clause explained by two OLD clauses).

    Two kinds of candidate pairs are tried for every source clause:
      * any two of its top-4 most similar parts      (must beat the best single part by SPLIT_MERGE_MARGIN)
      * its best part plus that part's neighbour     (must reproduce the source very closely; this catches
        uneven splits/merges where one half is tiny and its own similarity is too low to be a candidate)
    """
    proposals = []
    n_src = S.shape[1] if by_new else S.shape[0]
    n_parts = len(part_texts)
    for s in range(n_src):
        col = S[:, s] if by_new else S[s, :]
        order = [int(p) for p in np.argsort(-col)]
        best = order[0]
        if col[best] < config.SIM_PART_MIN:
            continue
        cand = [p for p in order[:4] if col[p] >= config.SIM_PART_MIN]
        pairs = {}                               # candidate pair -> which rules it may qualify under
        for pr in combinations(cand, 2):
            pairs.setdefault(tuple(sorted(pr)), set()).add("top")
        for nb in (best - 1, best + 1):
            if 0 <= nb < n_parts:
                pairs.setdefault(tuple(sorted((best, nb))), set()).add("adj")
        keys = list(pairs)
        if not keys:
            continue
        sims = embedder.encode([part_texts[a] + " " + part_texts[b] for a, b in keys]) @ src_emb[s]
        winner = None
        for (a, b), c in zip(keys, sims):
            rules, single = pairs[(a, b)], max(col[a], col[b])
            ok = (("top" in rules and c >= config.SIM_MATCH_THRESHOLD and c - single >= config.SPLIT_MERGE_MARGIN)
                  or ("adj" in rules and c >= config.ADJ_MIN_COMBINED and c - single >= config.ADJ_MARGIN))
            if ok:
                if winner is None or c > winner[2]:
                    winner = (s, (a, b), float(c))
        if winner:
            proposals.append(winner)
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
        for i, (a, b), c in _combo_proposals(Eo, n_txt, S, embedder, by_new=False):
            props.append(("split", c, [i], [a, b]))
        for j, (a, b), c in _combo_proposals(En, o_txt, S, embedder, by_new=True):
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
    def same_head(i, j):
        h = old[i].get("heading", "").strip().lower()
        return h != "" and h == new[j].get("heading", "").strip().lower()

    matches = {}                                     # old index -> new index
    ro = [i for i in range(len(old)) if i not in used_o]
    rn = [j for j in range(len(new)) if j not in used_n]
    if ro and rn:
        score = np.zeros((len(ro), len(rn)))
        for a, i in enumerate(ro):
            for b, j in enumerate(rn):
                score[a, b] = S[i, j] + (config.HEADING_BONUS if same_head(i, j) else 0.0)
        rows, cols = linear_sum_assignment(-score)
        for a, b in zip(rows, cols):
            i, j = ro[a], rn[b]
            if S[i, j] >= config.SIM_MATCH_THRESHOLD or (same_head(i, j) and S[i, j] >= config.SIM_HEADING_MIN):
                matches[i] = j
                used_o.add(i); used_n.add(j)

    # --- absorbed leftovers: a would-be "deleted"/"added" clause whose words sit inside a neighbour ---
    def absorbed(small, host_after, host_before):
        """True if `small` was folded into `host_after`: it brings words the neighbour did not have
        before (`host_before`), and those words now appear in `host_after`. Words the neighbour already
        had prove nothing (real contracts repeat boilerplate), so they are ignored."""
        fresh = content_words(small) - content_words(host_before)
        return (len(fresh) >= config.CONTAIN_MIN_WORDS
                and len(fresh & content_words(host_after)) / len(fresh) >= config.CONTAIN_MIN)

    for d in range(len(old)):                        # leftover OLD clause inside a matched neighbour -> merged
        if d in used_o:
            continue
        for nb in (d - 1, d + 1):
            if nb in matches and absorbed(old[d]["text"], new[matches[nb]]["text"], old[nb]["text"]):
                j = matches.pop(nb); used_o.add(d)
                oi = sorted((d, nb))
                changes.append(_change([old[x] for x in oi], [new[j]], "merged",
                               f"Clauses {', '.join(old[x]['number'] for x in oi)} merged into clause {new[j]['number']}", True))
                break
    by_new = {j: i for i, j in matches.items()}
    for a_ in range(len(new)):                       # leftover NEW clause inside a matched neighbour -> split
        if a_ in used_n:
            continue
        for nb in (a_ - 1, a_ + 1):
            if nb in by_new and by_new[nb] in matches and absorbed(new[a_]["text"], old[by_new[nb]]["text"], new[nb]["text"]):
                i = by_new.pop(nb); matches.pop(i); used_n.add(a_)
                nj = sorted((a_, nb))
                changes.append(_change([old[i]], [new[x] for x in nj], "split",
                               f"Clause {old[i]['number']} split into clauses {', '.join(new[x]['number'] for x in nj)}", True))
                break

    for i, j in matches.items():
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