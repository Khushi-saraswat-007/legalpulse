"""Score NLI backends on a CSV with columns premise,hypothesis,label (entailment/contradiction/neutral).

Reports accuracy, macro-F1, per-class precision/recall, the confusion matrix and a contradiction
threshold sweep (contradiction-vs-rest on P(contradiction)). --hypothesis-only blanks the premise
(PS-3 ablation, Gururangan et al. 2018): if it scores far above chance, the model is using
annotation artefacts in the hypothesis rather than reasoning over the pair.

Usage:  python nlp_core/scripts/evaluate_nli.py --csv dev.csv --backend both --tag dev
        add --hypothesis-only for the ablation;  --out results/nli_eval.json to save.
Tune on dev; run the test CSV once at the end.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

CLASSES = ["entailment", "contradiction", "neutral"]
THRESHOLDS = [0.5, 0.7, 0.8, 0.9]


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    bad = [r["label"] for r in rows if r["label"] not in CLASSES]
    if bad:
        raise ValueError(f"Unknown labels {sorted(set(bad))}; use {CLASSES}")
    return rows


def predict_all(backend, rows, hypothesis_only=False, batch=64):
    pairs = [("" if hypothesis_only else r["premise"], r["hypothesis"]) for r in rows]
    out = []
    for i in range(0, len(pairs), batch):
        out.extend(backend.predict(pairs[i:i + batch]))
        print(f"  scored {min(i + batch, len(pairs))}/{len(pairs)}", end="\r", file=sys.stderr)
    print(file=sys.stderr)
    return [{c: float(p.get(c, 0.0)) for c in CLASSES} for p in out]


def metrics(gold, probs):
    pred = [max(CLASSES, key=lambda c: p[c]) for p in probs]
    n = len(gold)
    conf = {g: {p: 0 for p in CLASSES} for g in CLASSES}
    for g, p in zip(gold, pred):
        conf[g][p] += 1
    per = {}
    for c in CLASSES:
        tp = conf[c][c]
        fp = sum(conf[g][c] for g in CLASSES if g != c)
        fn = sum(conf[c][p] for p in CLASSES if p != c)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        per[c] = {"precision": prec, "recall": rec, "f1": f1, "support": sum(conf[c].values())}
    sweep = []
    for t in THRESHOLDS:
        flag = [p["contradiction"] >= t for p in probs]
        tp = sum(f and g == "contradiction" for f, g in zip(flag, gold))
        fp = sum(f and g != "contradiction" for f, g in zip(flag, gold))
        fn = sum((not f) and g == "contradiction" for f, g in zip(flag, gold))
        sweep.append({"threshold": t, "tp": tp, "fp": fp, "fn": fn,
                      "precision": tp / (tp + fp) if tp + fp else 0.0,
                      "recall": tp / (tp + fn) if tp + fn else 0.0})
    return {"n": n, "accuracy": sum(g == p for g, p in zip(gold, pred)) / n if n else 0.0,
            "macro_f1": sum(per[c]["f1"] for c in CLASSES) / len(CLASSES),
            "per_class": per, "confusion": conf, "contradiction_sweep": sweep}


def show(name, m, hypothesis_only):
    mode = "HYPOTHESIS-ONLY" if hypothesis_only else "premise + hypothesis"
    print(f"\n== {name} ({mode}), n={m['n']}")
    print(f"accuracy={m['accuracy']:.3f}  macro-F1={m['macro_f1']:.3f}  (chance for 3 balanced classes = 0.333)")
    for c in CLASSES:
        p = m["per_class"][c]
        print(f"  {c:13} P={p['precision']:.2f} R={p['recall']:.2f} F1={p['f1']:.2f} n={p['support']}")
    print("  confusion (rows = gold, cols = predicted):")
    print("  " + " " * 14 + "".join(f"{c[:6]:>8}" for c in CLASSES))
    for g in CLASSES:
        print(f"  {g:13} " + "".join(f"{m['confusion'][g][p]:8d}" for p in CLASSES))
    print("  contradiction vs rest:")
    for s in m["contradiction_sweep"]:
        print(f"    P(contradiction)>={s['threshold']:.1f}  TP={s['tp']} FP={s['fp']} FN={s['fn']}  "
              f"precision={s['precision']:.2f} recall={s['recall']:.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--backend", choices=["rule", "hf", "both"], default="both")
    ap.add_argument("--model", default=None)
    ap.add_argument("--hypothesis-only", action="store_true")
    ap.add_argument("--tag", default="", help="free label stored in the JSON, e.g. dev or test")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    from legalpulse_nlp import HFNLIBackend, RuleBasedNLIBackend
    rows = read_rows(a.csv)
    gold = [r["label"] for r in rows]
    backends = []
    if a.backend in ("rule", "both"):
        backends.append(RuleBasedNLIBackend())
    if a.backend in ("hf", "both"):
        backends.append(HFNLIBackend(a.model) if a.model else HFNLIBackend())
    result = {"csv": str(a.csv), "tag": a.tag, "hypothesis_only": a.hypothesis_only, "backends": {}}
    for b in backends:
        name = getattr(b, "name", type(b).__name__)
        print(f"scoring {name} ...", file=sys.stderr)
        m = metrics(gold, predict_all(b, rows, a.hypothesis_only))
        show(name, m, a.hypothesis_only)
        result["backends"][name] = m
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nsaved {a.out}")


if __name__ == "__main__":
    main()
