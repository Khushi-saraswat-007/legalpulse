"""What does a modification MEAN?  (Module 3, semantic layer)

textdiff.py only says "these words differ". This module reads the difference:

  * numbers and units      30 -> 60 days (+100%)      amounts, percentages, periods
  * obligation strength    shall -> may               an obligation became a permission (or the reverse)
  * prohibitions           shall not ... added/removed
  * negation               "not", "no", "never" added or removed
  * caps                   "limited to ..." -> "unlimited"   (and the reverse)
  * parties and clause type changed

It is rule-based on purpose: every reason is a short, checkable sentence, so the report can explain itself.
An optional NLI model (see align_versions(semantic_scorer=...)) is used only to confirm that a reworded clause
really kept its meaning; rules, not the NLI model, decide what a change is.
"""
import re

_XREF = re.compile(r"\b(clauses?|sections?|articles?|schedules?|paragraphs?|annex(?:ure)?s?|exhibits?)\s+\d+(?:\.\d+)*(?:\s*\([a-z0-9]+\))*", re.I)
_UNIT = r"business\s+days?|calendar\s+days?|working\s+days?|days?|weeks?|months?|years?|hours?|%|per\s*cent|percent"
_QTY = re.compile(rf"(?P<cur>[$€£₹]|rs\.?\s|inr\s|usd\s)?\s*(?P<num>\d[\d,]*(?:\.\d+)?)(?!\d)(?!(?:st|nd|rd|th)\b)\)?\s*(?P<unit>{_UNIT})?", re.I)
_BENIGN_NEG = re.compile(r"\b(no|not)\s+(later|less|more|earlier|fewer|greater)\s+than\b", re.I)

_PROHIB = re.compile(r"\b(shall not|must not|may not|will not|cannot|can not|is prohibited|are prohibited)\b", re.I)
_OBLIG = re.compile(r"\b(shall|must|will|agrees to|undertakes to|is required to|are required to)\b", re.I)
_PERM = re.compile(r"\b(may|can|is entitled to|are entitled to|is permitted to|has the right to|have the right to)\b", re.I)
_NEG = re.compile(r"\b(not|no|never|neither|nor|without|none)\b", re.I)
_CAP = re.compile(r"\b(limited to|shall not exceed|not exceed|not exceeding|capped at|cap of|maximum|up to)\b", re.I)
_UNLIM = re.compile(r"\b(unlimited|without limit(?:ation)?|no limit|uncapped|no cap)\b", re.I)
_GENERIC_TYPES = {None, "", "general", "other", "none", "unknown"}

# how severe each kind of semantic change is (0..1)
SEVERITY = {"cap_removed": 0.95, "cap_introduced": 0.60, "prohibition": 0.70, "negation": 0.70,
            "obligation_weakened": 0.65, "obligation_strengthened": 0.60, "party": 0.50, "type": 0.40}


def _unit(raw, cur):
    if cur:
        return "amount"
    if not raw:
        return None
    r = re.sub(r"\s+", " ", raw.lower())
    if "%" in r or "cent" in r:
        return "%"
    for key in ("day", "week", "month", "year", "hour"):
        if key in r:
            return key + "s"
    return None


def quantities(text: str) -> list:
    """[(value, unit)] in reading order. Cross-reference numbers ("Clause 4.1") are ignored."""
    out = []
    for m in _QTY.finditer(_XREF.sub(" ", text)):
        try:
            v = float(m.group("num").replace(",", ""))
        except ValueError:
            continue
        out.append((v, _unit(m.group("unit"), m.group("cur"))))
    return out


def _fmt(v):
    return str(int(v)) if float(v).is_integer() else f"{v:.2f}".rstrip("0").rstrip(".")


def _numeric_changes(old: str, new: str) -> list:
    qo, qn = quantities(old), quantities(new)
    units = sorted({u for _, u in qo} | {u for _, u in qn}, key=lambda x: (x is None, str(x)))
    changes = []
    for u in units:
        a = [v for v, uu in qo if uu == u]
        b = [v for v, uu in qn if uu == u]
        if a == b:
            continue
        if len(a) == len(b):
            pairs = [(x, y) for x, y in zip(a, b) if x != y]
        else:
            ra, rb = [x for x in a if x not in b], [y for y in b if y not in a]
            pairs = [(ra[0], rb[0])] if len(ra) == 1 and len(rb) == 1 else []
            if not pairs and (ra or rb):
                changes.append({"unit": u, "old": None, "new": None, "pct": None, "direction": "set changed",
                                "text": f"{u or 'numbers'} changed: {', '.join(map(_fmt, ra)) or '-'} -> {', '.join(map(_fmt, rb)) or '-'}"})
        for x, y in pairs:
            pct = (y - x) / x if x else None
            label = {"%": "%", "amount": "", None: ""}.get(u, f" {u}")
            sign = f" ({pct:+.0%})" if pct is not None else ""
            changes.append({"unit": u, "old": x, "new": y, "pct": pct, "direction": "increased" if y > x else "decreased",
                            "text": f"{_fmt(x)} → {_fmt(y)}{label}{sign}"})
    return changes


def _modality(t: str) -> dict:
    prohib = len(_PROHIB.findall(t))
    rest = _PROHIB.sub(" ", t)
    return {"prohibition": prohib, "obligation": len(_OBLIG.findall(rest)), "permission": len(_PERM.findall(rest))}


