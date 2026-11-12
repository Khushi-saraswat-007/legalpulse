import sys
import pathlib

sys.path.insert(0, "reasoning/src")
from legalpulse_reasoning.ingest.splitter import split_clauses

files = sorted(pathlib.Path("data/raw").glob("r*.txt"), key=lambda p: int(p.name.split("_")[0][1:]))
print("contract | clauses | headings | sabse lambi | <40 chars")
for f in files:
    clauses = split_clauses(f.read_text(encoding="utf-8"), "x")["clauses"]
    if not clauses:
        print(f.name.split("_")[0], "| 0 clauses  <-- PROBLEM")
        continue
    lengths = [len(c["text"]) for c in clauses]
    print(f.name.split("_")[0], "|", len(clauses), "|", sum(1 for c in clauses if c["heading"]),
          "|", max(lengths), "|", sum(1 for n in lengths if n < 40))