"""Command-line interface for the Part 2 implementation."""

from __future__ import annotations

import argparse
import json
import os
import sys

from .exceptions import WebSummarizerError
from .fetcher import BrowserFetcher, StaticFetcher
from .service import WebSummaryService
from .summarizers import ExtractiveSummarizer, OpenAISummarizer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely scrape and concisely summarize a webpage."
    )
    parser.add_argument("url", help="Public HTTP(S) webpage to summarize")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use the deterministic extractive summarizer instead of an API",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Disable Playwright fallback for JavaScript-rendered pages",
    )
    parser.add_argument(
        "--max-summary-words",
        type=int,
        default=150,
        help="Maximum final summary length (default: 150)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="OpenAI model; defaults to OPENAI_MODEL from the environment",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    args = build_parser().parse_args(argv)
    if args.max_summary_words <= 0:
        print("error: --max-summary-words must be greater than zero", file=sys.stderr)
        return 2

    try:
        if args.offline:
            summarizer = ExtractiveSummarizer()
        else:
            summarizer = OpenAISummarizer(
                model=args.model or os.getenv("OPENAI_MODEL", "")
            )

        service = WebSummaryService(
            static_fetcher=StaticFetcher(),
            browser_fetcher=None if args.no_browser else BrowserFetcher(),
            summarizer=summarizer,
            max_summary_words=args.max_summary_words,
        )
        result = service.summarize_url(args.url)
    except WebSummarizerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

