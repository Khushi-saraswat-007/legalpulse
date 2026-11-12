"""Stress benchmark for version comparison: how much can a clause change before the aligner loses it?

The standard evaluation (evaluate_alignment.py) uses six easy edits, so a good aligner scores ~1.0 and there
is nothing left to improve. This script adds the hard cases:

  structural edits   a sentence inserted / dropped, a heading renamed, a clause moved, sentences reordered
  rewrite curve      a growing share (30/50/70/85 %) of a clause's words replaced, same heading and position
  false-match check  a clause replaced by an UNRELATED clause must stay "deleted + added"

For the first two groups the answer is known by construction: the edited clause must still be matched to ITS
OWN old clause. The false-match check measures the price of the structure pass: it must NOT match. Everything
is reported with and without the structure pass (ablation, config.USE_STRUCTURE_PASS).

Usage (repo root):
    python reasoning/evaluate_alignment_stress.py --embedder bow
    python reasoning/evaluate_alignment_stress.py --embedder sbert
    python reasoning/evaluate_alignment_stress.py --embedder legalbert
Writes reasoning/results/alignment_stress_<embedder>.json
Note: the word replacement is harsher than a real rewording (replacements come from the same contract), so read
the curve as "how much lexical change can the aligner survive", not as the share of real amendments it gets right.
"""
import argparse, copy, glob, json, pathlib, random, re, sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from legalpulse_reasoning import config
from legalpulse_reasoning.comparison.aligner import align_versions
from legalpulse_reasoning.comparison.embedders import make_embedder

DATA = ROOT / "data"
REWRITE_LEVELS = (0.3, 0.5, 0.7, 0.85)
UNRELATED = "replaced by an unrelated clause (must NOT match)"
sents = lambda t: [s for s in re.split(r"(?<=[.;])\s+", t.strip()) if s]


class CachedEmbedder:
    """Neural embedders are slow and the benchmark re-aligns the same clauses hundreds of times, so every distinct
    text is embedded once. Not used for BoW: it fits its vocabulary on each call, so its vectors depend on the batch."""
    def __init__(self, inner):
        self.inner, self.name, self.cache = inner, inner.name, {}

    def encode(self, texts):
        texts = list(texts)
        missing = [t for t in dict.fromkeys(texts) if t not in self.cache]
        if missing:
            for t, v in zip(missing, self.inner.encode(missing)):
                self.cache[t] = v
        return np.vstack([self.cache[t] for t in texts]) if texts else self.inner.encode([])


def _new_contract(old, new_clauses):
    return {"contract_id": old["contract_id"].replace("v1", "v2"), "version": "v2", "clauses": new_clauses, "contradictions": []}


def _edited(old, ops):
    out = []
    for i, c in enumerate(old["clauses"]):
        d = copy.deepcopy(c)
        d["clause_id"] = c["clause_id"].replace("v1_", "v2_")
        if i in ops:
            ops[i](d)
        out.append(d)
    return _new_contract(old, out)


def _matched_to_self(old, new, embedder, picks):
    got = {o: c["new_clause_ids"] for c in align_versions(old, new, embedder) for o in c["old_clause_ids"]}
    return sum(got.get(old["clauses"][i]["clause_id"]) == [old["clauses"][i]["clause_id"].replace("v1_", "v2_")] for i in picks)


def structural_edits():
    def insert(d): d["text"] += " The parties acknowledge that this obligation shall also apply to any successors and permitted assigns of either party."
    def drop(d):
        s = sents(d["text"]); d["text"] = " ".join(s[:-1]) if len(s) > 1 else d["text"]
    def reorder(d):
        s = sents(d["text"])
        if len(s) >= 3: d["text"] = " ".join([s[0]] + s[2:][::-1]) + " Each party shall notify the other promptly of any such change in writing."
    def rename(d): d["heading"] = "Miscellaneous Provisions"
    def rename_and_add(d): rename(d); insert(d)
    return {"sentence inserted": insert, "last sentence dropped": drop, "sentences reordered + one added": reorder,
            "heading renamed": rename, "heading renamed + sentence added": rename_and_add}


def load_contracts():
    files = sorted(glob.glob(str(DATA / "real" / "*_old.json"))) + sorted(glob.glob(str(DATA / "real_heldout" / "*_old.json")))
    return [json.load(open(f, encoding="utf-8")) for f in files]


