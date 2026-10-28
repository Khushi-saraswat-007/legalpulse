# NLP Core (Part B): Modules 1-2

Raw contract (PDF / DOCX / TXT) -> JSON that validates against `schemas/contract.schema.json`.
Plain Python library: JSON in/out, no DB, no frontend, no graph code (that is Part C / A).

```python
from legalpulse_nlp import extract
contract = extract("contract.pdf", contract_id="c001", version="v1")      # dict -> reasoning.pipeline.run(old, new)
contract = extract("contract.pdf", detect_contradictions=False)            # Module 1 only, no model needed
```
CLI: `python -m legalpulse_nlp contract.pdf --backend rule --out out.json`

## Setup
```bash
python -m venv .venv && source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r nlp_core/requirements.txt
export PYTHONPATH=nlp_core/src                              # Windows PowerShell: $env:PYTHONPATH="nlp_core/src"
pytest nlp_core/tests
```
Module 2 downloads a pretrained NLI model on first use (default `cross-encoder/nli-deberta-v3-small`, ~150 MB, CPU ok).
Change it in `src/legalpulse_nlp/config.py` (`NLI_MODEL_NAME`, e.g. `roberta-large-mnli`).
If the model cannot be loaded you get `NLIModelError`; use `nli_backend=RuleBasedNLIBackend()` for the offline baseline.

## Module 1: how it works (all transparent rules)
| Step | File | What |
|---|---|---|
| ingest | `ingest.py` | pdfplumber / python-docx / txt; strips page numbers; rebuilds Word auto-numbering; raises `ScannedPDFError` (OCR needed), `EmptyDocumentError`, `UnsupportedFormatError` |
| split | `segmenter.py` | "5." / "5.1" / "Clause 5" numbering; nested clauses are separate clauses ("4.1"); "(a)" items stay inside their clause; heading detection; preamble kept out of clauses; warns on duplicate numbers / gaps |
| metadata | `metadata.py` | parties (role words + "(the "Buyer")"), obligation_type (keyword rules in `config.py`), deadline, defined_terms, references -> clause_ids |
| assemble | `extractor.py` | stable ids `<contract_id>_<number>`, schema validation, warnings |

Conventions: `references` holds clause_ids and only EXPLICIT "Clause/Section N" citations (unknown numbers become warnings).
`defined_terms` = defined terms that appear in that clause. `deadline` = first explicit time limit, else `null`. Unknown obligation -> `"general"`.

## Module 2: contradiction detection
`contradiction.py`: candidate pairs (shared type / term / reference / TF-IDF similarity, capped at `MAX_CANDIDATE_PAIRS`)
-> skip explicit carve-outs ("Notwithstanding Clause 9..." is an override, not a conflict) -> NLI in BOTH directions, averaged
-> label by thresholds in `config.py`. Only `contradiction` records are emitted by default (`EMIT_LABELS`).
`nli.py`: `HFNLIBackend` (real model, loaded once) and `RuleBasedNLIBackend` (crude no-ML baseline, for tests/comparison).
Any object with `.predict(pairs)` works, so a fine-tuned Legal-BERT can be dropped in later.

## Evaluation (`python nlp_core/scripts/evaluate_extraction.py [--backend rule|hf]`)
Run against the teammate's mock contracts. They are hand-made, same-author, tiny: a sanity check, not a benchmark.
Latest run, rule-based NLI baseline on the mock set (the Hugging Face model is evaluated separately below, on ContractNLI):

| Field | Exact match |
|---|---|
| clause count / number / heading / text | 8/8, 88/88, 88/88, 88/88 (clean text only) |
| obligation_type | 71/88 (mock uses finer labels: price, services, updates, subletting ...) |
| deadline | 86/88 |
| defined_terms | 86/88 |
| references | 65/88 (mock also counts implicit links; we only extract explicit citations) |
| parties | 46/88 (mock lists both parties even where a clause names neither; we only list parties named in the clause) |

Contradictions (rule baseline): p1-p3 TP=1 FP=3 FN=0; held-out p4 TP=0 FP=2. Only ONE labelled positive pair exists, so no precision/recall claim is meaningful yet.

### NLI model evaluation (ContractNLI dev, a proxy)

Scored with `nlp_core/scripts/evaluate_nli.py` on a sample of the ContractNLI dev split: 495 examples (200 entailment, 95 contradiction, 200 neutral). Results are stored in `nlp_core/results/`.

| Backend | Accuracy | Macro-F1 | Contradiction precision / recall |
|---|---|---|---|
| Rule-based baseline | 0.525 | 0.433 | 0.375 / 0.663 |
| `cross-encoder/nli-deberta-v3-small` | 0.651 | 0.624 | 0.511 / 0.505 |
| DeBERTa, hypothesis-only (premise blanked) | 0.345 | 0.219 | 0.000 / 0.000 |

How to read it:
* The model beats the rule baseline. The hypothesis-only ablation (Gururangan et al., 2018) falls below the share of the largest class (200/495 = 0.404), so the model is using the premise and not only the hypothesis wording.
* Raising the contradiction threshold from 0.5 to 0.9 lifts contradiction precision from about 0.52 to 0.61 while recall stays near 0.5 (see `contradiction_sweep` in the JSON). The configured threshold is 0.80.

Caveats:
* ContractNLI is a proxy. It scores hypothesis vs contract, not clause vs clause inside one contract, and its neutral premises are random spans, not human-checked.
* Contradiction accuracy on real contracts is NOT measured: only one labelled positive pair exists in the mock set. The UI labels contradictions "experimental".
* The mock pair p4 is no longer a clean held-out set. It was used to find and fix a false positive (p4v2_3 / p4v2_7, scored 0.976 by the Hugging Face model); the fix ignores generic words when admitting candidate pairs.

Reproduce (from the repo root):

```
python nlp_core/scripts/prepare_contractnli.py <ContractNLI dev json> --out contractnli/dev.csv
python nlp_core/scripts/evaluate_nli.py --csv contractnli/dev.csv --backend both --tag dev --out nlp_core/results/nli_dev.json
python nlp_core/scripts/evaluate_nli.py --csv contractnli/dev.csv --backend hf --hypothesis-only --tag dev --out nlp_core/results/nli_dev_hyponly.json
```

Tune on dev; run the test split once, at the very end.

## Known limitations
* Scanned PDFs are detected, not OCR'd. Two-column or table-heavy layouts may split wrongly. Test on real contracts.
* Cross-references to unknown clauses are reported as warnings, not guessed.
* Only the first deadline per clause is kept (schema has one string).
* Exception handling is limited to explicit "notwithstanding / except as provided / subject to Clause N" patterns.
* Fine-tuning Legal-BERT is NOT done yet (needs a label mapping from CUAD / ContractNLI and a GPU: use Colab/Kaggle).
* Candidate pairs ignore generic words (within, days, shall, ...). How many real conflicting pairs this filter keeps (its   recall) is not measured yet; it needs labelled real clause pairs.
