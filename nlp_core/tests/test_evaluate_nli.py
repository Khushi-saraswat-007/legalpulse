"""Tests for the NLI benchmark scripts (metrics with a fake backend, ContractNLI conversion)."""
import importlib.util
import json
import random
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ev = _load("evaluate_nli")
prep = _load("prepare_contractnli")


class FakeBackend:
    """Returns a fixed answer per premise so the metrics have known values."""
    name = "fake"

    def __init__(self, table):
        self.table = table

    def predict(self, pairs):
        return [self.table[(p, h)] for p, h in pairs]


def _p(label):
    base = {"entailment": 0.0, "contradiction": 0.0, "neutral": 0.0}
    base[label] = 1.0
    return base


ROWS = [
    {"premise": "a", "hypothesis": "h", "label": "entailment"},
    {"premise": "b", "hypothesis": "h", "label": "entailment"},
    {"premise": "c", "hypothesis": "h", "label": "contradiction"},
    {"premise": "d", "hypothesis": "h", "label": "contradiction"},
    {"premise": "e", "hypothesis": "h", "label": "neutral"},
    {"premise": "f", "hypothesis": "h", "label": "neutral"},
]
# predictions: a ok, b -> neutral, c ok, d -> entailment, e ok, f -> contradiction
PRED = {"a": "entailment", "b": "neutral", "c": "contradiction", "d": "entailment", "e": "neutral", "f": "contradiction"}


def test_metrics_with_known_predictions():
    backend = FakeBackend({(r["premise"], "h"): _p(PRED[r["premise"]]) for r in ROWS})
    probs = ev.predict_all(backend, ROWS)
    m = ev.metrics([r["label"] for r in ROWS], probs)
    assert m["n"] == 6
    assert abs(m["accuracy"] - 3 / 6) < 1e-9
    assert m["confusion"]["entailment"] == {"entailment": 1, "contradiction": 0, "neutral": 1}
    assert m["confusion"]["contradiction"] == {"entailment": 1, "contradiction": 1, "neutral": 0}
    assert m["per_class"]["contradiction"]["precision"] == 0.5   # c correct, f wrong
    assert m["per_class"]["contradiction"]["recall"] == 0.5      # c found, d missed
    s = {x["threshold"]: x for x in m["contradiction_sweep"]}[0.8]
    assert (s["tp"], s["fp"], s["fn"]) == (1, 1, 1)


def test_hypothesis_only_blanks_the_premise():
    seen = []

    class Spy:
        def predict(self, pairs):
            seen.extend(pairs)
            return [_p("neutral") for _ in pairs]

    ev.predict_all(Spy(), ROWS, hypothesis_only=True)
    assert seen and all(p == "" for p, _ in seen)


def test_unknown_label_is_rejected(tmp_path):
    f = tmp_path / "x.csv"
    f.write_text("premise,hypothesis,label\na,b,maybe\n", encoding="utf-8")
    try:
        ev.read_rows(f)
    except ValueError as e:
        assert "maybe" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_contractnli_conversion_maps_labels_and_spans():
    text = ("Confidential Information shall not be disclosed to any third party without consent. "
            "The Receiving Party may share information with its employees who need to know it. "
            "This Agreement is governed by the laws of the State of New York in all respects.")
    s1 = [0, text.index(" The Receiving")]
    s2 = [text.index("The Receiving"), text.index(" This Agreement")]
    s3 = [text.index("This Agreement"), len(text)]
    data = {
        "labels": {"nda-1": {"hypothesis": "Receiving Party shall not disclose Confidential Information."},
                   "nda-2": {"hypothesis": "Receiving Party may share information with employees."},
                   "nda-3": {"hypothesis": "Agreement has no term."}},
        "documents": [{"id": 7, "text": text, "spans": [s1, s2, s3], "annotation_sets": [{"annotations": {
            "nda-1": {"choice": "Entailment", "spans": [0]},
            "nda-2": {"choice": "Contradiction", "spans": [1]},
            "nda-3": {"choice": "NotMentioned", "spans": []}}}]}],
    }
    rows = prep.build_rows(data, random.Random(1))
    by = {r["label_id"]: r for r in rows}
    assert by["nda-1"]["label"] == "entailment" and "shall not be disclosed" in by["nda-1"]["premise"]
    assert by["nda-2"]["label"] == "contradiction" and "employees" in by["nda-2"]["premise"]
    assert by["nda-3"]["label"] == "neutral" and by["nda-3"]["premise"]


def test_balance_caps_each_class():
    rows = [{"label": l} for l in ["entailment"] * 5 + ["contradiction"] * 3 + ["neutral"] * 9]
    out = prep.balance(rows, 3, random.Random(1))
    assert sorted(r["label"] for r in out).count("neutral") == 3 and len(out) == 9
