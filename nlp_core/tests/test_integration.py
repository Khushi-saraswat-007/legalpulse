"""Integration: nlp_core output -> reasoning pipeline (Part C). Skipped if reasoning deps are missing."""
import json
import sys
from pathlib import Path

import pytest
from conftest import FIXTURES, ROOT

from legalpulse_nlp import RuleBasedNLIBackend, extract, validate_contract

REPO = ROOT.parent
pytest.importorskip("networkx")


def test_extract_end_to_end_with_contradictions_valid():
    c = extract(FIXTURES / "sample_supply.pdf", "c001", nli_backend=RuleBasedNLIBackend())
    validate_contract(c)
    assert c["contradictions"] == [] or all("clause_a" in r for r in c["contradictions"])


def test_output_feeds_reasoning_graph_builder():
    sys.path.insert(0, str(REPO / "reasoning" / "src"))
    from legalpulse_reasoning.graph.builder import build_graph
    c = extract(FIXTURES / "sample_supply.txt", "c001", detect_contradictions=False)
    g = build_graph(c)
    assert any(d["type"] == "cross_reference" for _, _, d in g.edges(data=True))
