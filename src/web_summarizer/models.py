"""Typed data exchanged between scraping and summarization components."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FetchResult:
    """HTML returned by one of the fetching strategies."""

    url: str
    html: str
    method: str
    status_code: int
    content_type: str


@dataclass(frozen=True, slots=True)
class SummaryResult:
    """Final response returned to the CLI or a future API layer."""

    url: str
    summary: str
    fetch_method: str
    source_word_count: int
    chunk_count: int
    summary_word_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "url": self.url,
            "summary": self.summary,
            "fetch_method": self.fetch_method,
            "source_word_count": self.source_word_count,
            "chunk_count": self.chunk_count,
            "summary_word_count": self.summary_word_count,
        }

