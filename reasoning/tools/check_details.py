import sys
import pathlib

sys.path.insert(0, "reasoning/src")
from legalpulse_reasoning.ingest.splitter import split_clauses

files = sorted(pathlib.Path("data/raw").glob("r*.txt"), key=lambda p: int(p.name.split("_")[0][1:]))
print("contract | clauses | parties | defined terms | clauses with refs | with deadline")
for f in files:
    c = split_clauses(f.read_text(encoding="utf-8"), "x")
    cl = c["clauses"]
    print(f.name.split("_")[0], "|", len(cl), "|", c["meta"]["parties_detected"], "|",
          c["meta"]["defined_terms_found"], "|", sum(1 for x in cl if x["references"]), "|",
          sum(1 for x in cl if x["deadline"]))