import copy
import random
import re

# Synonym swaps: matlab wahi rehta hai, shabd badalte hain (ye "reword" badlav hai)
SWAPS = [("shall not", "must not"), ("shall", "must"), ("prior to", "before"),
         ("in the event that", "if"), ("pursuant to", "under"), ("commence", "begin"),
         ("utilize", "use"), ("additional", "further"), ("approximately", "about")]

# "30 days", "6 months", "10 percent" jaise number dhundne ka pattern
NUM = re.compile(r"\b(\d{1,3})(\s*(?:\(\d+\)\s*)?)(days?|months?|years?|weeks?|percent|%)", re.I)

# Sentence ki seema (clause todne ke liye)
SENT = re.compile(r"(?<=[.;])\s+(?=[A-Z(])")

# Nayi clause jo hum "added" badlav mein daalenge
BANK = [
    ("Force Majeure", "Neither party shall be liable for any delay or failure to perform caused by events beyond its reasonable control.", "force_majeure"),
    ("Severability", "If any provision of this Agreement is held invalid, the remaining provisions shall remain in full force and effect.", "other"),
    ("Counterparts", "This Agreement may be executed in counterparts, each of which shall be deemed an original.", "other"),
    ("Entire Agreement", "This Agreement constitutes the entire agreement between the parties and supersedes all prior understandings.", "other"),
    ("Notices", "All notices under this Agreement shall be in writing and delivered to the address of the receiving party.", "notice"),
    ("Non-Waiver", "A failure to enforce any provision of this Agreement shall not be deemed a waiver of that provision.", "other"),
]


# ---------- 3 chhote helpers: har ek text mein ek badlav karta hai ----------
def change_number(text):
    """Pehla number double kar do (30 days -> 60 days). Number nahi mila toh None."""
    m = NUM.search(text)
    if not m:
        return None
    n = int(m.group(1))
    new = n * 2 if n < 50 else n + 30
    return text[:m.start(1)] + str(new) + text[m.end(1):]


def reword(text):
    """Synonym swap. Kuch badla nahi toh None."""
    out = text
    for a, b in SWAPS:
        out = re.sub(rf"\b{a}\b", b, out)
    return out if out != text else None


def split_text(text):
    """Text ko beech ke sentence pe do hisson mein todo. Dono hisse 60+ chars ke hone chahiye."""
    parts = SENT.split(text)
    if len(parts) < 2:
        return None
    best = min(range(1, len(parts)), key=lambda i: abs(len(" ".join(parts[:i])) - len(text) / 2))
    a, b = " ".join(parts[:best]), " ".join(parts[best:])
    return (a, b) if len(a) >= 60 and len(b) >= 60 else None


