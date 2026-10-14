# Decision log
| Date | Decision | Why |
|---|---|---|
| start | JSON schemas frozen in `schemas/` | Lets three people work in parallel |
| start | Rule-based impact tracing (no GNN) | No labeled data exists for learned propagation; rules are explainable |
| 2026-10-13 | Backend uses `nlp_core` for clause extraction + contradiction detection; the stand-in splitter in `reasoning/ingest` is no longer used by the API | Part B's extractor finds cross-references and defined terms, which the impact graph needs; it also reads PDF/DOCX. NLI falls back to the rule-based baseline if the model cannot load |
