"""Convert a ContractNLI split (train/dev/test .json) into a flat CSV: premise,hypothesis,label.

ContractNLI (Koreeda and Manning, 2021) labels each (document, hypothesis) as Entailment, Contradiction
or NotMentioned and marks the evidence spans. For a pairwise NLI model we build:
  Entailment / Contradiction -> premise = the annotated evidence span(s) of the document
  NotMentioned               -> premise = a random span of the same document  (label: neutral)
The neutral premises are random spans, NOT human-checked neutral pairs: report this in the README.

Usage:  python prepare_contractnli.py dev.json --out dev.csv --per-class 200 --seed 13
"""
import argparse
import csv
import json
import random
import sys
from pathlib import Path

MAP = {"entailment": "entailment", "contradiction": "contradiction", "notmentioned": "neutral"}
MAX_PREMISE_CHARS = 1200


def _clean(s):
    return " ".join(s.split())


def build_rows(data, rng):
    missing = [k for k in ("documents", "labels") if k not in data]
    if missing:
        sys.exit(f"Unexpected ContractNLI format: missing {missing}. Top-level keys found: {sorted(data)}")
    hyps = {lid: v["hypothesis"] for lid, v in data["labels"].items()}
    rows = []
    for doc in data["documents"]:
        text, spans = doc["text"], doc["spans"]
        usable = [(a, b) for a, b in spans if 60 <= b - a <= MAX_PREMISE_CHARS]
        for aset in doc.get("annotation_sets", []):
            for lid, ann in aset["annotations"].items():
                label = MAP.get(str(ann.get("choice", "")).lower())
                if label is None or lid not in hyps:
                    continue
                if label == "neutral":
                    if not usable:
                        continue
                    a, b = rng.choice(usable)
                    premise = text[a:b]
                else:
                    idx = ann.get("spans") or []
                    premise = " ".join(text[spans[i][0]:spans[i][1]] for i in idx)
                premise = _clean(premise)[:MAX_PREMISE_CHARS]
                if not premise:
                    continue
                rows.append({"premise": premise, "hypothesis": hyps[lid], "label": label,
                             "doc_id": doc.get("id", ""), "label_id": lid})
    return rows


def balance(rows, per_class, rng):
    out = []
    for lab in ("entailment", "contradiction", "neutral"):
        group = [r for r in rows if r["label"] == lab]
        rng.shuffle(group)
        out.extend(group[:per_class] if per_class else group)
    rng.shuffle(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("split_json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--per-class", type=int, default=200, help="max rows per class (0 = all)")
    ap.add_argument("--seed", type=int, default=13)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    data = json.loads(Path(a.split_json).read_text(encoding="utf-8"))
    rows = balance(build_rows(data, rng), a.per_class, rng)
    with open(a.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, ["premise", "hypothesis", "label", "doc_id", "label_id"])
        w.writeheader()
        w.writerows(rows)
    counts = {l: sum(r["label"] == l for r in rows) for l in ("entailment", "contradiction", "neutral")}
    print(f"wrote {len(rows)} rows to {a.out}: {counts}")


if __name__ == "__main__":
    main()
