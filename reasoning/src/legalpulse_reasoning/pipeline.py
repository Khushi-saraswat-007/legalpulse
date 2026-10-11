"""End-to-end entry point: (old contract JSON, new contract JSON) -> risk report JSON."""
from .graph.builder import build_graph, graph_to_json
from .impact.tracer import trace_impact
from .risk.scorer import score_risk
from .comparison.aligner import align_versions


def run(old_contract: dict, new_contract: dict, embedder=None) -> dict:
    changes = align_versions(old_contract, new_contract, embedder)
    g = build_graph(new_contract)
    flagged = {c for p in new_contract.get("contradictions", [])
               if p["label"] == "contradiction" for c in (p["clause_a"], p["clause_b"])}
    risks = []
    for ch in changes:
        new_ids = ch.get("new_clause_ids") or []
        if ch["change_type"] == "unchanged" or not new_ids:
            continue
        impacted = {}
        for nid in new_ids:
            for r in trace_impact(g, nid):
                if r["clause_id"] not in new_ids and r["clause_id"] not in impacted:
                    impacted[r["clause_id"]] = r
        impacted = sorted(impacted.values(), key=lambda r: -r["score"])
        s = score_risk(ch, impacted, any(n in flagged for n in new_ids))
        risks.append({"severity": s["severity"], "score": s["score"],
                      "trigger_clause": new_ids[0],
                      "impacted_clauses": [i["clause_id"] for i in impacted],
                      "explanation": f"{ch['summary']} (score parts: {s['components']})"})
    risks.sort(key=lambda r: -r["score"])
    for i, r in enumerate(risks, 1):
        r["rank"] = i
    return {"contract_id": new_contract["contract_id"], "changes": changes,
            "graph": graph_to_json(g), "risks": risks}
