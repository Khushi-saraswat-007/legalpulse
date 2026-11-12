"""Step 3: rule-based extraction of parties, obligation type, deadline, defined terms, references.

Everything here is transparent regex / keyword logic. Nothing is invented: when a field cannot be
found we return [] or None (allowed by schemas/contract.schema.json).
"""
from __future__ import annotations

import re

from . import config

# ------------------------------------------------------------------ parties
_PREAMBLE_ROLE = re.compile(
    r"""\(\s*(?:hereinafter\s+)?(?:referred\s+to\s+as\s+|called\s+|the\s+)*
        ["“']([A-Z][\w ]{1,30}?)["”']\s*\)""",
    re.X,
)


def detect_document_roles(full_text: str) -> list[str]:
    """Party roles used in this contract, in order of first appearance."""
    found: list[tuple[int, str]] = []
    for m in _PREAMBLE_ROLE.finditer(full_text):
        role = re.sub(r"^(the)\s+", "", m.group(1).strip(), flags=re.I)
        if role and role not in {"Effective Date", "Agreement", "Contract"}:
            found.append((m.start(), role))
    for role in config.PARTY_ROLES:
        m = re.search(rf"\b{re.escape(role)}\b", full_text)
        if m:
            found.append((m.start(), role))
    found.sort()
    roles: list[str] = []
    for _, r in found:
        if r not in roles:
            roles.append(r)
    return roles


def extract_parties(text: str, doc_roles: list[str]) -> list[str]:
    hits: list[tuple[int, str]] = []
    for role in doc_roles:
        m = re.search(rf"\b{re.escape(role)}\b", text)
        if m:
            hits.append((m.start(), role))
    parties = [r for _, r in sorted(hits)]
    # "Either party", "both parties": applies to every party, but only if we know the parties.
    if len(doc_roles) >= 2 and any(re.search(rf"\b{p}\b", text, re.I) for p in config.COLLECTIVE_PARTY_PHRASES):
        for r in doc_roles[:2]:
            if r not in parties:
                parties.append(r)
    return parties


# ------------------------------------------------------------------ obligation type
def classify_obligation(heading: str, text: str) -> str:
    h = heading.lower().strip()
    t = text.lower()
    if h:
        for typ, h_re, _ in config.OBLIGATION_RULES:
            if re.search(h_re, h):
                return typ
    for typ, _, t_re in config.OBLIGATION_RULES:
        if re.search(t_re, t):
            return typ
    return config.DEFAULT_OBLIGATION_TYPE


# ------------------------------------------------------------------ deadlines
_NUM_WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen twenty".split())}
_NUM_WORDS.update({"thirty": 30, "forty": 40, "forty-five": 45, "sixty": 60, "ninety": 90})
_UNIT = r"(?:business\s+|working\s+|calendar\s+)?(?:hour|day|week|month|year)s?"
_NUM = r"(?:\d+|" + "|".join(sorted(_NUM_WORDS, key=len, reverse=True)) + r")"
_DURATION = re.compile(rf"\b({_NUM})(?:\s*\(\s*(\d+)\s*\))?[\s-]+({_UNIT})\b", re.I)
_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
_DATE_LONG = re.compile(rf"\b(\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{_MONTHS})\s+\d{{4}}|(?:{_MONTHS})\s+\d{{1,2}},?\s+\d{{4}})\b")
_DATE_ISO = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_RECURRING = re.compile(r"\b(\d{1,2}(?:st|nd|rd|th)\s+(?:day\s+)?of\s+(?:each|every|the)\s+(?:calendar\s+)?(?:month|quarter|year))\b", re.I)
# Durations that are NOT deadlines ("24 hours a day", "for a period of 3 years" is a term, still kept).
_NOT_DEADLINE_CONTEXT = re.compile(r"\ba\s+day\b|\bper\s+day\b|\beach\s+day\b", re.I)


_CUE_BEFORE = re.compile(r"(within|after|before|prior to|no later than|on or before|by|for a period of|for|from|upon|with|on|every|each)\W*$", re.I)
_CUE_AFTER = re.compile(r"^\W*(?:'s?\s+)?(?:written\s+)?(?:prior\s+)?(?:notice|after|before|from|of the|following|of receipt|of such)", re.I)
_AMOUNT_AFTER = re.compile(r"^\W*(?:of\s+)?(?:the\s+)?(?:monthly\s+)?(?:rent|fee|fees|salary|wages|charges|price)", re.I)


