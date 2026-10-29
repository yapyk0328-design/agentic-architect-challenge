"""Domain-specific exceptions for the webpage summarizer."""


class WebSummarizerError(Exception):
    """Base exception for expected application failures."""


class UnsafeURLError(WebSummarizerError):
    """Raised when a URL could access a local or private resource."""


class FetchError(WebSummarizerError):
    """Raised when a webpage cannot be fetched safely."""


class UnsupportedContentError(WebSummarizerError):
    """Raised when a response is not supported webpage content."""


class ContentExtractionError(WebSummarizerError):
    """Raised when meaningful main-page content cannot be extracted."""


class ConfigurationError(WebSummarizerError):
    """Raised when required runtime configuration is missing."""


class SummaryValidationError(WebSummarizerError):
    """Raised when a generated summary violates an output guardrail."""

