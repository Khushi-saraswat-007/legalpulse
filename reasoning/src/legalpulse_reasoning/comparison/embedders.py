"""Sentence embedders. All return L2-normalised numpy arrays, so dot product = cosine similarity."""
import re
import zlib
import warnings
import numpy as np

_STOP = set("a an the of to in on or and for by with at as is are be been this that it its".split())


class BagOfWordsEmbedder:
    """Baseline: hashed word counts. Stateless, so any two texts are directly comparable.
    Used for tests and as the 'no deep learning' baseline in the evaluation chapter."""
    name = "bow"

    def __init__(self, dim: int = 2048):
        self.dim = dim

    def encode(self, texts):
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            for w in re.findall(r"[a-z]+|\d+", t.lower()):
                if w not in _STOP:
                    out[i, zlib.crc32(w.encode()) % self.dim] += 1.0
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.maximum(norms, 1e-9)


class SBertEmbedder:
    """Sentence-BERT embedder (needs `pip install sentence-transformers`; downloads the model once)."""
    name = "sbert"

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def encode(self, texts):
        return np.asarray(self.model.encode(list(texts), normalize_embeddings=True))


class LegalBertEmbedder:
    """LEGAL-BERT (Chalkidis et al., 2020) as a clause embedder: mean-pooled last hidden state, L2-normalised.
    Needs `pip install transformers torch`; downloads the model once. Used as a comparison baseline in the
    evaluation: it was pre-trained on legal text but, unlike Sentence-BERT, not trained to compare sentences."""
    name = "legalbert"

    def __init__(self, model_name: str = "nlpaueb/legal-bert-base-uncased", max_length: int = 256):
        import torch
        from transformers import AutoModel, AutoTokenizer
        self._torch = torch
        self.max_length = max_length
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).eval()

    def encode(self, texts):
        torch, out = self._torch, []
        for i in range(0, len(texts), 16):
            batch = self.tok(list(texts[i:i + 16]), padding=True, truncation=True,
                             max_length=self.max_length, return_tensors="pt")
            with torch.no_grad():
                hidden = self.model(**batch).last_hidden_state
            mask = batch["attention_mask"].unsqueeze(-1).float()
            pooled = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
            out.append(torch.nn.functional.normalize(pooled, dim=1).numpy())
        return np.vstack(out) if out else np.zeros((0, 768), dtype=np.float32)


def make_embedder(name: str):
    """'bow' | 'sbert' | 'legalbert'"""
    return {"bow": BagOfWordsEmbedder, "sbert": SBertEmbedder, "legalbert": LegalBertEmbedder}[name]()


def get_default_embedder():
    try:
        return SBertEmbedder()
    except Exception as e:  # missing package or no internet for the first model download
        warnings.warn(f"SBERT unavailable ({e}); falling back to the bag-of-words baseline.")
        return BagOfWordsEmbedder()
