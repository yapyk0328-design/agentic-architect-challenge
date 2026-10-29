
"""Deterministic output checks applied after model generation."""

from __future__ import annotations

import re

_BULLET_PATTERN = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+", re.MULTILINE)
_SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")


def count_words(text: str) -> int:
    return len(text.split())


def count_bullets(text: str) -> int:
    return len(_BULLET_PATTERN.findall(text))


def guardrail_violations(
    text: str,
    *,
    max_words: int,
    max_bullets: int,
) -> list[str]:
    violations: list[str] = []
    if not text.strip():
        violations.append("summary is empty")
    if count_words(text) > max_words:
        violations.append(f"summary exceeds {max_words} words")
    if count_bullets(text) > max_bullets:
        violations.append(f"summary exceeds {max_bullets} bullet points")
    return violations


def _limit_bullets(text: str, max_bullets: int) -> str:
    bullet_count = 0
    retained: list[str] = []
    for line in text.splitlines():
        if _BULLET_PATTERN.match(line):
            bullet_count += 1
            if bullet_count > max_bullets:
                continue
        retained.append(line)
    return "\n".join(retained).strip()


def _trim_to_complete_sentences(text: str, max_words: int) -> str:
    if count_words(text) <= max_words:
        return text.strip()

    sentences = _SENTENCE_PATTERN.split(text.strip())
    retained: list[str] = []
    current_words = 0
    for sentence in sentences:
        sentence_words = sentence.split()
        if current_words + len(sentence_words) > max_words:
            break
        retained.append(sentence)
        current_words += len(sentence_words)

    if retained:
        return " ".join(retained).strip()

    return " ".join(text.split()[:max_words]).strip()


def enforce_summary_guardrail(
    text: str,
    *,
    max_words: int = 150,
    max_bullets: int = 5,
) -> str:
    """Apply a deterministic final boundary after an LLM compression attempt."""

    limited = _limit_bullets(text.strip(), max_bullets)
    return _trim_to_complete_sentences(limited, max_words)

