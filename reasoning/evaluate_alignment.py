"""Score the version aligner against the answer keys.

Usage (from the repo root):
    python reasoning/evaluate_alignment.py --embedder bow
    python reasoning/evaluate_alignment.py --embedder sbert
    python reasoning/evaluate_alignment.py --embedder bow --dir real            # real contracts (dev)
    python reasoning/evaluate_alignment.py --embedder bow --dir real_heldout    # real contracts (test)

Two numbers matter for the report:
  * Mapping P/R/F1: did the aligner find the right old->new clause groups (incl. split/merge/added/deleted)?
  * Type accuracy: for correctly mapped groups, did it name the change type correctly?
"""
import argparse, json, pathlib, sys, collections
ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from legalpulse_reasoning.comparison.aligner import align_versions
from legalpulse_reasoning.comparison.embedders import BagOfWordsEmbedder, SBertEmbedder

DATA = ROOT / "data"


def key(ch):
    return (frozenset(ch["old_clause_ids"] if "old_clause_ids" in ch else ch["old"]),
            frozenset(ch["new_clause_ids"] if "new_clause_ids" in ch else ch["new"]))


def evaluate(embedder, folder="mock", verbose=True):
    MOCK = DATA / folder
    pair_ids = sorted(f.name.split("_")[0] for f in MOCK.glob("*_truth.json"))
    tot = collections.Counter()
    per_pair, errors = {}, []
    confusion = collections.Counter()
    per_type = collections.defaultdict(lambda: [0, 0])          # truth type -> [found with right type, total]
    for p in pair_ids:
        old = json.loads((MOCK / f"{p}_old.json").read_text(encoding="utf-8"))
        new = json.loads((MOCK / f"{p}_new.json").read_text(encoding="utf-8"))
        truth = json.loads((MOCK / f"{p}_truth.json").read_text(encoding="utf-8"))["changes"]
        pred = align_versions(old, new, embedder)
        t = {key(c): c["change_type"] for c in truth}
        q = {key(c): c["change_type"] for c in pred}
        hit = set(t) & set(q)
        type_ok = sum(t[k] == q[k] for k in hit)
        per_pair[p] = (len(hit), len(q), len(t), type_ok)
        tot.update(hit=len(hit), pred=len(q), truth=len(t), type_ok=type_ok)
        for k in t:
            per_type[t[k]][1] += 1
            per_type[t[k]][0] += int(k in q and q[k] == t[k])
        for k in hit:
            confusion[(t[k], q[k])] += 1
            if t[k] != q[k]:
                errors.append(f"{p}: wrong type for {sorted(k[0])}->{sorted(k[1])}: truth={t[k]} pred={q[k]}")
        for k in set(t) - set(q):
            errors.append(f"{p}: MISSED mapping {sorted(k[0])}->{sorted(k[1])} (truth={t[k]})")
        for k in set(q) - set(t):
            errors.append(f"{p}: EXTRA mapping {sorted(k[0])}->{sorted(k[1])} (pred={q[k]})")
    P = tot["hit"] / max(tot["pred"], 1); R = tot["hit"] / max(tot["truth"], 1)
    F = 2 * P * R / max(P + R, 1e-9); acc = tot["type_ok"] / max(tot["hit"], 1)
    res = {"embedder": embedder.name, "precision": round(P, 3), "recall": round(R, 3), "f1": round(F, 3),
           "type_accuracy": round(acc, 3), "per_pair": {k: dict(zip(("matched", "predicted", "truth", "type_correct"), v)) for k, v in per_pair.items()},
           "per_type_recall": {k: {"correct": v[0], "total": v[1]} for k, v in sorted(per_type.items())},
           "errors": errors}
    if verbose:
        print(f"Embedder: {embedder.name}")
        print(f"Mapping  precision={P:.3f} recall={R:.3f} F1={F:.3f}")
        print(f"Type accuracy on correctly mapped groups: {acc:.3f} ({tot['type_ok']}/{tot['hit']})")
        for p, (h, pr, tr, ok) in per_pair.items():
            print(f"  {p}: matched {h}/{tr} truth groups, {pr} predicted, types right {ok}/{h}")
        print("Per change type (correct / total):  " + "  ".join(f"{k} {v[0]}/{v[1]}" for k, v in sorted(per_type.items())))
        print("Errors:" if errors else "No errors.")
        for e in errors:
            print("  -", e)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--embedder", choices=["bow", "sbert"], default="bow")
    ap.add_argument("--dir", default="mock", help="folder under reasoning/data: 'mock', 'real' or 'real_heldout'")
    a = ap.parse_args()
    emb = BagOfWordsEmbedder() if a.embedder == "bow" else SBertEmbedder()
    res = evaluate(emb, a.dir)
    out = ROOT / "results"; out.mkdir(exist_ok=True)
    fname = f"alignment_{a.embedder}.json" if a.dir == "mock" else f"alignment_{a.embedder}_{a.dir}.json"
    (out / fname).write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"\nSaved reasoning/results/{fname}")