def _negations(t: str) -> int:
    return len(_NEG.findall(_BENIGN_NEG.sub(" ", _PROHIB.sub(" ", t))))


def compare_clauses(old: dict, new: dict) -> dict:
    """old/new are clause dicts (text, parties, obligation_type). Returns
    {"reasons": [str], "features": {...}, "severity_hint": 0..1}."""
    ot, nt = old.get("text", ""), new.get("text", "")
    reasons, kinds, features = [], [], {}

    # caps: "limited to ..." <-> "unlimited"
    o_cap, n_cap = bool(_CAP.search(ot)), bool(_CAP.search(nt))
    o_un, n_un = bool(_UNLIM.search(ot)), bool(_UNLIM.search(nt))
    if (o_cap and not o_un) and n_un and not n_cap:
        reasons.append("cap removed (limited → unlimited)"); kinds.append(("cap_removed", SEVERITY["cap_removed"]))
    elif o_un and not o_cap and n_cap and not n_un:
        reasons.append("cap introduced (unlimited → limited)"); kinds.append(("cap_introduced", SEVERITY["cap_introduced"]))

    # numbers and units
    nums = _numeric_changes(ot, nt)
    features["numeric"] = nums
    for c in nums:
        reasons.append(c["text"])
        mag = abs(c["pct"]) if c["pct"] is not None else 0.5
        kinds.append(("numeric", 0.35 + 0.65 * min(mag, 1.0)))

    # obligation strength and prohibitions
    mo, mn = _modality(ot), _modality(nt)
    features["modality"] = {"old": mo, "new": mn}
    if mo["obligation"] > 0 and mn["obligation"] == 0 and mn["permission"] > mo["permission"]:
        reasons.append("obligation weakened (shall → may)"); kinds.append(("obligation_weakened", SEVERITY["obligation_weakened"]))
    elif mo["permission"] > 0 and mn["permission"] == 0 and mn["obligation"] > mo["obligation"]:
        reasons.append("permission became an obligation (may → shall)"); kinds.append(("obligation_strengthened", SEVERITY["obligation_strengthened"]))
    if mn["prohibition"] > mo["prohibition"]:
        reasons.append("prohibition added"); kinds.append(("prohibition", SEVERITY["prohibition"]))
    elif mn["prohibition"] < mo["prohibition"]:
        reasons.append("prohibition removed"); kinds.append(("prohibition", SEVERITY["prohibition"]))

    # negation
    no, nn = _negations(ot), _negations(nt)
    features["negations"] = {"old": no, "new": nn}
    if nn > no:
        reasons.append("negation added"); kinds.append(("negation", SEVERITY["negation"]))
    elif nn < no:
        reasons.append("negation removed"); kinds.append(("negation", SEVERITY["negation"]))

    # parties and clause type
    po, pn = set(old.get("parties") or []), set(new.get("parties") or [])
    if po and pn and po != pn:
        added, removed = sorted(pn - po), sorted(po - pn)
        reasons.append("party changed (" + "; ".join(([f"+{', '.join(added)}"] if added else []) + ([f"-{', '.join(removed)}"] if removed else [])) + ")")
        kinds.append(("party", SEVERITY["party"]))
    to, tn = old.get("obligation_type"), new.get("obligation_type")
    if to not in _GENERIC_TYPES and tn not in _GENERIC_TYPES and to != tn:
        reasons.append(f"clause type changed ({to} → {tn})"); kinds.append(("type", SEVERITY["type"]))

    hint = 0.0
    if kinds:
        hint = min(1.0, max(v for _, v in kinds) + 0.05 * (len(kinds) - 1))
    return {"reasons": reasons, "features": features, "severity_hint": round(hint, 3)}


def describe_removed(clause: dict) -> dict:
    """A deleted clause takes its content with it: say what protection or duty disappeared."""
    t = clause.get("text", "")
    reasons, hint = [], 0.0
    if _CAP.search(t) and not _UNLIM.search(t):
        reasons.append("the removed clause contained a cap or limit"); hint = max(hint, SEVERITY["cap_removed"])
    m = _modality(t)
    if m["prohibition"]:
        reasons.append("the removed clause contained a prohibition"); hint = max(hint, SEVERITY["prohibition"])
    if m["obligation"]:
        reasons.append("the removed clause contained obligations"); hint = max(hint, 0.60)
    if quantities(t):
        reasons.append("the removed clause contained figures or deadlines"); hint = max(hint, 0.50)
    return {"reasons": reasons, "features": {}, "severity_hint": round(hint, 3)}


def describe_added(clause: dict) -> dict:
    """A new clause adds duties or limits that did not exist before."""
    t = clause.get("text", "")
    reasons, hint = [], 0.0
    m = _modality(t)
    if m["prohibition"]:
        reasons.append("the new clause adds a prohibition"); hint = max(hint, SEVERITY["prohibition"])
    if _CAP.search(t) and not _UNLIM.search(t):
        reasons.append("the new clause adds a cap or limit"); hint = max(hint, SEVERITY["cap_introduced"])
    if m["obligation"]:
        reasons.append("the new clause adds obligations"); hint = max(hint, 0.50)
    return {"reasons": reasons, "features": {}, "severity_hint": round(hint, 3)}
