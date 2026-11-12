"""CLI:  python -m legalpulse_nlp contract.pdf [--no-nli] [--backend rule|hf] [--out out.json]"""
import argparse
import json
import sys

from . import RuleBasedNLIBackend, extract_detailed
from .errors import NLPCoreError


def main():
    ap = argparse.ArgumentParser(prog="legalpulse_nlp")
    ap.add_argument("file")
    ap.add_argument("--no-nli", action="store_true", help="skip Module 2 (no model needed)")
    ap.add_argument("--backend", choices=["hf", "rule"], default="hf")
    ap.add_argument("--contract-id", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    try:
        res = extract_detailed(a.file, a.contract_id, detect_contradictions=not a.no_nli,
                               nli_backend=RuleBasedNLIBackend() if a.backend == "rule" else None)
    except NLPCoreError as exc:
        sys.exit(f"ERROR: {exc}")
    for w in res.warnings:
        print("warning:", w, file=sys.stderr)
    text = json.dumps(res.contract, indent=2, ensure_ascii=False)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
        print(f"wrote {a.out}: {len(res.contract['clauses'])} clauses, {len(res.contract['contradictions'])} contradiction(s)")
    else:
        print(text)


main()
