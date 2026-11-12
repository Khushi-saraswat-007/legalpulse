"""Threshold-free comparison of embedders for version comparison.

The stress benchmark depends on fixed similarity thresholds, which were tuned for BoW/SBERT. An embedder with a
different similarity scale (mean-pooled BERT scores almost every pair 0.8-0.95) is then judged unfairly. This
script removes the threshold: for each clause it asks "is the rewritten version of this clause more similar to
it than a DIFFERENT clause of the same contract is?" and reports the AUC (1.0 = always, 0.5 = coin flip).

  positive pair  (clause, the same clause with p% of its words replaced)   p = 30 / 50 / 70 / 85 %
  negative pair  (clause, another clause of the same contract)

Also reports the mean similarity of both kinds of pair, i.e. how much room there is between them.

Usage (repo root):  python reasoning/evaluate_embedder_separation.py --embedder bow|sbert|legalbert
Writes reasoning/results/embedder_separation_<embedder>.json
"""
import argparse, glob, json, pathlib, random, re, sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from legalpulse_reasoning.comparison.embedders import make_embedder

LEVELS = (0.3, 0.5, 0.7, 0.85)

# Meaning-preserving legal synonyms (longest phrases first). Used by --edit paraphrase: the wording changes, the meaning does not.
SYNONYMS = [("in the event that", "if"), ("prior to", "before"), ("subsequent to", "after"), ("pursuant to", "under"),
            ("in accordance with", "following"), ("with respect to", "regarding"), ("on or before", "no later than"),
            ("shall", "must"), ("terminate", "end"), ("terminated", "ended"), ("termination", "ending"), ("notify", "inform"),
            ("notice", "notification"), ("commence", "begin"), ("commencement", "start"), ("purchase", "buy"), ("obtain", "get"),
            ("provide", "supply"), ("provided", "supplied"), ("payment", "remittance"), ("approximately", "about"),
            ("agreement", "contract"), ("obligations", "duties"), ("obligation", "duty"), ("liable", "responsible"),
            ("liability", "responsibility"), ("damages", "losses"), ("breach", "violation"), ("assign", "transfer"),
            ("consent", "approval"), ("additional", "further"), ("required", "needed"), ("require", "need"),
            ("sufficient", "enough"), ("confidential", "private"), ("disclose", "reveal"), ("indemnify", "compensate"),
            ("purchaser", "buyer"), ("therein", "in it"), ("hereunder", "under this agreement"), ("hereby", "")]
_SYN = [(re.compile(r"\b" + re.escape(a) + r"\b", re.I), b) for a, b in SYNONYMS]


def paraphrase(text: str) -> str:
    for rx, b in _SYN:
        text = rx.sub(b, text)
    return re.sub(r"\s+", " ", text).strip()


def auc(pos, neg):
    """P(pos > neg) over all pairs (Mann-Whitney); ties count 1/2."""
    pos, neg = np.asarray(pos), np.asarray(neg)
    greater = (pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum()
    return float(greater / (len(pos) * len(neg)))


def run(embedder, seed=7, picks=6, negatives=6, contracts=None, edit="random"):
    files = sorted(glob.glob(str(ROOT / "data" / "real" / "*_old.json"))) + sorted(glob.glob(str(ROOT / "data" / "real_heldout" / "*_old.json")))
    contracts = contracts or [json.load(open(f, encoding="utf-8")) for f in files]
    out = {}
    for p in (LEVELS if edit == "random" else (None,)):
        rnd = random.Random(seed); pos, neg = [], []
        for old in contracts:
            texts = [c["text"] for c in old["clauses"]]
            idxs = [i for i, t in enumerate(texts) if len(t) > 250]
            if len(idxs) < 4: continue
            pool = [w for t in texts for w in t.split()]
            chosen = rnd.sample(idxs, min(picks, len(idxs)))
            rewrites = ([" ".join(rnd.choice(pool) if rnd.random() < p else w for w in texts[i].split()) for i in chosen]
                        if edit == "random" else [paraphrase(texts[i]) for i in chosen])
            V = embedder.encode(texts + rewrites)            # one call per contract: same batch for every pair
            for k, i in enumerate(chosen):
                pos.append(float(V[i] @ V[len(texts) + k]))
                others = [j for j in idxs if j != i]
                for j in rnd.sample(others, min(negatives, len(others))):
                    neg.append(float(V[i] @ V[j]))
        out["legal synonyms swapped (same meaning)" if p is None else f"{int(p * 100)}% of the words replaced"] = {"auc": round(auc(pos, neg), 3), "mean_similarity_same_clause": round(float(np.mean(pos)), 3),
                                                         "mean_similarity_different_clause": round(float(np.mean(neg)), 3), "pairs": [len(pos), len(neg)]}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--embedder", choices=["bow", "sbert", "legalbert"], default="bow")
    ap.add_argument("--edit", choices=["random", "paraphrase"], default="random",
                    help="random: replace words by random ones (lexical stress); paraphrase: swap legal synonyms (same meaning)")
    a = ap.parse_args()
    emb = make_embedder(a.embedder)
    res = run(emb, edit=a.edit)
    print(f"\nEmbedder: {emb.name}\n{'edit':32} {'AUC':>6} {'same clause':>12} {'other clause':>13}")
    for k, v in res.items():
        print(f"{k:32} {v['auc']:>6} {v['mean_similarity_same_clause']:>12} {v['mean_similarity_different_clause']:>13}")
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / f"embedder_separation_{emb.name}{'' if a.edit == 'random' else '_paraphrase'}.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"\nSaved to reasoning/results/")
