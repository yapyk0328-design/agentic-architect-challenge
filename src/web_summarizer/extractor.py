## capture the content inside the pages and remove unnecessary content
"""Main-content extraction with a standard-library safety fallback."""

from __future__ import annotations

import html as html_module
import re
from html.parser import HTMLParser


class _VisibleTextParser(HTMLParser):
    """Small fallback extractor used when Trafilatura is unavailable."""

    _ignored_tags = {
        "script",
        "style",
        "noscript",
        "svg",
        "nav",
        "footer",
        "header",
        "form",
    }

    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self._ignored_tags:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._ignored_tags and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth == 0 and data.strip():
            self._parts.append(data.strip())

    @property
    def text(self) -> str:
        return "\n".join(self._parts)


def normalize_text(text: str) -> str:
    """Normalize whitespace while retaining paragraph boundaries."""

    text = html_module.unescape(text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def extract_main_content(html: str, *, url: str | None = None) -> str:
    """Extract a page's main readable text.

    Trafilatura is preferred because it removes common webpage boilerplate. The
    fallback keeps the demo and unit tests usable in a minimal environment.
    """

    extracted: str | None = None
    try:
        from trafilatura import extract

        extracted = extract(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            output_format="txt",
            favor_precision=True,
        )
    except ImportError:
        extracted = None

    if not extracted:
        parser = _VisibleTextParser()
        parser.feed(html)
        extracted = parser.text

    return normalize_text(extracted)


def is_sufficient_content(
    text: str,
    *,
    min_words: int = 80,
    min_characters: int = 400,
) -> bool:
    """Return whether extraction produced enough content to summarize."""

    return len(text) >= min_characters and len(text.split()) >= min_words

