# LegalPulse: Sensing Risk Before It Becomes a Problem

A legal intelligence platform for contract risk analysis.
Pipeline: extract clauses -> detect contradictions -> compare versions -> build dependency graph -> trace impact -> ranked, explainable risk report.

## Repo layout

| Folder | Owner | Contents |
|---|---|---|
| `frontend/` | Person A | React UI (login, upload, report viewer, diff view, graph view, dashboard) |
| `nlp_core/` | Person B | Modules 1-2: clause/entity extraction, contradiction detection |
| `reasoning/` | Person C | Modules 3-6: version comparison, knowledge graph, impact tracing, risk report |
| `backend/` | Person C | FastAPI API, database, auth, monitoring job, alerts |
| `schemas/` | All | Shared JSON contracts between the parts. Change only via PR + group announcement |
| `data/` | All | Sample contracts and test data |
| `docs/` | All | Architecture, decision log |

## Data flow

```
Upload -> [backend] -> nlp_core (contract JSON) -> reasoning (risk report JSON) -> [backend] -> frontend
```

## Rules

1. `main` always works. Work on `feature/<name>` branches, merge by pull request.
2. Schemas in `schemas/` are the contract between parts. Never change them silently.
3. Each folder has its own `requirements.txt` / `package.json`.
4. Log decisions in `docs/DECISIONS.md` (useful for the viva).

## Quick start (reasoning + backend)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r reasoning/requirements.txt -r backend/requirements.txt
pytest reasoning/tests backend/tests
uvicorn backend.app.main:app --reload
```
