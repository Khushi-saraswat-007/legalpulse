"""Continuous monitoring job (TODO).

Every N minutes: scan the watch folder / DB for new or updated contracts,
run nlp_core + reasoning on them, store the report, and create Alerts for
deadlines within 7 days. Scheduled with APScheduler from main.py.
"""


def scan_and_process():
    pass
