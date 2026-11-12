import sys
import json
import pathlib

sys.path.insert(0, "reasoning/src")
from legalpulse_reasoning.ingest.splitter import split_clauses
from legalpulse_reasoning.ingest.editor import make_edited_pair

# r1-r8 = DEV (isse tum fix/tune karogi), r9-r16 = HELD-OUT (final number sirf yahan se)
DEV_DIR = pathlib.Path("reasoning/data/real")
HELD_DIR = pathlib.Path("reasoning/data/real_heldout")
DEV_DIR.mkdir(parents=True, exist_ok=True)
HELD_DIR.mkdir(parents=True, exist_ok=True)

files = sorted(pathlib.Path("data/raw").glob("r*.txt"), key=lambda p: int(p.name.split("_")[0][1:]))
for f in files:
    pid = f.name.split("_")[0]
    number = int(pid[1:])
    out_dir, seed = (DEV_DIR, 7) if number <= 8 else (HELD_DIR, 11)

    old = split_clauses(f.read_text(encoding="utf-8"), pid, "v1")
    if len(old["clauses"]) < 8:
        print(pid, "skip: sirf", len(old["clauses"]), "clauses")
        continue

    new, truth = make_edited_pair(old, seed=seed)
    (out_dir / f"{pid}_old.json").write_text(json.dumps(old, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / f"{pid}_new.json").write_text(json.dumps(new, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / f"{pid}_truth.json").write_text(json.dumps(truth, indent=2, ensure_ascii=False), encoding="utf-8")

    kinds = {}
    for c in truth["changes"]:
        kinds[c["change_type"]] = kinds.get(c["change_type"], 0) + 1
    print(pid, len(old["clauses"]), "->", len(new["clauses"]), kinds)