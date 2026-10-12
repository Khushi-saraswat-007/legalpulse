"""Glue between the backend and the reasoning engine.

Raw contract text -> clauses (stand-in splitter) -> pipeline.run -> risk report JSON.
Part B's extraction module will later replace `split_clauses`; nothing else here changes.
"""
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]          # repo root
sys.path.insert(0, str(ROOT / "reasoning" / "src"))

from legalpulse_reasoning import pipeline                     # noqa: E402
from legalpulse_reasoning.comparison.embedders import BagOfWordsEmbedder, SBertEmbedder  # noqa: E402
from legalpulse_reasoning.ingest.splitter import split_clauses  # noqa: E402

_embedder = None


def get_embedder():
    """Load the embedder once (SBERT takes a few seconds). Fall back to bag-of-words if SBERT is missing.
    Set LEGALPULSE_EMBEDDER=bow to force the fast baseline (used in tests)."""
    global _embedder
    if _embedder is None:
        if os.environ.get("LEGALPULSE_EMBEDDER", "sbert") == "bow":
            _embedder = BagOfWordsEmbedder()
        else:
            try:
                _embedder = SBertEmbedder()
            except Exception:
                _embedder = BagOfWordsEmbedder()
    return _embedder


def analyze_texts(old_text: str, new_text: str, contract_key: str = "c001") -> dict:
    old = split_clauses(old_text, contract_key, "v1")
    new = split_clauses(new_text, contract_key, "v2")
    if not old["clauses"] or not new["clauses"]:
        raise ValueError("Could not find numbered clauses in one of the files")
    emb = get_embedder()
    report = pipeline.run(old, new, embedder=emb)
    report["meta"] = {"embedder": emb.name, "old_clauses": len(old["clauses"]),
                      "new_clauses": len(new["clauses"])}
    return report