def extract_deadline(text: str) -> str | None:
    """First explicit time limit in the clause, e.g. '30 days', '5th of each month', '2026-03-31'.

    Durations with a deadline cue ("within 30 days", "30 days notice") beat bare durations such as the
    "3 months" in "a deposit equal to 3 months of Rent" (an amount, not a deadline).
    """
    strong: list[tuple[int, str]] = []
    weak: list[tuple[int, str]] = []
    for m in _RECURRING.finditer(text):
        strong.append((m.start(), m.group(1)))
    for rx in (_DATE_LONG, _DATE_ISO):
        for m in rx.finditer(text):
            strong.append((m.start(), m.group(1)))
    for m in _DURATION.finditer(text):
        if _NOT_DEADLINE_CONTEXT.search(text[m.end():m.end() + 12]):
            continue
        num = m.group(2) or m.group(1)
        if not num.isdigit():
            num = str(_NUM_WORDS.get(num.lower(), num))
        unit = re.sub(r"\s+", " ", m.group(3).lower())
        item = (m.start(), f"{num} {unit}")
        before, after = text[max(0, m.start() - 25):m.start()], text[m.end():m.end() + 25]
        if _AMOUNT_AFTER.match(after):
            continue                                     # "3 months of Rent" = an amount
        (strong if (_CUE_BEFORE.search(before) or _CUE_AFTER.match(after)) else weak).append(item)
    pool = strong or weak
    return min(pool)[1] if pool else None


# ------------------------------------------------------------------ defined terms
_DEF_PATTERNS = [
    re.compile(r"""["“]([A-Z][\w\- ]{1,40}?)["”]\s+(?:means|shall\s+mean|has\s+the\s+meaning|refers\s+to)"""),
    re.compile(r"""\(\s*(?:the\s+|each\s+a\s+)?["“]([A-Z][\w\- ]{1,40}?)["”]\s*\)"""),
]


def detect_defined_terms(full_text: str, doc_roles: list[str]) -> list[str]:
    terms: list[str] = []
    for rx in _DEF_PATTERNS:
        for m in rx.finditer(full_text):
            t = m.group(1).strip()
            if t not in terms and t not in doc_roles:
                terms.append(t)
    return terms


def terms_in_clause(text: str, doc_terms: list[str]) -> list[str]:
    return [t for t in doc_terms if re.search(rf"\b{re.escape(t)}\b", text)]


# ------------------------------------------------------------------ cross references
_REF = re.compile(
    r"""\b(?:clauses?|sections?|articles?|paragraphs?)\s+
        (?P<body>\d+(?:\.\d+)*(?:\([a-z]\))?
            (?:\s*(?:,|and|or|&|to|through|-)\s*\d+(?:\.\d+)*(?:\([a-z]\))?)*)""",
    re.I | re.X,
)
_NUMTOK = re.compile(r"\d+(?:\.\d+)*")
# NLP-EX-08: "Section 351 of the PHSA", "Section 5 of the Securities Exchange Act", "Section 42 U.S.C.262"
# cite external law, not a clause of this contract. Case-sensitive on purpose (Act / PHSA capitals).
_EXTERNAL_AFTER = re.compile(
    r"""\s*(?:\([a-z0-9]+\)\s*)*
    (?:
        (?:U\.?\s?S\.?\s?C|C\.?\s?F\.?\s?R)\b
      | (?:U\.S\.C\.|C\.F\.R\.|USC|CFR)
      | (?:of|under)\s+(?:the\s+)?(?:[A-Z][A-Za-z&.'\-]*\s+){0,4}(?:Act|Code|Law|Laws|Regulations?|Rules?|Statute|Directive|Treaty|Convention|Constitution)\b
      | (?:of|under)\s+(?:the\s+)?[A-Z]{2,}(?:[&/][A-Z]+)*\b
    )""",
    re.X,
)


def extract_references(text: str, own_number: str, number_to_id: dict[str, str]) -> tuple[list[str], list[str]]:
    """Return (resolved clause_ids, unresolved numbers). Self references are dropped."""
    resolved: list[str] = []
    unresolved: list[str] = []
    for m in _REF.finditer(text):
        body = m.group("body")
        if _EXTERNAL_AFTER.match(text, m.end("body")):
            continue   # NLP-EX-08: external law, not a clause of this contract
        nums = _NUMTOK.findall(body)
        if re.search(r"\b(to|through)\b|\d\s*-\s*\d", body) and len(nums) == 2 and "." not in "".join(nums):
            lo, hi = int(nums[0]), int(nums[1])
            if 0 < hi - lo <= 20:
                nums = [str(i) for i in range(lo, hi + 1)]
        for n in nums:
            if n == own_number:
                continue
            cid = number_to_id.get(n)
            if cid is None:
                if n not in unresolved:
                    unresolved.append(n)
            elif cid not in resolved:
                resolved.append(cid)
    return resolved, unresolved
