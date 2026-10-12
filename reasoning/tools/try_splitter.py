import sys
import pathlib

sys.path.insert(0, "reasoning/src")
from legalpulse_reasoning.ingest.splitter import split_clauses

# use: python reasoning/tools/try_splitter.py r1_
prefix = sys.argv[1]
files = sorted(pathlib.Path("data/raw").glob(prefix + "*.txt"))
text = files[0].read_text(encoding="utf-8")
contract = split_clauses(text, prefix.rstrip("_"))
clauses = contract["clauses"]

print("File:", files[0].name)
print("Total clauses:", len(clauses))
print()
for c in clauses[:12]:
    print(c["number"], "|", len(c["text"]), "chars |", c["text"][:80])
print()
short = [c for c in clauses if len(c["text"]) < 40]
print("Bahut chhoti clauses (40 chars se kam):", len(short))
for c in short[:8]:
    print("  ", c["number"], "|", c["text"])