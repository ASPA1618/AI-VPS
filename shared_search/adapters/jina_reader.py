from __future__ import annotations

import ipaddress
import os
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from ..models import PageContent


def _validate_public_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("reader accepts only absolute http/https URLs")
    host = parsed.hostname.casefold()
    if host == "localhost" or host.endswith(".localhost"):
        raise ValueError("local URLs are not allowed")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return
    if not address.is_global:
        raise ValueError("private, loopback and link-local IP URLs are not allowed")


class JinaReader:
    """No-account page-to-markdown adapter using r.jina.ai.

    The no-key endpoint is intentionally rate-limited; callers should enrich
    only the highest-ranked results and gracefully continue when it is unavailable.
    """

    def __init__(self, endpoint: str | None = None, timeout: float = 20.0) -> None:
        self.endpoint = (endpoint or os.getenv("SEARCH_GATEWAY_JINA_READER_URL") or "https://r.jina.ai").rstrip("/")
        self.timeout = timeout

    def read(self, url: str, max_chars: int = 12000) -> PageContent:
        _validate_public_http_url(url)
        request = Request(
            f"{self.endpoint}/{url}",
            headers={
                "Accept": "text/plain",
                "User-Agent": "SharedSearchGateway/1.0",
                "X-Return-Format": "markdown",
            },
        )
        with urlopen(request, timeout=self.timeout) as response:
            text = response.read(max_chars + 1).decode("utf-8", errors="replace")
        if len(text) > max_chars:
            text = text[:max_chars]
        return PageContent(url=url, text=text, provider="jina-reader")