# ---------- main function ----------
def make_edited_pair(old, seed=0, n_modify=3, n_reword=3, n_delete=2, n_add=2, n_split=1, n_merge=1):
    """old = split_clauses() ka output. Return: (new_contract, truth)."""
    rng = random.Random(seed)                      # seed se same badlav dobara aate hain
    cid = old["contract_id"]
    oc = old["clauses"]
    N = len(oc)

    # chhote contract mein kam badlav karo (zyada se zyada 45% clauses)
    scale = min(1.0, (0.45 * N) / max(n_modify + n_reword + n_delete + n_split + n_merge * 2, 1))
    n_modify, n_reword, n_delete, n_split, n_merge = [int(round(x * scale)) for x in
                                                      (n_modify, n_reword, n_delete, n_split, n_merge)]

    free = list(range(1, N))                       # pehli clause ko mat chhedo
    rng.shuffle(free)
    plan = {}                                      # clause index -> (badlav, data)

    def assign(op, count, fn):
        got = 0
        for i in list(free):
            if got >= count:
                break
            result = fn(oc[i]["text"])
            if result:
                plan[i] = (op, result)
                free.remove(i)
                got += 1

    assign("modified", n_modify, change_number)
    assign("reworded", n_reword, reword)
    assign("split", n_split, split_text)
    for _ in range(n_merge):                       # do padosi free clauses jodo
        for i in sorted(free):
            if i + 1 in free:
                plan[i] = ("merge_head", i + 1)
                plan[i + 1] = ("merge_tail", i)
                free.remove(i)
                free.remove(i + 1)
                break
    for i in free[:n_delete]:
        plan[i] = ("deleted", None)

    add_after = sorted(rng.sample(range(0, N - 1), min(n_add, N - 1))) if n_add else []
    bank = BANK[:]
    rng.shuffle(bank)

    # ---- naya clause list banao, saath mein groups (answer key ka kaccha maal) ----
    new, groups = [], []                           # groups: (old idx list, new idx list, type, reworded_only, note)

    def push(c, text=None, heading=None):
        c = copy.deepcopy(c)
        if text is not None:
            c["text"] = text
        if heading is not None:
            c["heading"] = heading
        new.append(c)
        return len(new) - 1

    b = 0
    for i, c in enumerate(oc):
        op, data = plan.get(i, ("keep", None))
        if op == "keep":
            groups.append(([i], [push(c)], "keep", False, ""))
        elif op == "modified":
            groups.append(([i], [push(c, data)], "modified", False, "a number was changed"))
        elif op == "reworded":
            groups.append(([i], [push(c, data)], "unchanged", True, "synonym swap, same meaning"))
        elif op == "deleted":
            groups.append(([i], [], "deleted", False, "clause removed"))
        elif op == "split":
            a, bb = data
            groups.append(([i], [push(c, a), push(c, bb, heading="")], "split", False, "split into two clauses"))
        elif op == "merge_head":
            idx = push(c, c["text"] + " " + oc[data]["text"])
            groups.append(([i, data], [idx], "merged", False, "two adjacent clauses merged"))
        # merge_tail: head ke saath pehle hi ho gaya
        if i in add_after and b < len(bank):
            h, tx, ob = bank[b]
            b += 1
            base = copy.deepcopy(c)
            base.update(heading=h, text=tx, obligation_type=ob, deadline=None,
                        defined_terms=[], references=[], parties=[])
            groups.append(([], [push(base)], "added", False, "new boilerplate clause"))

    # ---- numbering ----
    all_plain_ints = all(re.fullmatch(r"\d+", c["number"]) for c in oc)
    for pos, c in enumerate(new):
        if all_plain_ints:
            c["number"] = str(pos + 1)             # delete/add ke baad 1, 2, 3 ... dobara (renumbering)
    seen = {}
    for c in new:                                  # numbers unique rakho
        n = c["number"]
        if n in seen:
            seen[n] += 1
            c["number"] = f"{n}{chr(64 + seen[n])}"
        else:
            seen[n] = 0
    for c in new:
        c["clause_id"] = f"{cid}v2_{c['number']}"

    # ---- references ko naye ids pe map karo ----
    old_to_new = {}
    for oi, ni, typ, _, _ in groups:
        for o in oi:
            if ni:
                old_to_new[oc[o]["clause_id"]] = new[ni[0]]["clause_id"]
    for c in new:
        c["references"] = [old_to_new[r] for r in c["references"]
                           if r in old_to_new and old_to_new[r] != c["clause_id"]]

    # ---- answer key (truth) ----
    changes = []
    for oi, ni, typ, reworded_only, note in groups:
        old_ids = [oc[i]["clause_id"] for i in oi]
        new_ids = [new[j]["clause_id"] for j in ni]
        renumbered = bool(oi and ni and oc[oi[0]]["number"] != new[ni[0]]["number"])
        if typ == "keep":
            typ = "renumbered" if renumbered else "unchanged"
            note = "renumbered only" if renumbered else "identical"
        if typ == "unchanged" and renumbered:      # matlab wahi, sirf number badla
            typ = "renumbered"
        if typ in ("split", "merged"):
            renumbered = True
        changes.append({"old": old_ids, "new": new_ids, "change_type": typ,
                        "renumbered": renumbered, "reworded_only": reworded_only, "note": note})

    new_contract = {"contract_id": cid, "version": "v2", "clauses": new, "contradictions": [],
                    "meta": {"edited_from": f"{cid}v1", "seed": seed}}
    truth = {"pair": cid, "description": "Real contract with programmatic edits", "changes": changes}
    return new_contract, truth