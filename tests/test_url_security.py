import socket

import pytest

from web_summarizer.exceptions import UnsafeURLError
from web_summarizer.url_security import validate_public_http_url


def resolver_for(address: str):
    def resolve(host: str, port: int, *, type: int):
        del host, type
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port))]

    return resolve


def test_allows_public_https_url():
    result = validate_public_http_url(
        "https://example.com/article",
        resolver=resolver_for("93.184.216.34"),
    )

    assert result == "https://example.com/article"


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/admin",
        "http://127.0.0.1/admin",
        "http://10.0.0.1/internal",
        "file:///etc/passwd",
    ],
)
def test_blocks_local_private_and_non_http_urls(url: str):
    with pytest.raises(UnsafeURLError):
        validate_public_http_url(url, resolver=resolver_for("127.0.0.1"))


def test_blocks_hostname_resolving_to_private_address():
    with pytest.raises(UnsafeURLError):
        validate_public_http_url(
            "https://internal.example",
            resolver=resolver_for("192.168.1.10"),
        )

