import re
from .enrich import add_details

# ---------- patterns ----------
# Line ki shuruaat mein section number: 1, 2.1, 4.2.1 (teen level tak)
MARK = re.compile(
    r"^\s*(?:SECTION\s+|Section\s+|ARTICLE\s+|Article\s+)?(\d{1,2}(?:\.\d{1,2}){0,2})[\.\)]?\s+(\S.*)$"
)
# Line ke BEECH mein chhupa number, jaise "... 4. Obligations 4.1 The Contractor shall ..."
INLINE = re.compile(r"(?:(?<=\s)|^)(\d{1,2}(?:\.\d{1,2}){0,2})[\.\)]?\s+(?=[A-Z\"“(])")

# Ye shabd sentence mein hote hain, heading mein nahi
VERBS = re.compile(r"\b(shall|may|will|agrees?|is|are|must|has|have|would|can)\b", re.I)
# "Termination. This Agreement may ..." : chhota title, full stop, phir text
HEAD_THEN_TEXT = re.compile(r"^([A-Z][A-Za-z0-9 ,&/\-'’]{2,70}?)[\.:]\s+(\S.*)$")


def number_to_tuple(num):
    """'2.1' -> (2, 1, 0)   '4.2.1' -> (4, 2, 1)   '3' -> (3, 0, 0)"""
    parts = [int(p) for p in num.split(".")]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def pick_markers(cands):
    """cands = [(number_text, ...), ...] jo number jaisi cheezein mili.
    Inme se sirf wahi rakho jo ek badhte hue sequence (1, 1.1, 1.2, 2 ...) ka hissa hain.
    Isse '30 days after' jaisi line galti se clause nahi banti."""
    start = None
    for i in range(len(cands) - 1):
        k, k2 = number_to_tuple(cands[i][0]), number_to_tuple(cands[i + 1][0])
        # shuruaat: pehla number chhota ho aur turant uske baad agla bada number aaye
        if k[0] <= 5 and k2 > k and k2[0] - k[0] <= 2:
            start = i
            break
    if start is None:
        return []
    accepted = [cands[start]]
    last = number_to_tuple(cands[start][0])
    for c in cands[start + 1:]:
        k = number_to_tuple(c[0])
        if k > last and k[0] - last[0] <= 2:
            accepted.append(c)
            last = k
    return accepted


def find_by_lines(text):
    """Tarika 1: har clause ek nayi line se shuru hota hai."""
    lines = text.splitlines()
    cands = []
    for idx, line in enumerate(lines):
        m = MARK.match(line)
        if m:
            cands.append((m.group(1), idx, m.group(2)))
    acc = pick_markers(cands)
    raw = []
    for n, (num, idx, first) in enumerate(acc):
        end = acc[n + 1][1] if n + 1 < len(acc) else len(lines)
        rest = [l.strip() for l in lines[idx + 1:end] if l.strip()]
        raw.append([num, first, rest])
    return raw


def find_inline(text):
    """Tarika 2: poora contract lambi lines mein hai aur numbers beech mein hain."""
    flat = " ".join(text.split())
    cands = [(m.group(1), m.start(), m.end()) for m in INLINE.finditer(flat)]
    acc = pick_markers(cands)
    raw = []
    for n, (num, s, e) in enumerate(acc):
        end = acc[n + 1][1] if n + 1 < len(acc) else len(flat)
        raw.append([num, flat[e:end].strip(), []])
    return raw


def find_heading(first_line, rest_lines):
    """Return (heading, text). Heading nahi mili toh heading khali aur poora text."""
    first_line = " ".join(first_line.split())
    rest = " ".join(" ".join(rest_lines).split())

    # Case 1: heading apni alag line pe hai, text agli lines mein
    short = len(first_line.split()) <= 8
    no_end_punct = not first_line.endswith((".", ";", ","))
    if rest and short and no_end_punct and not VERBS.search(first_line):
        return first_line.strip(" .:-"), rest

    # Case 2: heading aur text ek hi line mein: "Termination. This Agreement ..."
    full = (first_line + " " + rest).strip()
    m = HEAD_THEN_TEXT.match(full)
    if m and len(m.group(1).split()) <= 8 and not VERBS.search(m.group(1)) and len(m.group(2)) >= 20:
        return m.group(1).strip(), m.group(2).strip()

    return "", full


def split_clauses(text, contract_id, version="v1"):
    raw = find_by_lines(text)
    if len(raw) < 6:                       # line se kam clauses mile toh doosra tarika try karo
        alt = find_inline(text)
        if len(alt) > len(raw):
            raw = alt

    # Title wali rows hatao: "1. DEFINITIONS" jiske baad "1.1 ..." aata hai aur khud ka koi text nahi
    kept = []
    for idx, (num, first, rest) in enumerate(raw):
        next_num = raw[idx + 1][0] if idx + 1 < len(raw) else ""
        title_only = (not rest and len(first.split()) <= 10 and next_num.startswith(num + "."))
        if not title_only:
            kept.append((num, first, rest))

    result = []
    for num, first, rest in kept:
        heading, body = find_heading(first, rest)
        result.append({
            "clause_id": f"{contract_id}{version}_{num}",
            "number": num,
            "heading": heading,
            "text": body,
            "parties": [],
            "obligation_type": "other",
            "deadline": None,
            "defined_terms": [],
            "references": [],
        })

    contract = {"contract_id": contract_id, "version": version,
                "clauses": result, "contradictions": []}
    return add_details(contract, text)