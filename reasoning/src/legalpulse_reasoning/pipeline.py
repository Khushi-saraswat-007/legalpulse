"""End-to-end entry point: (old contract JSON, new contract JSON) -> risk report JSON."""
from .graph.builder import build_graph, graph_to_json
from .impact.tracer import trace_impact
from .risk.scorer import score_risk
from .comparison.aligner import align_versions


def _explain(ch: dict, s: dict) -> str:
    """Plain-language reasons first (what the change means), then the word-level summary, then the score parts."""
    reasons = (ch.get("semantic") or {}).get("reasons") or []
    text = ("; ".join(reasons[:3]) + ". " + ch["summary"]) if reasons else ch["summary"]
    return f"{text} (score parts: {s['components']})"


def run(old_contract: dict, new_contract: dict, embedder=None, semantic_scorer=None) -> dict:
    changes = align_versions(old_contract, new_contract, embedder, semantic_scorer)
    g = build_graph(new_contract)
    g_old = build_graph(old_contract)      # needed to score DELETED clauses (they are not in the new graph)
    old_to_new = {}                        # old clause id -> the new clause id that replaced it
    for ch in changes:
        for oid in ch.get("old_clause_ids") or []:
            if ch.get("new_clause_ids"):
                old_to_new[oid] = ch["new_clause_ids"][0]
    flagged = {c for p in new_contract.get("contradictions", [])
               if p["label"] == "contradiction" for c in (p["clause_a"], p["clause_b"])}
    risks = []
    for ch in changes:
        new_ids = ch.get("new_clause_ids") or []
        if ch["change_type"] == "unchanged":
            continue
        if not new_ids:
            # DELETED clause: it only exists in the old version, so trace its impact in the OLD graph
            # and report the clauses that depended on it (translated to their ids in the new version).
            old_ids = ch.get("old_clause_ids") or []
            if not old_ids:
                continue
            dep = {}
            for oid in old_ids:
                for r in trace_impact(g_old, oid):
                    nid = old_to_new.get(r["clause_id"])
                    if nid and nid not in dep:
                        dep[nid] = r
            dep = sorted(dep.values(), key=lambda r: -r["score"])
            s = score_risk(ch, dep, False)
            risks.append({"severity": s["severity"], "score": s["score"],
                          "trigger_clause": old_ids[0],      # the clause only exists in the old version
                          "impacted_clauses": list(dict.fromkeys(old_to_new[r["clause_id"]] for r in dep)),
                          "explanation": _explain(ch, s)})
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
                      "explanation": _explain(ch, s)})
    risks.sort(key=lambda r: -r["score"])
    for i, r in enumerate(risks, 1):
        r["rank"] = i
    return {"contract_id": new_contract["contract_id"], "changes": changes,
            "graph": graph_to_json(g), "risks": risks}
