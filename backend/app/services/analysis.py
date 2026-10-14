"""Glue between the backend, nlp_core (Part B) and the reasoning engine (Part C).

raw file (.txt / .pdf / .docx)
    -> nlp_core: read text, split into clauses, extract metadata, detect contradictions
    -> reasoning.pipeline.run(old, new) -> risk report JSON

Environment switches (both optional):
    LEGALPULSE_EMBEDDER = bow | sbert (default sbert, falls back to bow)
    LEGALPULSE_NLI      = rule | hf   (default hf,    falls back to rule)
"""
import logging
import os
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[3]          # repo root
sys.path.insert(0, str(ROOT / "reasoning" / "src"))
sys.path.insert(0, str(ROOT / "nlp_core" / "src"))

from legalpulse_reasoning import pipeline                     # noqa: E402
from legalpulse_reasoning.comparison.embedders import BagOfWordsEmbedder, SBertEmbedder  # noqa: E402
from legalpulse_nlp.contradiction import detect_contradictions  # noqa: E402
from legalpulse_nlp.errors import NLPCoreError                # noqa: E402
from legalpulse_nlp.extractor import extract_from_text, validate_contract  # noqa: E402
from legalpulse_nlp.ingest import read_text                   # noqa: E402
from legalpulse_nlp.nli import HFNLIBackend, RuleBasedNLIBackend  # noqa: E402

log = logging.getLogger("legalpulse.analysis")
SUPPORTED_EXTENSIONS = (".txt", ".pdf", ".docx")

_embedder = None
_nli = None


def get_embedder():
    """Load the embedder once (SBERT takes a few seconds). Fall back to bag-of-words if SBERT is missing."""
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


class _SafeNLI:
    """Real NLI model if it loads; otherwise the rule-based baseline (decided on first use)."""

    def __init__(self):
        self._rule = RuleBasedNLIBackend()
        self._hf = None if os.environ.get("LEGALPULSE_NLI", "hf") == "rule" else HFNLIBackend()
        self.name = self._rule.name if self._hf is None else self._hf.name

    def predict(self, pairs):
        if self._hf is not None:
            try:
                return self._hf.predict(pairs)
            except Exception as e:  # torch/transformers missing, no internet for the download, ...
                log.warning("NLI model unavailable (%s); using the rule-based baseline", e)
                self._hf = None
                self.name = self._rule.name
        return self._rule.predict(pairs)


def get_nli():
    global _nli
    if _nli is None:
        _nli = _SafeNLI()
    return _nli


def warm_up():
    """Load the embedder and the NLI model once, at server start, so the first request is not slow.
    Models are cached in module globals / HFNLIBackend._cache and reused by every later request."""
    get_embedder()
    get_nli().predict([("Payment is due in 30 days.", "Payment is due in 90 days.")])


def _contract_from_text(text: str, contract_key: str, version: str, find_contradictions: bool = True):
    """Text -> schema-valid contract dict (clauses + contradictions) using nlp_core.

    The risk engine only reads contradictions of the NEW version, so the slow NLI step is skipped
    for the old one (this halves the analysis time on a CPU)."""
    result = extract_from_text(text, f"{contract_key}{version}", version)
    contract = result.contract
    if not contract["clauses"]:
        raise ValueError("Could not find numbered clauses in one of the files")
    contract["contradictions"] = (detect_contradictions(contract["clauses"], backend=get_nli())
                                  if find_contradictions else [])
    validate_contract(contract)
    return contract, result.warnings


def analyze_texts(old_text: str, new_text: str, contract_key: str = "c001") -> dict:
    """Old and new contract text -> risk report."""
    try:
        old, old_warn = _contract_from_text(old_text, contract_key, "v1", find_contradictions=False)
        new, new_warn = _contract_from_text(new_text, contract_key, "v2")
    except NLPCoreError as e:
        raise ValueError(str(e)) from e
    emb = get_embedder()
    report = pipeline.run(old, new, embedder=emb)
    report["meta"] = {"embedder": emb.name, "nli": get_nli().name,
                      "old_clauses": len(old["clauses"]), "new_clauses": len(new["clauses"]),
                      "contradictions": len(new["contradictions"]),
                      # NLI accuracy is not yet measured on real labelled data: never present it as final
                      "contradictions_status": "experimental",
                      "warnings": old_warn + new_warn}
    return report


def read_document(filename: str, data: bytes) -> str:
    """Bytes of an uploaded .txt / .pdf / .docx -> clean text (via nlp_core's own readers)."""
    suffix = pathlib.Path(filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"{filename}: only {', '.join(SUPPORTED_EXTENSIONS)} files are supported")
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / f"upload{suffix}"
        path.write_bytes(data)
        try:
            return read_text(path)
        except NLPCoreError as e:
            raise ValueError(f"{filename}: {e}") from e


def analyze_files(old_name: str, old_data: bytes, new_name: str, new_data: bytes,
                  contract_key: str = "c001") -> dict:
    """Same as analyze_texts but starting from uploaded files of any supported type."""
    return analyze_texts(read_document(old_name, old_data), read_document(new_name, new_data),
                         contract_key)
