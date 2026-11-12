import re

# "Defined Term" means ...   /   (the "Defined Term")
DEF1 = re.compile(r"[\"“]([A-Z][A-Za-z0-9&\-' ]{1,40}?)[\"”}]\s+(?:means|shall mean|refers to|has the meaning)")
DEF2 = re.compile(r"\((?:the\s+|each,?\s+|collectively,?\s+|hereinafter\s+(?:the\s+)?(?:referred to as\s+)?)?[\"“]([A-Z][A-Za-z0-9&\-' ]{1,40}?)[\"”}]\s*[\)}]")

# Ye naam party nahi hote, defined terms hote hain
NOT_PARTY = re.compile(
    r"\b(agreement|date|effective|term|party|parties|contract|services?|products?|software|"
    r"confidential|information|territory|license|schedule|exhibit)\b", re.I)

# "Section 5", "Article 3", "Clause 2.1"
REF = re.compile(r"\b(?:Sections?|Articles?|Clauses?|Paragraphs?)\s+(\d{1,2}(?:\.\d{1,2}){0,2})")

# "30 days", "six (6) months", "2 years"
DUR = re.compile(r"\b(\d{1,3})\s*(?:\(\d+\)\s*)?(days?|weeks?|months?|years?)\b", re.I)

# clause ka type: pehle heading mein dhundo, phir text mein
OB_TYPES = [
    ("terminat", "termination"), ("confidential", "confidentiality"), ("indemn", "indemnity"),
    ("warrant", "warranty"), ("governing law", "governing_law"), ("governed by", "governing_law"),
    ("arbitrat", "dispute_resolution"), ("dispute", "dispute_resolution"), ("assign", "assignment"),
    ("licen", "license"), ("liabil", "liability"), ("pay", "payment"), ("fee", "payment"),
    ("royalt", "payment"), ("insur", "insurance"), ("exclusiv", "exclusivity"),
    ("notice", "notice"), ("force majeure", "force_majeure"), ("definition", "definition"),
]


def find_parties(text):
    """Shuru ke 1500 characters mein ("Naam") jaisa pattern dhundo."""
    parties = []
    for name in DEF2.findall(text[:1500]):
        name = name.strip()
        if name not in parties and not NOT_PARTY.search(name):
            parties.append(name)
    if not parties:                                   # "Party A" / "Party B" jaise naam
        for name in re.findall(r"\b(Party [A-Z])\b", text[:3000]):
            if name not in parties:
                parties.append(name)
    return parties[:4]


def find_defined_terms(clauses, parties):
    terms = []
    for c in clauses:
        for t in DEF1.findall(c["text"]) + DEF2.findall(c["text"]):
            t = t.strip()
            if t not in terms and t not in parties:
                terms.append(t)
    return terms


def guess_type(heading, body):
    for source in (heading.lower(), body.lower()):
        for key, label in OB_TYPES:
            if key in source:
                return label
    return "other"


def add_details(contract, full_text):
    """contract dict ko bharo: parties, defined_terms, references, deadline, obligation_type."""
    clauses = contract["clauses"]
    parties = find_parties(full_text)
    terms = find_defined_terms(clauses, parties)
    id_of = {c["number"]: c["clause_id"] for c in clauses}

    for c in clauses:
        body = c["text"]
        c["parties"] = [p for p in parties if re.search(rf"\b{re.escape(p)}\b", body)]
        c["defined_terms"] = [t for t in terms if re.search(rf"\b{re.escape(t)}\b", body)]
        refs = []
        for num in REF.findall(body):
            if num in id_of and num != c["number"] and id_of[num] not in refs:
                refs.append(id_of[num])
        c["references"] = refs
        d = DUR.search(body)
        c["deadline"] = f"{d.group(1)} {d.group(2).lower()}" if d else None
        c["obligation_type"] = guess_type(c["heading"], body)

    contract["meta"] = {"parties_detected": parties, "defined_terms_found": len(terms)}
    return contract