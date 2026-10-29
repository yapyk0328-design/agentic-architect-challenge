## handle the long content into smaller chunks solve the ai cannot handle too long content
"""Bounded long-text chunking for map-reduce summarization."""

from __future__ import annotations


def chunk_text(
    text: str,
    *,
    max_words: int = 1_200,
    overlap_words: int = 100,
) -> list[str]:
    """Split text into overlapping word-bounded chunks."""

    if max_words <= 0:
        raise ValueError("max_words must be greater than zero.")
    if overlap_words < 0 or overlap_words >= max_words:
        raise ValueError("overlap_words must be between zero and max_words - 1.")

    words = text.split()
    if not words:
        return []
    if len(words) <= max_words:
        return [" ".join(words)]

    chunks: list[str] = []
    step = max_words - overlap_words
    for start in range(0, len(words), step):
        chunk_words = words[start : start + max_words]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        if start + max_words >= len(words):
            break

    return chunks

