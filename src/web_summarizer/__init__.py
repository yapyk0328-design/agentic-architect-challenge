"""Reliable webpage scraping and concise summarization."""

from .models import FetchResult, SummaryResult
from .service import WebSummaryService

__all__ = ["FetchResult", "SummaryResult", "WebSummaryService"]

