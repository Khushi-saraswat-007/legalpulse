"""Evaluate nlp_core against the hand-made mock contracts in reasoning/data/mock/.

IMPORTANT CAVEATS (state these in the report):
  * The mock files were written by a teammate; they are a sanity check, NOT an independent benchmark.
  * We rebuild raw text from each mock JSON ("N. Heading\\nbody"), so this tests metadata rules and the
    splitter on CLEAN text only. Real PDFs are messier: test those by hand and record the errors.
  * Mock `references` also contain implicit links (shared defined terms), while we only extract explicit
    "Clause N" citations, so the references score is a lower bound on what we actually do.

Usage:  python scripts/evaluate_extraction.py [--backend rule|hf] [--model NAME]
"""
import argparse
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from legalpulse_nlp import RuleBasedNLIBackend, HFNLIBackend, detect_contradictions, extract_from_text  # noqa: E402

MOCK = ROOT.parent / "reasoning" / "data" / "mock"


def render(contract):
    out = []
    for c in contract["clauses"]:
        out.append(f"{c['number']}. {c['heading']}" if c.get("heading") else f"{c['number']}.")
        out.append(c["text"])
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["rule", "hf"], default="rule")
    ap.add_argument("--model", default=None)
    args = ap.parse_args()
    backend = RuleBasedNLIBackend() if args.backend == "rule" else (HFNLIBackend(args.model) if args.model else HFNLIBackend())

    files = sorted(glob.glob(str(MOCK / "p*_old.json")) + glob.glob(str(MOCK / "p*_new.json")))
    hit, tot = defaultdict(int), defaultdict(int)
    errors = []
    cm = {"tune (p1-p3)": [0, 0, 0, 0], "held-out (p4)": [0, 0, 0, 0]}   # tp fp fn tn
    for f in files:
        grp = "held-out (p4)" if Path(f).name.startswith("p4") else "tune (p1-p3)"
        gold = json.load(open(f))
        res = extract_from_text(render(gold), gold["contract_id"], gold["version"])
        pred = res.contract
        tot["clause_count"] += 1
        hit["clause_count"] += len(pred["clauses"]) == len(gold["clauses"])
        for g, p in zip(gold["clauses"], pred["clauses"]):
            id_map = {gc["clause_id"]: pc["clause_id"] for gc, pc in zip(gold["clauses"], pred["clauses"])}
            checks = {
                "number": g["number"] == p["number"],
                "heading": g["heading"] == p["heading"],
                "text": g["text"] == p["text"],
                "obligation_type": g["obligation_type"] == p["obligation_type"],
                "deadline": g["deadline"] == p["deadline"],
                "parties": set(g["parties"]) == set(p["parties"]),
                "defined_terms": set(g["defined_terms"]) == set(p["defined_terms"]),
                "references": {id_map.get(r) for r in g["references"]} == set(p["references"]),
            }
            for k, ok in checks.items():
                tot[k] += 1
                hit[k] += ok
                if not ok:
                    errors.append(f"{Path(f).name} clause {g['number']} [{k}]: gold={g.get(k)!r} pred={p.get(k)!r}")
        # contradictions: gold = the file's own `contradictions` list (only p3_new has one)
        gold_pairs = {frozenset((r["clause_a"], r["clause_b"])) for r in gold.get("contradictions", []) if r["label"] == "contradiction"}
        pred_pairs = set()
        idx = {pc["clause_id"]: gc["clause_id"] for gc, pc in zip(gold["clauses"], pred["clauses"])}
        for r in detect_contradictions(pred["clauses"], backend=backend):
            pred_pairs.add(frozenset((idx[r["clause_a"]], idx[r["clause_b"]])))
        n = len(gold["clauses"])
        all_pairs = n * (n - 1) // 2
        c = cm[grp]
        c[0] += len(gold_pairs & pred_pairs); c[1] += len(pred_pairs - gold_pairs); c[2] += len(gold_pairs - pred_pairs)
        c[3] += all_pairs - len(gold_pairs | pred_pairs)
        for pr in pred_pairs - gold_pairs:
            errors.append(f"{Path(f).name} FALSE POSITIVE contradiction {sorted(pr)}")
        for pr in gold_pairs - pred_pairs:
            errors.append(f"{Path(f).name} MISSED contradiction {sorted(pr)}")

    print(f"Contracts evaluated: {len(files)}   NLI backend: {getattr(backend, 'name', backend)}\n")
    print("Module 1 field accuracy (exact match vs mock labels)")
    for k in ["clause_count", "number", "heading", "text", "obligation_type", "deadline", "parties", "defined_terms", "references"]:
        print(f"  {k:16s} {hit[k]:3d}/{tot[k]:3d} = {hit[k] / tot[k]:.3f}")
    print("\nModule 2 contradiction detection (pair level). Thresholds tuned on p1-p3 only; p4 is held out.")
    for grp, (tp, fp, fn, tn) in cm.items():
        prec = tp / (tp + fp) if tp + fp else float("nan")
        rec = tp / (tp + fn) if tp + fn else float("nan")
        f1 = 2 * prec * rec / (prec + rec) if tp else 0.0
        print(f"  {grp:14s} TP={tp} FP={fp} FN={fn} TN={tn}  precision={prec:.3f} recall={rec:.3f} F1={f1:.3f}")
    print("  (only 1 labelled positive pair exists in all 8 files: these numbers are NOT statistically meaningful)")
    print(f"\n{len(errors)} mismatches:")
    for e in errors:
        print("  -", e)


if __name__ == "__main__":
    main()
