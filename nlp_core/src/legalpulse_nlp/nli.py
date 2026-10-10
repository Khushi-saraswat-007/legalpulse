"""NLI backends. A backend is any object with:

    predict(pairs: list[tuple[str, str]]) -> list[dict]   # each dict: {"entailment": p, "contradiction": p, "neutral": p}

so the model can be swapped (DeBERTa, RoBERTa-MNLI, a Legal-BERT you fine-tune later) without
touching the rest of the code.
"""
from __future__ import annotations

import re
from typing import Protocol

from . import config
from .errors import NLIModelError

LABELS = ("entailment", "contradiction", "neutral")


class NLIBackend(Protocol):
    name: str

    def predict(self, pairs: list[tuple[str, str]]) -> list[dict[str, float]]: ...


class HFNLIBackend:
    """HuggingFace sequence-classification NLI model (premise, hypothesis) -> 3 probabilities.

    The model is loaded ONCE (lazily, on first predict) and reused for every pair.
    Label order differs between models, so we read it from model.config.id2label.
    """

    _cache: dict[str, tuple] = {}

    def __init__(self, model_name: str = config.NLI_MODEL_NAME, device: str | None = None):
        self.name = model_name
        self.device = device
        self._tok = None
        self._model = None
        self._label_idx: dict[str, int] = {}

    def _load(self):
        if self._model is not None:
            return
        if self.name in HFNLIBackend._cache:
            self._tok, self._model, self._label_idx = HFNLIBackend._cache[self.name]
            return
        try:
            import torch  # noqa: F401
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            tok = AutoTokenizer.from_pretrained(self.name)
            model = AutoModelForSequenceClassification.from_pretrained(self.name)
            model.eval()
        except Exception as exc:
            raise NLIModelError(
                f"Could not load NLI model '{self.name}': {exc}. "
                "Install torch + transformers and make sure the model can be downloaded "
                "(or pass nli_backend=RuleBasedNLIBackend() for the offline baseline).") from exc
        idx = {}
        for i, lab in model.config.id2label.items():
            low = str(lab).lower()
            for L in LABELS:
                if low.startswith(L[:5]):          # "entail", "contra", "neutra"
                    idx[L] = int(i)
        if set(idx) != set(LABELS):
            raise NLIModelError(f"Model '{self.name}' labels {model.config.id2label} are not entailment/contradiction/neutral")
        self._tok, self._model, self._label_idx = tok, model, idx
        HFNLIBackend._cache[self.name] = (tok, model, idx)

    def predict(self, pairs):
        if not pairs:
            return []
        self._load()
        import torch

        out = []
        bs = config.NLI_BATCH_SIZE
        for i in range(0, len(pairs), bs):
            chunk = pairs[i:i + bs]
            enc = self._tok([p for p, _ in chunk], [h for _, h in chunk], truncation=True,
                            max_length=config.NLI_MAX_LENGTH, padding=True, return_tensors="pt")
            with torch.no_grad():
                probs = torch.softmax(self._model(**enc).logits, dim=-1).tolist()
            for row in probs:
                out.append({L: row[self._label_idx[L]] for L in LABELS})
        return out


# ---------------------------------------------------------------------------------------------
# Rule-based baseline: NO deep learning. Used (a) offline, (b) as the "no-DL baseline" row in the
# evaluation, (c) in unit tests. It only looks for a few classic conflict signals between two
# clauses that talk about the same thing, so it is intentionally crude.
# ---------------------------------------------------------------------------------------------
_STOP = set("the a an of to in on or and is are be shall may will any this that with for by as at from it its such".split())
_NEG = re.compile(r"\b(not|no|never|neither|nor|without|cannot|unable)\b", re.I)
_NUM = re.compile(r"\b\d+(?:\.\d+)?\b")
_ANYTIME = re.compile(r"\bat any time\b|\bwithout (?:any )?(?:prior )?notice\b", re.I)
_FIRST_N = re.compile(r"\b(?:during|within) the first \d+", re.I)


_GENERIC = set("tenant landlord buyer seller supplier licensor licensee provider client party parties agreement lease "
               "contract termination shall may must will written notice premises".split())
_NUM_UNIT = re.compile(r"\b(\d+(?:,\d+)*)\s+(hour|day|week|month|year|rupee|dollar)s?\b", re.I)


def _content(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", s.lower()) if w not in _STOP and len(w) > 2}


def _specific(s: str) -> set[str]:
    return _content(s) - _GENERIC


def _units(s: str) -> dict[str, set[str]]:
    d: dict[str, set[str]] = {}
    for n, u in _NUM_UNIT.findall(s):
        d.setdefault(u.lower(), set()).add(n)
    return d


class RuleBasedNLIBackend:
    """Crude no-ML baseline. Fires only if the clauses share >= 2 topic words (parties / filler excluded)."""
    name = "rule-based-baseline"
    MIN_SHARED = 2

    def predict(self, pairs):
        out = []
        for a, b in pairs:
            shared = _specific(a) & _specific(b)
            ca, cb = _content(a), _content(b)
            overlap = len(ca & cb) / max(1, min(len(ca), len(cb)))
            signal = 0.0
            if len(shared) >= self.MIN_SHARED:
                if bool(_NEG.search(a)) != bool(_NEG.search(b)):
                    signal = max(signal, 0.85)                  # one forbids, the other does not
                ua, ub = _units(a), _units(b)
                if any(ua[u] and ub[u] and not (ua[u] & ub[u]) for u in set(ua) & set(ub)):
                    signal = max(signal, 0.82)                  # same topic, same unit, different figure
            if shared and ((_ANYTIME.search(a) and _FIRST_N.search(b)) or (_ANYTIME.search(b) and _FIRST_N.search(a))):
                signal = max(signal, 0.9)                       # "any time / no notice" vs "not in first N months"
            if signal:
                out.append({"entailment": 0.0, "contradiction": signal, "neutral": 1 - signal})
            elif overlap >= 0.8:
                out.append({"entailment": 0.8, "contradiction": 0.0, "neutral": 0.2})
            else:
                out.append({"entailment": 0.0, "contradiction": 0.0, "neutral": 1.0})
        return out