def run(embedder, seed=7, picks_per_contract=4, contracts=None):
    contracts = contracts or load_contracts()
    results = {}
    for use_structure in (False, True):
        config.USE_STRUCTURE_PASS = use_structure
        res = {}
        rnd = random.Random(seed)
        for name, fn in structural_edits().items():
            ok = tot = 0
            for old in contracts:
                idxs = [i for i, c in enumerate(old["clauses"]) if len(sents(c["text"])) >= 3 and len(c["text"]) > 250]
                if len(idxs) < picks_per_contract: continue
                picks = rnd.sample(idxs, picks_per_contract)
                ok += _matched_to_self(old, _edited(old, {i: fn for i in picks}), embedder, picks); tot += len(picks)
            res[name] = {"correct": ok, "total": tot}
        rnd = random.Random(seed); ok = tot = 0
        for old in contracts:
            cl = old["clauses"]; idxs = [i for i, c in enumerate(cl) if len(c["text"]) > 250]
            if len(idxs) < 2: continue
            j = rnd.choice(idxs); k = min(len(cl) - 1, j + 6)
            order = list(range(len(cl))); order.remove(j); order.insert(k, j)
            moved = []
            for pos, i in enumerate(order):
                d = copy.deepcopy(cl[i]); d["clause_id"] = cl[i]["clause_id"].replace("v1_", "v2_"); d["number"] = str(pos + 1); moved.append(d)
            ok += _matched_to_self(old, _new_contract(old, moved), embedder, [j]); tot += 1
        res["clause moved and renumbered"] = {"correct": ok, "total": tot}
        rnd = random.Random(seed); ok = tot = 0
        for n, old in enumerate(contracts):
            donors = [c for c in contracts[(n + 1) % len(contracts)]["clauses"] if len(c["text"]) > 250]
            idxs = [i for i, c in enumerate(old["clauses"]) if len(c["text"]) > 250]
            if not idxs or not donors: continue
            for i in rnd.sample(idxs, min(picks_per_contract, len(idxs))):
                donor = rnd.choice(donors)
                def swap(d, donor=donor): d["text"], d["heading"] = donor["text"], donor.get("heading", "")
                got = {o: c["new_clause_ids"] for c in align_versions(old, _edited(old, {i: swap}), embedder) for o in c["old_clause_ids"]}
                ok += got.get(old["clauses"][i]["clause_id"]) == []; tot += 1
        res[UNRELATED] = {"correct": ok, "total": tot}
        for p in REWRITE_LEVELS:
            rnd = random.Random(seed); ok = tot = 0
            for old in contracts:
                pool = [w for c in old["clauses"] for w in c["text"].split()]
                idxs = [i for i, c in enumerate(old["clauses"]) if len(c["text"]) > 250]
                if len(idxs) < picks_per_contract: continue
                picks = rnd.sample(idxs, picks_per_contract)
                def rewrite(d, p=p): d["text"] = " ".join(rnd.choice(pool) if rnd.random() < p else w for w in d["text"].split())
                ok += _matched_to_self(old, _edited(old, {i: rewrite for i in picks}), embedder, picks); tot += len(picks)
            res[f"{int(p * 100)}% of the words replaced"] = {"correct": ok, "total": tot}
        results["with_structure_pass" if use_structure else "similarity_only"] = res
    config.USE_STRUCTURE_PASS = True
    return results


def print_table(results, name):
    a, b = results["similarity_only"], results["with_structure_pass"]
    print(f"\nEmbedder: {name}   (share of cases handled correctly)\n")
    print(f"{'edit':52} {'similarity only':>17} {'+ structure pass':>18}")
    for k in a:
        fa, fb = a[k], b[k]
        print(f"{k:52} {fa['correct']:>5}/{fa['total']:<4}({100 * fa['correct'] / max(fa['total'], 1):3.0f}%)  {fb['correct']:>5}/{fb['total']:<4}({100 * fb['correct'] / max(fb['total'], 1):3.0f}%)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--embedder", choices=["bow", "sbert", "legalbert"], default="bow")
    a = ap.parse_args()
    emb = make_embedder(a.embedder)
    if a.embedder != "bow":
        emb = CachedEmbedder(emb)
    res = run(emb)
    print_table(res, emb.name)
    out = ROOT / "results"; out.mkdir(exist_ok=True)
    (out / f"alignment_stress_{emb.name}.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"\nSaved reasoning/results/alignment_stress_{emb.name}.json")
