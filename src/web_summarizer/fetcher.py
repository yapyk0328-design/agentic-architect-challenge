## normal cpature content 
"""Static HTTP fetching with an optional browser-rendering fallback."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from .exceptions import FetchError, UnsupportedContentError
from .models import FetchResult
from .url_security import validate_public_http_url

_REDIRECT_CODES = {301, 302, 303, 307, 308}
_ALLOWED_CONTENT_TYPES = (
    "text/html",
    "application/xhtml+xml",
    "text/plain",
)


@dataclass(slots=True)
class StaticFetcher:
    """Fetch ordinary webpages without starting a full browser."""

    timeout_seconds: float = 15.0
    max_response_bytes: int = 5_000_000
    max_redirects: int = 3
    user_agent: str = "AgenticArchitectChallenge/1.0"

    def fetch(self, url: str) -> FetchResult:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - environment-specific
            raise FetchError("Install the 'httpx' dependency to fetch webpages.") from exc

        current_url = validate_public_http_url(url)
        timeout = httpx.Timeout(self.timeout_seconds)

        try:
            with httpx.Client(timeout=timeout, follow_redirects=False) as client:
                for redirect_number in range(self.max_redirects + 1):
                    current_url = validate_public_http_url(current_url)
                    with client.stream(
                        "GET",
                        current_url,
                        headers={
                            "User-Agent": self.user_agent,
                            "Accept": "text/html,application/xhtml+xml,text/plain",
                        },
                    ) as response:
                        if response.status_code in _REDIRECT_CODES:
                            if redirect_number >= self.max_redirects:
                                raise FetchError("The webpage exceeded the redirect limit.")
                            location = response.headers.get("location")
                            if not location:
                                raise FetchError("Redirect response did not include a location.")
                            current_url = urljoin(str(response.url), location)
                            continue

                        response.raise_for_status()
                        content_type = response.headers.get("content-type", "").lower()
                        if not any(item in content_type for item in _ALLOWED_CONTENT_TYPES):
                            raise UnsupportedContentError(
                                f"Unsupported content type: {content_type or 'unknown'}"
                            )

                        declared_size = int(response.headers.get("content-length", "0") or 0)
                        if declared_size > self.max_response_bytes:
                            raise FetchError("The webpage exceeds the configured size limit.")

                        body = bytearray()
                        for data in response.iter_bytes():
                            body.extend(data)
                            if len(body) > self.max_response_bytes:
                                raise FetchError(
                                    "The webpage exceeded the configured size limit while downloading."
                                )

                        encoding = response.encoding or "utf-8"
                        html = bytes(body).decode(encoding, errors="replace")
                        return FetchResult(
                            url=str(response.url),
                            html=html,
                            method="static-http",
                            status_code=response.status_code,
                            content_type=content_type,
                        )
        except (UnsupportedContentError, FetchError):
            raise
        except httpx.HTTPError as exc:
            raise FetchError(f"Unable to fetch webpage: {exc}") from exc

        raise FetchError("Unable to fetch webpage.")


@dataclass(slots=True)
class BrowserFetcher:
    """Render JavaScript-heavy pages using headless Chromium."""

    timeout_ms: int = 20_000

    def fetch(self, url: str) -> FetchResult:
        try:
            from playwright.sync_api import Error as PlaywrightError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # pragma: no cover - environment-specific
            raise FetchError(
                "Browser fallback requires the 'playwright' package and Chromium."
            ) from exc

        safe_url = validate_public_http_url(url)
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="AgenticArchitectChallenge/1.0"
                )
                page = context.new_page()
                response = page.goto(
                    safe_url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout_ms,
                )
                html = page.content()
                final_url = validate_public_http_url(page.url)
                status_code = response.status if response else 200
                browser.close()
        except PlaywrightError as exc:
            raise FetchError(f"Browser rendering failed: {exc}") from exc

        return FetchResult(
            url=final_url,
            html=html,
            method="playwright",
            status_code=status_code,
            content_type="text/html",
        )

