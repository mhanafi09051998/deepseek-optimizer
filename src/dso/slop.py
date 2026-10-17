"""Detect low-value patterns that language models habitually emit."""

from __future__ import annotations

import re

CLICHES = [
    "it's important to note",
    "it is important to note",
    "it's worth noting",
    "it is worth noting",
    "delve into",
    "dive into",
    "in today's fast-paced",
    "comprehensive guide",
    "comprehensive solution",
    "seamless",
    "robust solution",
    "leverage",
    "game-changer",
    "unlock the",
    "let's break",
    "let me know if",
    "i hope this helps",
    "great question",
    "certainly!",
    "in conclusion",
    "here's a quick",
    "not only",
    "furthermore",
    "moreover",
]

PATTERNS = {
    "bold": re.compile(r"\*\*[^*\n]+\*\*"),
    "em_dash": re.compile(r"[\u2014\u2013]"),
    "spaced_hyphen": re.compile(r"(?<=\w) - (?=\w)"),
    "emoji": re.compile(r"[\U0001f300-\U0001faff\u2600-\u27bf]"),
    "heading": re.compile(r"^#{2,}\s", re.MULTILINE),
}

FENCE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]+`")


def strip_code(text: str) -> str:
    """Remove code blocks and inline code: syntax is not prose slop."""
    return INLINE_CODE.sub(" ", FENCE.sub(" ", text))


def analyze(texts: list[str]) -> dict:
    """Return slop markers and a normalized score for the given text parts."""
    prose = strip_code("\n".join(texts))
    lowered = prose.lower()
    words = len(re.findall(r"\b[\w'-]+\b", prose))

    markers: dict[str, int] = {}
    for name, pattern in PATTERNS.items():
        count = len(pattern.findall(prose))
        if count:
            markers[name] = count

    for phrase in CLICHES:
        count = lowered.count(phrase)
        if count:
            markers[phrase] = count

    total = sum(markers.values())
    per_1k = (total / words * 1000) if words else 0.0
    return {
        "words": words,
        "total": total,
        "per_1k_words": round(per_1k, 2),
        "markers": dict(sorted(markers.items(), key=lambda item: -item[1])),
    }


def format_report(result: dict) -> str:
    lines = [
        f"words: {result['words']}",
        f"markers: {result['total']} ({result['per_1k_words']} per 1k words)",
    ]
    for name, count in result["markers"].items():
        lines.append(f"  {count:>3}  {name}")
    return "\n".join(lines)
