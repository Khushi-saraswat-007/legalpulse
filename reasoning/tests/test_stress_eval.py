"""The stress benchmark runs end to end on two real contracts and the structure pass helps on the rewrite curve."""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "src"))
import evaluate_alignment_stress as st
from legalpulse_reasoning.comparison.embedders import BagOfWordsEmbedder


def test_stress_benchmark_smoke():
    res = st.run(BagOfWordsEmbedder(), contracts=st.load_contracts()[:3])
    base, new = res["similarity_only"], res["with_structure_pass"]
    assert set(base) == set(new) and st.UNRELATED in base
    heavy = "70% of the words replaced"
    assert new[heavy]["correct"] >= base[heavy]["correct"]
    assert new[st.UNRELATED]["correct"] >= new[st.UNRELATED]["total"] - 1       # (almost) no false matches


def test_embedder_separation_smoke():
    import evaluate_embedder_separation as sep
    res = sep.run(BagOfWordsEmbedder(), contracts=st.load_contracts()[:3])
    assert 0.5 < res["30% of the words replaced"]["auc"] <= 1.0
    assert res["30% of the words replaced"]["auc"] >= res["85% of the words replaced"]["auc"]
    assert sep.auc([1, 2], [0, 0]) == 1.0 and sep.auc([1], [1]) == 0.5
