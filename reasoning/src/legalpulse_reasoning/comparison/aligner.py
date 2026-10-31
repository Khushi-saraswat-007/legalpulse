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
  5. Structure pass: a clause left over in the gap between two matched neighbours is paired with the
     leftover on the other side of that gap when they share a structural cue (same heading = strong;
     same number or clause type = weak, needs more text overlap). This keeps a heavily rewritten clause
     from being reported as "deleted + added" (config.USE_STRUCTURE_PASS switches it off for ablation).
  6. Each matched pair is classified: modified (meaning changed) / renumbered (only the number
     changed) / unchanged. Modified pairs also get a `semantic` block: what the change means
     (comparison/semantic.py). An optional NLI scorer can confirm that a reworded clause is harmless.
"""
from itertools import combinations
import numpy as np
from scipy.optimize import linear_sum_assignment

from .. import config
from .embedders import get_default_embedder
from .textdiff import meaning_changed, summarize_change, content_words
from .semantic import compare_clauses, describe_added, describe_removed


def _longest_increasing(pairs):
    """pairs: [(old_idx, new_idx)] sorted by old_idx -> the longest subset whose new_idx also increases
    (clauses that were moved far away are not usable as anchors)."""
    n = len(pairs)
    if not n:
        return []
    length, back = [1] * n, [-1] * n
    for a in range(n):
        for b in range(a):
            if pairs[b][1] < pairs[a][1] and length[b] + 1 > length[a]:
                length[a], back[a] = length[b] + 1, b
    end = max(range(n), key=lambda x: length[x])
    chain = []
    while end != -1:
        chain.append(pairs[end]); end = back[end]
    return chain[::-1]


_GENERIC_TYPES = {None, "", "general", "other", "none", "unknown"}


def _structure_matches(old, new, S, matches, used_o, used_n):
    """Pair up leftovers that sit in the same gap between two matched neighbours (see module docstring)."""
    anchors = _longest_increasing(sorted(matches.items()))
    bounds = [(-1, -1)] + anchors + [(len(old), len(new))]

    def cue(i, j):
        """2 = same heading (strong), 1 = same number or same clause type (weak), 0 = no structural cue."""
        ho, hn = old[i].get("heading", "").strip().lower(), new[j].get("heading", "").strip().lower()
        if ho and ho == hn:
            return 2
        no, nn = str(old[i].get("number", "")).strip(), str(new[j].get("number", "")).strip()
        if no and no == nn:
            return 1
        ot, nt = old[i].get("obligation_type"), new[j].get("obligation_type")
        return 1 if (ot not in _GENERIC_TYPES and ot == nt) else 0

    found = {}
    for (i0, j0), (i1, j1) in zip(bounds, bounds[1:]):
        go = [i for i in range(i0 + 1, i1) if i not in used_o]
        gn = [j for j in range(j0 + 1, j1) if j not in used_n]
        if not go or not gn:
            continue
        if len(go) == len(gn) and len(go) <= 3:
            cand = list(zip(go, gn))                          # same number of leftovers: keep their order
        else:
            cand = sorted(((i, j) for i in go for j in gn), key=lambda ij: -S[ij[0], ij[1]])
        taken_o, taken_n = set(), set()
        for i, j in cand:
            if i in taken_o or j in taken_n:
                continue
            c = cue(i, j)
            need = config.SIM_STRUCT_MIN if c == 2 else config.SIM_STRUCT_WEAK_MIN
            if c and S[i, j] >= need:
                found[i] = j; taken_o.add(i); taken_n.add(j)
    return found


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
            rules, single = pairs[(a, b)], col[best]      # compare with the BEST match overall, not just these two
            ok = (("top" in rules and c >= config.SIM_MATCH_THRESHOLD and c - single >= config.SPLIT_MERGE_MARGIN)
                  or ("adj" in rules and c >= config.ADJ_MIN_COMBINED and c - single >= config.ADJ_MARGIN))
            if ok:
                if winner is None or c > winner[2]:
                    winner = (s, (a, b), float(c))
        if winner:
            proposals.append(winner)
    return proposals


def align_versions(old_contract: dict, new_contract: dict, embedder=None, semantic_scorer=None) -> list:
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

    struct = set()
    if config.USE_STRUCTURE_PASS and old and new:
        extra = _structure_matches(old, new, S, matches, used_o, used_n)
        for i, j in extra.items():
            matches[i] = j; used_o.add(i); used_n.add(j); struct.add(i)

    nli_candidates = []
    for i, j in matches.items():
        o, n = old[i], new[j]
        renum = o["number"] != n["number"]
        sem = None
        if meaning_changed(o["text"], n["text"]):
            ctype, summary = "modified", summarize_change(o["text"], n["text"])
            sem = compare_clauses(o, n)
        elif renum:
            ctype, summary = "renumbered", f"Renumbered {o['number']} -> {n['number']}"
        else:
            ctype = "unchanged"
            summary = "No change" if o["text"] == n["text"] else "Reworded, same meaning"
        ch = _change([o], [n], ctype, summary, renum)
        if i in struct:
            ch["match_basis"] = "structure"
        if sem is not None:
            ch["semantic"] = sem
            if not sem["reasons"]:
                nli_candidates.append((ch, o, n, renum))
        changes.append(ch)

    if semantic_scorer and nli_candidates:
        _nli_refine(nli_candidates[: config.NLI_MAX_PAIRS], semantic_scorer)

    for i in range(len(old)):
        if i not in used_o:
            ch = _change([old[i]], [], "deleted", f"Clause removed: {old[i].get('heading') or old[i]['number']}")
            ch["semantic"] = describe_removed(old[i])
            changes.append(ch)
    for j in range(len(new)):
        if j not in used_n:
            ch = _change([], [new[j]], "added", f"New clause: {new[j].get('heading') or new[j]['number']}")
            ch["semantic"] = describe_added(new[j])
            changes.append(ch)

    pos_o = {c["clause_id"]: k for k, c in enumerate(old)}
    pos_n = {c["clause_id"]: k for k, c in enumerate(new)}
    changes.sort(key=lambda ch: pos_n[ch["new_clause_ids"][0]] if ch["new_clause_ids"] else pos_o[ch["old_clause_ids"][0]] + 0.5)
    return changes


def _nli_refine(candidates, semantic_scorer):
    """Modified pairs with no rule-detected meaning change (number, obligation word, negation, cap, party...)
    are probably rewordings. Ask the NLI model in both directions: if each wording entails the other, the
    change is harmless. A strong contradiction is reported as a reason. `semantic_scorer(pairs)` takes
    [(premise, hypothesis)] and returns one {entailment, neutral, contradiction} dict per pair."""
    fwd = [(o["text"], n["text"]) for _, o, n, _ in candidates]
    bwd = [(n["text"], o["text"]) for _, o, n, _ in candidates]
    probs = semantic_scorer(fwd + bwd)
    k = len(candidates)
    for idx, (ch, o, n, renum) in enumerate(candidates):
        f, b = probs[idx], probs[k + idx]
        sem = ch["semantic"]
        sem["nli"] = {"old_entails_new": round(f["entailment"], 3), "new_entails_old": round(b["entailment"], 3),
                      "contradiction": round(max(f["contradiction"], b["contradiction"]), 3)}
        if f["entailment"] >= config.NLI_SAME_MEANING and b["entailment"] >= config.NLI_SAME_MEANING:
            ch["change_type"] = "renumbered" if renum else "unchanged"
            ch["summary"] = f"Renumbered {o['number']} -> {n['number']}" if renum else "Reworded, same meaning (NLI)"
            sem["reasons"] = ["same meaning (confirmed by NLI)"]
            sem["severity_hint"] = 0.0
        elif sem["nli"]["contradiction"] >= config.NLI_CONTRADICTION:
            sem["reasons"] = ["the new wording contradicts the old (NLI)"]
            sem["severity_hint"] = max(sem["severity_hint"], 0.8)
