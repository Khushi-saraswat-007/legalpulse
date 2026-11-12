"""Module 1 entry point: file/text -> contract JSON (schemas/contract.schema.json)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import metadata
from .errors import SchemaValidationError
from .ingest import clean_text, read_text
from .segmenter import segment


@dataclass
class ExtractionResult:
    contract: dict
    warnings: list[str] = field(default_factory=list)
    preamble: str = ""


def _find_schema(name: str) -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "schemas" / name
        if cand.exists():
            return cand
    return None


def validate_contract(contract: dict, schema_path: str | Path | None = None) -> None:
    """Raise SchemaValidationError if `contract` breaks the shared schema."""
    import jsonschema

    path = Path(schema_path) if schema_path else _find_schema("contract.schema.json")
    if path is None:
        raise SchemaValidationError("contract.schema.json not found; pass schema_path explicitly")
    schema = json.loads(path.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(contract, schema)
    except jsonschema.ValidationError as exc:
        where = "/".join(str(p) for p in exc.absolute_path)
        raise SchemaValidationError(f"Invalid contract JSON at '{where}': {exc.message}") from exc


def extract_from_text(text: str, contract_id: str = "c001", version: str = "v1") -> ExtractionResult:
    text = clean_text(text)
    seg = segment(text)
    warnings = list(seg.warnings)

    full = text
    doc_roles = metadata.detect_document_roles(full)
    doc_terms = metadata.detect_defined_terms(full, doc_roles)

    # stable, unique ids: "<contract_id>_<number>"; duplicates get a suffix
    number_to_id: dict[str, str] = {}
    ids: list[str] = []
    for c in seg.clauses:
        cid = f"{contract_id}_{c.number}"
        n = 2
        while cid in ids:
            cid = f"{contract_id}_{c.number}_dup{n}"
            n += 1
        ids.append(cid)
        number_to_id.setdefault(c.number, cid)   # references point at the first clause with that number

    clauses = []
    for c, cid in zip(seg.clauses, ids):
        refs, unresolved = metadata.extract_references(f"{c.heading}. {c.text}" if c.heading else c.text,
                                                       c.number, number_to_id)
        if unresolved:
            warnings.append(f"Clause {c.number}: reference(s) to unknown clause number(s) {unresolved}")
        clauses.append({
            "clause_id": cid,
            "number": c.number,
            "heading": c.heading,
            "text": c.text,
            "parties": metadata.extract_parties(c.text, doc_roles),
            "obligation_type": metadata.classify_obligation(c.heading, c.text),
            "deadline": metadata.extract_deadline(c.text),
            "defined_terms": metadata.terms_in_clause(c.text, doc_terms),
            "references": refs,
        })
    contract = {"contract_id": contract_id, "version": version, "clauses": clauses, "contradictions": []}
    return ExtractionResult(contract, warnings, seg.preamble)


def extract_detailed(path: str | Path, contract_id: str | None = None, version: str = "v1",
                     detect_contradictions: bool = True, nli_backend=None,
                     validate: bool = True) -> ExtractionResult:
    path = Path(path)
    cid = contract_id or re.sub(r"[^A-Za-z0-9]+", "", path.stem.lower())[:20] or "c001"
    result = extract_from_text(read_text(path), cid, version)
    if detect_contradictions:
        from .contradiction import detect_contradictions as _detect
        result.contract["contradictions"] = _detect(result.contract["clauses"], backend=nli_backend)
    if validate:
        validate_contract(result.contract)
    return result


def extract(path: str | Path, contract_id: str | None = None, version: str = "v1",
            detect_contradictions: bool = True, nli_backend=None) -> dict:
    """PUBLIC ENTRY POINT used by the backend: raw PDF/DOCX/TXT -> schema-valid contract dict.

    detect_contradictions=False skips Module 2 (no model needed, fast).
    """
    return extract_detailed(path, contract_id, version, detect_contradictions, nli_backend).contract
