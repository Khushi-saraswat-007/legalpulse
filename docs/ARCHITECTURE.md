# Architecture

```
frontend (React) <--REST--> backend (FastAPI + SQLite)
                               |-- calls nlp_core.extract(file)          -> contract JSON
                               |-- calls reasoning.pipeline.run(old,new) -> risk report JSON
                               |-- monitor job (APScheduler)             -> alerts
```
The backend is the only component that talks to the DB. nlp_core and reasoning are plain
Python libraries (JSON in, JSON out), so they can be developed and tested alone.
