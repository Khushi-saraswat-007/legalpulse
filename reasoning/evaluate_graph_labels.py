"""Score every graph setting against labelled sheets.

Usage (from reasoning/):
  python evaluate_graph_labels.py results/labelling/labelling_sheet_CLAUDE.csv
  python evaluate_graph_labels.py sheetA.csv sheetB.csv        # two reviewers: gold y = both said y, prints kappa
  python evaluate_graph_labels.py my.xlsx results/labelling/labelling_sheet_CLAUDE.csv   # xlsx also works (needs: pip install openpyxl)
Only rows that have a y/n label in EVERY given sheet are used.

Numbers are measured inside the candidate pool (what the sheets contained), not over the whole contract:
  precision = of the clauses a setting flagged, how many are labelled y
  recall    = of all clauses labelled y, how many the setting flagged
  false alarms/change = clauses flagged that are labelled n, averaged over changes
"""
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEY = ROOT / "results" / "labelling" / "labelling_key.csv"


def load(path):
    """Read a labelled sheet: .csv (label (y/n) column) or the friendly .xlsx (item, clause no., ..., label)."""
    if str(path).lower().endswith(".xlsx"):
        import re
        from openpyxl import load_workbook
        ws = load_workbook(path, data_only=True)["Labelling"]
        out = {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            item, clause, label = row[0], row[1], row[5]
            if item and re.fullmatch(r"C\d\d", str(item).strip()) and clause is not None:
                out[(str(item).strip(), str(clause).strip())] = (str(label).strip().lower() if label else "")
        return out
    return {(r["item"], r["candidate_clause"]): r["label (y/n)"].strip().lower()
            for r in csv.DictReader(open(path, encoding="utf-8-sig")) if r["candidate_clause"]}


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in ("y", "n"))
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def live_flags(name, rows, key):
    """Flagged candidates for a setting that the key does not know (e.g. the newer directed-term settings):
    run the real graph + tracer. Needs data/ and the contract + changed_clause columns in labelling_key.csv."""
    sys.path.insert(0, str(ROOT))
    import evaluate_graph_ablation as ab
    from legalpulse_reasoning import config
    st = next((x for x in ab.SETTINGS if x["name"] == name), None)
    if st is None or "contract" not in next(iter(key.values())):
        return None
    saved = (config.WEIGHT_MODE, config.TERM_EDGES, dict(config.EDGE_WEIGHTS))
    cache, out = {}, set()
    try:
        for k in rows:
            kr = key[k]; c = kr["contract"]
            if c not in cache:
                folder = "mock" if c.startswith("p") else "real"
                contract = json.load(open(ROOT / "data" / folder / f"{c}_new.json"))
                cache[c] = (ab.impacted_sets(contract, st), {x["number"]: x["clause_id"] for x in contract["clauses"]})
            imp, by = cache[c]
            if any(kr["candidate_id"] in imp.get(by[n.strip()], ()) for n in kr["changed_clause"].split(",")):
                out.add(k)
    finally:
        config.WEIGHT_MODE, config.TERM_EDGES = saved[0], saved[1]
        config.EDGE_WEIGHTS.clear(); config.EDGE_WEIGHTS.update(saved[2])
    return out


def main(paths):
    sheets = [load(p) for p in paths]
    rows = [k for k in sheets[0] if all(s.get(k) in ("y", "n") for s in sheets)]
    if not rows:
        sys.exit("no rows labelled y/n in all sheets")
    gold = {k: all(s[k] == "y" for s in sheets) for k in rows}
    if len(sheets) == 2:
        a, b = [sheets[0][k] for k in rows], [sheets[1][k] for k in rows]
        agree = sum(x == y for x, y in zip(a, b)) / len(rows)
        print(f"agreement {agree:.0%}, Cohen's kappa {kappa(a, b):.2f}  ({len(rows)} rows)\n")
    key = {(r["item"], r["candidate_clause"]): r for r in csv.DictReader(open(KEY, encoding="utf-8-sig"))}
    names = json.loads((ROOT / "results" / "graph_ablation.json").read_text())["rows"]
    names = [r["setting"] for r in names]
    items = {k[0] for k in rows}
    total_y = sum(gold.values())
    print(f"{len(items)} changes, {len(rows)} candidates, {total_y} labelled y\n")
    print(f"{'setting':<34}{'flagged':>8}{'prec':>7}{'recall':>8}{'F1':>6}{'false alarms/change':>21}")
    out = []
    for s in names:
        known = any(s in r["suggested_by"].split(" | ") for r in key.values())
        flagged = [k for k in rows if s in key[k]["suggested_by"].split(" | ")] if known else None
        if flagged is None:                      # setting added after the labelling pool was built -> compute it live
            live = live_flags(s, rows, key)
            flagged = sorted(live) if live is not None else []
        tp = sum(gold[k] for k in flagged); fp = len(flagged) - tp
        p = tp / len(flagged) if flagged else 0.0; r = tp / total_y if total_y else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        out.append((s, len(flagged), p, r, f1, fp / len(items)))
    for s, n, p, r, f1, fa in sorted(out, key=lambda x: -x[4]):
        print(f"{s:<34}{n:>8}{p:>7.2f}{r:>8.2f}{f1:>6.2f}{fa:>21.2f}")
    print("\npool caveat: candidates were sampled from the union of all settings (+3 random clauses per change).")


if __name__ == "__main__":
    main(sys.argv[1:] or [str(ROOT / "results" / "labelling" / "labelling_sheet_CLAUDE.csv")])
