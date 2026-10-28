# Decision log
| Date | Decision | Why |
|---|---|---|
| start | JSON schemas frozen in `schemas/` | Lets three people work in parallel |
| start | Rule-based impact tracing (no GNN) | No labeled data exists for learned propagation; rules are explainable |
| 2026-10-13 | Backend uses `nlp_core` for clause extraction + contradiction detection; the stand-in splitter in `reasoning/ingest` is no longer used by the API | Part B's extractor finds cross-references and defined terms, which the impact graph needs; it also reads PDF/DOCX. NLI falls back to the rule-based baseline if the model cannot load |
| 2026-10 | Carve-outs are bound to the exact clause number the marker cites ("9(b)" is never read as clause 9) | A loose match silenced real conflicts. A marker is bound only when its target is identifiable; otherwise the pair goes to NLI (PR #7, #8) |
| 2026-10 | Filler words ("anything in", "the provisions of", "terms and conditions of") are allowed between a marker and its target clause | "terms and conditions of Clause 9" broke carve-out detection; regression tests added |
| 2026-10 | Heading-only parent clauses (for example "4. Termination") are never paired for NLI (PR #11) | They caused false positives against their own child clauses |
| 2026-10 | Segmentation and metadata extraction stay rule-based | Transparent and testable, and no labelled data exists to train on; limits are listed in nlp_core/README.md |
| 2026-10 | Real-contract fixes EX-06 to EX-09: table-of-contents entries ignored, list items kept inside their clause, external-law citations skipped, EDGAR page footers dropped (PR #23) | Found by running the extractor on real CUAD contracts |
| 2026-10 | Contradiction score is the mean of both NLI directions | NLI models are order-sensitive. Known weakness: one direction can fire (0.96) while the other does not (0.01), and the mean hides it. Not changed until labelled real clause pairs exist |
| 2026-10 | ContractNLI is used only as a proxy to evaluate the NLI model | It tests hypothesis vs contract, not clause vs clause inside one contract, and its neutral premises are random spans. It does not measure contradiction detection on real contracts |
| 2026-10-28 | Candidate-pair admission ignores generic words (within, days, shall, the, ...) when measuring text similarity | p4v2_3 and p4v2_7 shared only filler words, were sent to NLI and scored 0.976. They are no longer admitted. Side effect: 139 other pairs newly admitted across 20 files, so check candidate recall once labelled pairs exist |
