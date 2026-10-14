"""Step 2: plain text -> list of RawClause(number, heading, text).

Rules (all transparent regex, no ML):
  * A line that starts with a clause number begins a new clause. Accepted forms:
        "5. Payment"   "5) Payment"   "5.1 Text"   "Clause 5: ..."   "Section 5.2 ..."
  * Nested numbers (5.1, 5.2) become their own clauses; their `number` keeps the dots.
  * Lettered / roman sub-items "(a)", "(i)" stay INSIDE the clause they belong to.
  * Short title-like text after the number is the heading; the body follows on later lines,
    or after ":" / " - " on the same line.
  * Text before the first numbered clause (title, parties preamble) is returned separately.
  * If no numbering exists at all, fall back to blank-line separated paragraphs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import config
from .errors import NoClausesFoundError

_KEYWORD = r"(?:clause|section|article)"
# Number forms. Bare "30 days" must NOT match, so a plain integer needs "." or ")" after it.
_START = re.compile(
    rf"""^\s*
    (?:
        (?P<kw>{_KEYWORD})\s+(?P<n1>\d{{1,{config.MAX_NUMBER_DIGITS}}}(?:\.\d+)*)[.):]?   # Clause 5 / Section 5.2
      | (?P<n2>\d{{1,{config.MAX_NUMBER_DIGITS}}}(?:\.\d+)+)[.)]?                         # 5.1  5.1.2
      | (?P<n3>\d{{1,{config.MAX_NUMBER_DIGITS}}})[.)]                                    # 5.  5)
    )
    (?:\s+|$)(?P<rest>.*)$""",
    re.I | re.X,
)
_SUBITEM = re.compile(r"^\s*\(?([a-z]|[ivx]{1,4})\)\s+", re.I)
_SPLIT_HEADING = re.compile(r"^(?P<h>[^:–—\-.]{2,60}?)\s*(?::|\s[–—-]\s|\.\s)\s*(?P<b>\S.*)$")


@dataclass
class RawClause:
    number: str
    heading: str
    text: str


@dataclass
class SegmentResult:
    clauses: list[RawClause] = field(default_factory=list)
    preamble: str = ""
    warnings: list[str] = field(default_factory=list)


def _looks_like_heading(s: str) -> bool:
    words = s.split()
    if not words or len(words) > config.MAX_HEADING_WORDS:
        return False
    if s.rstrip().endswith((".", ";", ",")):
        return False
    return True


def _title_case_ish(s: str) -> bool:
    words = [w for w in re.findall(r"[A-Za-z]+", s)]
    if not words:
        return False
    caps = sum(1 for w in words if w[0].isupper() or w.lower() in {"of", "and", "the", "for", "to", "in", "on", "or"})
    return caps / len(words) >= 0.75


def segment(text: str) -> SegmentResult:
    lines = [l for l in text.split("\n")]
    result = SegmentResult()
    current: dict | None = None
    preamble: list[str] = []
    last_top: int | None = None   # highest top-level number seen so far

    def flush():
        nonlocal current
        if current is None:
            return
        body = " ".join(p for p in current["body"] if p).strip()
        heading = current["heading"].strip()
        if not body:               # clause with only a heading (parent of 5.1, 5.2 ...)
            body = heading
        result.clauses.append(RawClause(current["number"], heading, re.sub(r"\s+", " ", body)))
        current = None

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        m = _START.match(stripped)
        # a "(a)" line is never a new top-level clause; also reject if it looks like a sentence
        # continuation of a wrapped line ("... Clause 5 applies") -> only accept if keyword form
        # starts the line AND is followed by text that is not a lowercase continuation.
        if m and m.group("kw") and current is not None:
            rest = (m.group("rest") or "").strip()
            if rest[:1].islower():
                m = None
        # NLP-EX-07: "1. the services will ..." inside clause 2.1 is a list item, not a new clause.
        # Only a bare "n." that does not move forward AND continues in lower case is absorbed.
        if m and m.group("n3") and current is not None and last_top is not None:
            if int(m.group("n3")) <= last_top and (m.group("rest") or "").strip()[:1].islower():
                m = None
        if m:
            flush()
            number = m.group("n1") or m.group("n2") or m.group("n3")
            last_top = int(number.split(".")[0])
            rest = (m.group("rest") or "").strip()
            heading, body = "", rest
            if rest:
                sh = _SPLIT_HEADING.match(rest)
                if _looks_like_heading(rest) and (_title_case_ish(rest) or _next_is_body(lines, idx)):
                    heading, body = rest, ""
                elif sh and _looks_like_heading(sh.group("h")) and _title_case_ish(sh.group("h")):
                    heading, body = sh.group("h").strip(), sh.group("b").strip()
            current = {"number": number, "heading": heading, "body": [body] if body else []}
        elif current is None:
            preamble.append(stripped)
        else:
            current["body"].append(stripped)
    flush()
    result.preamble = " ".join(preamble)

    if not result.clauses:
        result = _fallback_paragraphs(text, result)
    _drop_toc_entries(result)
    _check_numbers(result)
    return result


_PAGE_TAIL = re.compile(r"^(?P<h>.*?\S)\s+\d{1,3}$")


def _norm_heading(h: str) -> str:
    m = _PAGE_TAIL.match(h.strip())
    return re.sub(r"[^a-z0-9]+", " ", (m.group("h") if m else h).lower()).strip()


def _drop_toc_entries(result: SegmentResult) -> None:
    """NLP-EX-06: \"2. Licenses 13\" (heading + page number) is a table-of-contents entry when the same
    number appears again LATER with the same heading. Both conditions are required, so a real
    heading that merely ends in a number (\"1. Term 3\") is never dropped."""
    cl = result.clauses
    drop = set()
    for i, c in enumerate(cl):
        if not c.heading or not _PAGE_TAIL.match(c.heading.strip()):
            continue
        key = _norm_heading(c.heading)
        if key and any(d.number == c.number and d.heading and _norm_heading(d.heading) == key for d in cl[i + 1:]):
            drop.add(i)
    if drop:
        result.clauses = [c for i, c in enumerate(cl) if i not in drop]
        result.warnings.append(f"Ignored {len(drop)} table-of-contents entries.")


def _next_is_body(lines: list[str], idx: int) -> bool:
    """True if the next non-empty line is body text (not another clause number)."""
    for nxt in lines[idx + 1:]:
        s = nxt.strip()
        if not s:
            continue
        return not _START.match(s) or bool(_SUBITEM.match(s))
    return False


def _fallback_paragraphs(text: str, result: SegmentResult) -> SegmentResult:
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paras:
        raise NoClausesFoundError("No clauses could be found in the text.")
    result.warnings.append("No clause numbering detected; split by paragraphs instead. Numbers are sequential guesses.")
    result.clauses = [RawClause(str(i), "", p) for i, p in enumerate(paras, 1)]
    result.preamble = ""
    return result


def _check_numbers(result: SegmentResult) -> None:
    seen: dict[str, int] = {}
    for c in result.clauses:
        seen[c.number] = seen.get(c.number, 0) + 1
    dups = sorted(n for n, k in seen.items() if k > 1)
    if dups:
        result.warnings.append(f"Duplicate clause numbers found (malformed numbering?): {', '.join(dups)}")
    top = [int(c.number) for c in result.clauses if "." not in c.number]
    gaps = [b for a, b in zip(top, top[1:]) if b != a + 1 and b > a]
    if gaps:
        result.warnings.append(f"Gaps in top-level numbering before clause(s): {gaps}")
