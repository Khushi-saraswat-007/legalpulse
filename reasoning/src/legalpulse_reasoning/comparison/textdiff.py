"""Cheap, explainable text comparison used to decide 'same meaning?' and to describe changes.

meaning_changed() is a deliberately STRICT heuristic: it flags a clause as modified if any number
differs or any content word differs after light normalisation. When in doubt it says "modified",
because missing a real change is worse than flagging a harmless rewording. Its known weakness
(pure rewordings that swap several words) is what the NLI upgrade in Module 2 is meant to fix.
"""
import re
import difflib

_STOP = set("a an the of to in on or and for by with at as is are be been this that it its "
            "all each every such".split())
_IRREGULAR = {"kept": "keep", "must": "shall", "will": "shall"}


def _stem(w: str) -> str:
    if w in _IRREGULAR:
        return _IRREGULAR[w]
    for suf in ("ing", "ed", "es", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def numbers(text: str) -> set:
    return {n.replace(",", "").rstrip(".") for n in re.findall(r"\d[\d,\.]*%?", text)}


def content_words(text: str) -> set:
    words = re.findall(r"[a-z]+", re.sub(r"'s\b", "", text.lower()))
    return {_stem(w) for w in words if w not in _STOP}


def meaning_changed(old: str, new: str) -> bool:
    if numbers(old) != numbers(new):
        return True
    return bool(content_words(old) ^ content_words(new))


def summarize_change(old: str, new: str, max_edits: int = 3) -> str:
    a, b = old.split(), new.split()
    edits = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag == "replace":
            edits.append(f"'{' '.join(a[i1:i2])}' -> '{' '.join(b[j1:j2])}'")
        elif tag == "delete":
            edits.append(f"removed '{' '.join(a[i1:i2])}'")
        elif tag == "insert":
            edits.append(f"added '{' '.join(b[j1:j2])}'")
    if not edits:
        return "No change"
    more = f" (+{len(edits) - max_edits} more edits)" if len(edits) > max_edits else ""
    return "Changed: " + "; ".join(edits[:max_edits]) + more
