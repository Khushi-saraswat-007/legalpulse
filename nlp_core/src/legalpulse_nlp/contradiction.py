"""Module 2: contradiction detection between clauses of ONE contract version.

Pipeline:  clauses -> candidate pairs -> exception filter -> NLI (both directions) -> records

Why each step exists
  * candidate pairs : n clauses = n(n-1)/2 pairs; NLI is slow, so we only test pairs that plausibly
                      talk about the same thing (shared obligation type / defined term / reference /
                      similar wording). Keyword overlap alone is NEVER treated as a contradiction.
  * exception filter: "Notwithstanding Clause 9, ..." is a deliberate override, not an accident.
  * both directions : NLI models can be order sensitive; we score (A,B) and (B,A) and average.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from itertools import combinations

from . import config, metadata
from .nli import NLIBackend, HFNLIBackend

_TOKEN = re.compile(r"[a-z0-9]+")
_EXC = re.compile("|".join(config.EXCEPTION_MARKERS), re.I)


# ------------------------------------------------------------------ candidate pairs
def _tfidf_vectors(clauses: list[dict]) -> list[dict[str, float]]:
    docs = [Counter(_TOKEN.findall(c["text"].lower())) for c in clauses]
    df: Counter = Counter()
    for d in docs:
        df.update(d.keys())
    n = len(docs)
    vecs = []
    for d in docs:
        v = {t: (1 + math.log(tf)) * math.log((1 + n) / (1 + df[t])) for t, tf in d.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({t: x / norm for t, x in v.items()})
    return vecs


def _cos(a: dict[str, float], b: dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(t, 0.0) for t, x in a.items())

#def candidate_pair's helper function
def _heading_only(c: dict) -> bool:
    """Parent clause like '4. Termination' whose text is just its heading."""
    h = (c.get("heading") or "").strip()
    return bool(h) and (c.get("text") or "").strip() == h


def candidate_pairs(clauses: list[dict]) -> list[tuple[int, int, float]]:
    """Indices (i, j, priority) of clause pairs worth sending to the NLI model."""
    vecs = _tfidf_vectors(clauses)
    id_to_idx = {c["clause_id"]: i for i, c in enumerate(clauses)}
    out = []
    for i, j in combinations(range(len(clauses)), 2):
        a, b = clauses[i], clauses[j]
        if _heading_only(a) or _heading_only(b):
            continue
        if a.get("obligation_type") in config.SKIP_TYPES_FOR_PAIRS or b.get("obligation_type") in config.SKIP_TYPES_FOR_PAIRS:
            continue
        sim = _cos(vecs[i], vecs[j])
        linked = (b["clause_id"] in a.get("references", []) or a["clause_id"] in b.get("references", []))
        same_type = a.get("obligation_type") == b.get("obligation_type") and a.get("obligation_type") != "general"
        shared_term = bool(set(a.get("defined_terms", [])) & set(b.get("defined_terms", [])))
        if linked or same_type or shared_term or sim >= config.MIN_TEXT_SIMILARITY:
            priority = sim + (1.0 if linked else 0) + (0.5 if same_type else 0) + (0.3 if shared_term else 0)
            out.append((i, j, priority))
    out.sort(key=lambda t: -t[2])
    return out[:config.MAX_CANDIDATE_PAIRS]


# ------------------------------------------------------------------ exception handling
# Words allowed between an exception marker and the clause it points at, e.g.
# "Notwithstanding ANYTHING IN Clause 9", "subject to THE PROVISIONS OF Clause 9".
_MARKER_FILLER = {"anything", "in", "of", "the", "provisions", "provision", "to", "contrary", "contained",
                  "herein", "this", "agreement", "contract", "under", "set", "out", "stated", "specified",
                  "provided", "as", "terms", "conditions", "and"}
_WORD = re.compile(r"\s*([A-Za-z]+)\b")
_TARGET_TOKEN = re.compile(r"\d+(?:\.\d+)*(\([a-z]\))?")   # group 1 = optional "(b)" sub-clause suffix


def _marker_targets(text: str) -> dict[str, str]:
    """{clause number: marker} for every exception marker whose target clause is identifiable.

    A marker is bound to a clause only if, right after the marker, there are nothing but filler
    words (no comma / semicolon / other words) followed by "Clause(s) N [and M ...]".
    Anything else -> the target is unknown -> nothing is bound (the pair then goes to NLI).
    """
    targets: dict[str, str] = {}
    for m in _EXC.finditer(text):
        pos = m.end()
        while True:
            w = _WORD.match(text, pos)
            if not w or w.group(1).lower() not in _MARKER_FILLER:
                break
            pos = w.end()
        while pos < len(text) and text[pos].isspace():
            pos += 1
        ref = metadata._REF.match(text, pos)
        if ref:
            for tok in _TARGET_TOKEN.finditer(ref.group("body")):
                if tok.group(1) is None:      # "9(b)" is a sub-clause, not clause 9: never bind it
                    targets.setdefault(tok.group(0), m.group(0).lower())
    return targets


def is_explicit_carveout(a: dict, b: dict) -> str | None:
    """If one clause uses an exception marker that points at the other clause (exact clause
    number), return a description; otherwise None."""
    for x, y in ((a, b), (b, a)):
        marker = _marker_targets(x["text"]).get(y["number"])
        if marker and y["clause_id"] in x.get("references", []):
            return (f"Clause {x['number']} deliberately qualifies Clause {y['number']} "
                    f"('{marker}'), so this is treated as an override, not an accidental conflict.")
    return None


# ------------------------------------------------------------------ explanation
def _hints(a: dict, b: dict) -> str:
    hints = []
    na, nb = set(re.findall(r"\b\d+\b", a["text"])), set(re.findall(r"\b\d+\b", b["text"]))
    if na and nb and na != nb:
        hints.append(f"different figures ({', '.join(sorted(na))} vs {', '.join(sorted(nb))})")
    neg = re.compile(r"\b(not|no|never|without|cannot)\b", re.I)
    if bool(neg.search(a["text"])) != bool(neg.search(b["text"])):
        hints.append("one clause is negated and the other is not")
    return "; ".join(hints)


def _explain(a: dict, b: dict, p: dict, fwd: dict, rev: dict, model: str) -> str:
    base = (f"Clause {a['number']} and Clause {b['number']} may conflict "
            f"(P(contradiction)={p['contradiction']:.2f}; forward {fwd['contradiction']:.2f}, reverse {rev['contradiction']:.2f}; model: {model}).")
    h = _hints(a, b)
    return f"{base} Signals: {h}." if h else base


# ------------------------------------------------------------------ main entry
def classify(p: dict) -> str:
    if p["contradiction"] >= config.CONTRADICTION_THRESHOLD:
        return "contradiction"
    if p["entailment"] >= config.ENTAILMENT_THRESHOLD:
        return "entailment"
    return "neutral"


def detect_contradictions(clauses: list[dict], backend: NLIBackend | None = None,
                          emit_labels: tuple[str, ...] | None = None) -> list[dict]:
    """Return records for contract["contradictions"]. `backend` defaults to the HF model in config."""
    emit = emit_labels or config.EMIT_LABELS
    if len(clauses) < 2:
        return []
    backend = backend or HFNLIBackend()
    pairs = candidate_pairs(clauses)

    records, to_score = [], []
    for i, j, _ in pairs:
        a, b = clauses[i], clauses[j]
        note = is_explicit_carveout(a, b)
        if note:
            if "neutral" in emit:
                records.append({"clause_a": a["clause_id"], "clause_b": b["clause_id"], "label": "neutral",
                                "score": 0.0, "explanation": note})
            continue
        to_score.append((a, b))

    # one batched call for forward pairs and one for reverse pairs (model is loaded once)
    fwd = backend.predict([(a["text"], b["text"]) for a, b in to_score])
    rev = backend.predict([(b["text"], a["text"]) for a, b in to_score])
    for (a, b), f, r in zip(to_score, fwd, rev):
        mean = {k: (f[k] + r[k]) / 2 for k in f}
        label = classify(mean)
        if label not in emit:
            continue
        score = mean[label]
        rec = {"clause_a": a["clause_id"], "clause_b": b["clause_id"], "label": label, "score": round(score, 4)}
        if label == "contradiction":
            rec["explanation"] = _explain(a, b, mean, f, r, getattr(backend, "name", "nli"))
        records.append(rec)
    records.sort(key=lambda x: -x["score"])
    return records