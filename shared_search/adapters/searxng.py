from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..models import SearchQuery, SearchResult


class SearxngSearchAdapter:
    def __init__(self, base_url: str | None = None, timeout: float = 12.0) -> None:
        self.base_url = (base_url or os.getenv("SEARCH_GATEWAY_SEARXNG_URL") or "http://127.0.0.1:8888").rstrip("/")
        self.timeout = timeout

    def search(self, query: SearchQuery) -> list[SearchResult]:
        params: dict[str, str] = {
            "q": query.query,
            "format": "json",
            "categories": ",".join(query.categories),
        }
        if query.language and query.language != "auto":
            params["language"] = query.language

        request = Request(
            f"{self.base_url}/search?{urlencode(params)}",
            headers={"Accept": "application/json", "User-Agent": "SharedSearchGateway/1.0"},
        )
        with urlopen(request, timeout=self.timeout) as response:
            payload = json.load(response)

        rows = payload.get("results") or []
        return [self._parse_result(row) for row in rows[: query.limit]]

    @staticmethod
    def _parse_result(row: dict[str, Any]) -> SearchResult:
        engines = row.get("engines") or []
        if isinstance(engines, str):
            engines = [engines]
        metadata = {
            key: row[key]
            for key in ("category", "publishedDate", "positions")
            if key in row and row[key] is not None
        }
        return SearchResult(
            title=str(row.get("title") or ""),
            url=str(row.get("url") or ""),
            snippet=str(row.get("content") or ""),
            engines=tuple(str(engine) for engine in engines),
            provider="searxng",
            provider_score=float(row.get("score") or 0.0),
            metadata=metadata,
        )
