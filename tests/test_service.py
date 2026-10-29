from dataclasses import dataclass

import pytest

from web_summarizer.exceptions import ContentExtractionError
from web_summarizer.models import FetchResult
from web_summarizer.service import WebSummaryService
from web_summarizer.summarizers import ExtractiveSummarizer


def article_html(word_count: int) -> str:
    article = " ".join(
        f"content-word-{index}." for index in range(word_count)
    )
    return f"<html><body><article><h1>Article</h1><p>{article}</p></article></body></html>"


@dataclass
class FakeFetcher:
    html: str
    method: str = "fake-static"
    calls: int = 0

    def fetch(self, url: str) -> FetchResult:
        self.calls += 1
        return FetchResult(
            url=url,
            html=self.html,
            method=self.method,
            status_code=200,
            content_type="text/html",
        )


def test_service_summarizes_long_content_in_multiple_chunks():
    service = WebSummaryService(
        static_fetcher=FakeFetcher(article_html(260)),
        summarizer=ExtractiveSummarizer(),
        browser_fetcher=None,
        chunk_words=100,
        chunk_overlap_words=10,
        partial_summary_words=30,
        max_summary_words=40,
    )

    result = service.summarize_url("https://example.com/article")

    assert result.chunk_count == 3
    assert result.summary_word_count <= 40
    assert result.fetch_method == "fake-static"


def test_service_uses_browser_when_static_extraction_is_too_short():
    static_fetcher = FakeFetcher("<html><body><p>Loading...</p></body></html>")
    browser_fetcher = FakeFetcher(article_html(100), method="fake-browser")
    service = WebSummaryService(
        static_fetcher=static_fetcher,
        browser_fetcher=browser_fetcher,
        summarizer=ExtractiveSummarizer(),
        max_summary_words=40,
    )

    result = service.summarize_url("https://example.com/dynamic")

    assert static_fetcher.calls == 1
    assert browser_fetcher.calls == 1
    assert result.fetch_method == "fake-browser"


def test_service_fails_safely_when_no_strategy_extracts_enough_content():
    service = WebSummaryService(
        static_fetcher=FakeFetcher("<html><body>Loading</body></html>"),
        browser_fetcher=FakeFetcher("<html><body>Still empty</body></html>"),
        summarizer=ExtractiveSummarizer(),
    )

    with pytest.raises(ContentExtractionError):
        service.summarize_url("https://example.com/empty")

