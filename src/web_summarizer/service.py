"""End-to-end orchestration for scraping and summarization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .chunking import chunk_text
from .exceptions import ContentExtractionError
from .extractor import extract_main_content, is_sufficient_content
from .guardrails import (
    count_words,
    enforce_summary_guardrail,
    guardrail_violations,
)
from .models import FetchResult, SummaryResult
from .summarizers import TextSummarizer


class Fetcher(Protocol):
    def fetch(self, url: str) -> FetchResult:
        """Fetch a webpage and return its HTML."""


@dataclass(slots=True)
class WebSummaryService:
    """Coordinate static fetch, browser fallback, extraction, and summarization."""

    static_fetcher: Fetcher
    summarizer: TextSummarizer
    browser_fetcher: Fetcher | None = None
    chunk_words: int = 1_200
    chunk_overlap_words: int = 100
    partial_summary_words: int = 180
    max_summary_words: int = 150
    max_summary_bullets: int = 5

    def _fetch_and_extract(self, url: str) -> tuple[FetchResult, str]:
        result = self.static_fetcher.fetch(url)
        text = extract_main_content(result.html, url=result.url)

        if is_sufficient_content(text):
            return result, text

        if self.browser_fetcher is None:
            raise ContentExtractionError(
                "Static extraction returned too little content and browser fallback "
                "is disabled."
            )

        browser_result = self.browser_fetcher.fetch(result.url)
        browser_text = extract_main_content(browser_result.html, url=browser_result.url)
        if not is_sufficient_content(browser_text):
            raise ContentExtractionError(
                "The page did not contain enough readable content after browser rendering."
            )
        return browser_result, browser_text

    def _summarize_chunks(self, chunks: list[str]) -> str:
        if len(chunks) == 1:
            return self.summarizer.summarize(
                chunks[0],
                max_words=self.max_summary_words,
                purpose="direct",
            )

        partials = [
            self.summarizer.summarize(
                chunk,
                max_words=self.partial_summary_words,
                purpose="chunk",
            )
            for chunk in chunks
        ]
        numbered_partials = "\n\n".join(
            f"Section {index}:\n{partial}"
            for index, partial in enumerate(partials, start=1)
        )
        return self.summarizer.summarize(
            numbered_partials,
            max_words=self.max_summary_words,
            purpose="reduce",
        )

    def _apply_guardrail(self, draft: str) -> str:
        violations = guardrail_violations(
            draft,
            max_words=self.max_summary_words,
            max_bullets=self.max_summary_bullets,
        )

        if violations:
            draft = self.summarizer.summarize(
                draft,
                max_words=self.max_summary_words,
                purpose="compress",
            )

        return enforce_summary_guardrail(
            draft,
            max_words=self.max_summary_words,
            max_bullets=self.max_summary_bullets,
        )

    def summarize_url(self, url: str) -> SummaryResult:
        fetch_result, text = self._fetch_and_extract(url)
        chunks = chunk_text(
            text,
            max_words=self.chunk_words,
            overlap_words=self.chunk_overlap_words,
        )
        if not chunks:
            raise ContentExtractionError("The extracted webpage content was empty.")

        draft = self._summarize_chunks(chunks)
        final_summary = self._apply_guardrail(draft)

        return SummaryResult(
            url=fetch_result.url,
            summary=final_summary,
            fetch_method=fetch_result.method,
            source_word_count=count_words(text),
            chunk_count=len(chunks),
            summary_word_count=count_words(final_summary),
        )

