"""Score the version aligner against the hand-made answer keys.

Usage (from the repo root):
    python reasoning/evaluate_alignment.py --embedder bow
    python reasoning/evaluate_alignment.py --embedder sbert

Two numbers matter for the report:
  * Mapping P/R/F1: did the aligner find the right old->new clause groups (incl. split/merge/added/deleted)?
  * Type accuracy: for correctly mapped groups, did it name the change type correctly?
"""
import argparse, json, pathlib, sys, collections
ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from legalpulse_reasoning.comparison.aligner import align_versions
from legalpulse_reasoning.comparison.embedders import BagOfWordsEmbedder, SBertEmbedder

MOCK = ROOT / "data" / "mock"


def key(ch):
    return (frozenset(ch["old_clause_ids"] if "old_clause_ids" in ch else ch["old"]),
            frozenset(ch["new_clause_ids"] if "new_clause_ids" in ch else ch["new"]))


def evaluate(embedder, verbose=True):
    tot = collections.Counter()
    per_pair, errors = {}, []
    confusion = collections.Counter()
    for p in ("p1", "p2", "p3", "p4"):
        old = json.loads((MOCK / f"{p}_old.json").read_text())
        new = json.loads((MOCK / f"{p}_new.json").read_text())
        truth = json.loads((MOCK / f"{p}_truth.json").read_text())["changes"]
        pred = align_versions(old, new, embedder)
        t = {key(c): c["change_type"] for c in truth}
        q = {key(c): c["change_type"] for c in pred}
        hit = set(t) & set(q)
        type_ok = sum(t[k] == q[k] for k in hit)
        per_pair[p] = (len(hit), len(q), len(t), type_ok)
        tot.update(hit=len(hit), pred=len(q), truth=len(t), type_ok=type_ok)
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
           "errors": errors}
    if verbose:
        print(f"Embedder: {embedder.name}")
        print(f"Mapping  precision={P:.3f} recall={R:.3f} F1={F:.3f}")
        print(f"Type accuracy on correctly mapped groups: {acc:.3f} ({tot['type_ok']}/{tot['hit']})")
        for p, (h, pr, tr, ok) in per_pair.items():
            print(f"  {p}: matched {h}/{tr} truth groups, {pr} predicted, types right {ok}/{h}")
        print("Errors:" if errors else "No errors.")
        for e in errors:
            print("  -", e)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--embedder", choices=["bow", "sbert"], default="bow")
    a = ap.parse_args()
    emb = BagOfWordsEmbedder() if a.embedder == "bow" else SBertEmbedder()
    res = evaluate(emb)
    out = ROOT / "results"; out.mkdir(exist_ok=True)
    (out / f"alignment_{a.embedder}.json").write_text(json.dumps(res, indent=2))
    print(f"\nSaved reasoning/results/alignment_{a.embedder}.json")
