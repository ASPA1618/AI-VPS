from __future__ import annotations

import os
from dataclasses import replace
from typing import Protocol

from .adapters import JinaReader, SearxngSearchAdapter
from .models import PageContent, SearchQuery, SearchResult
from .policy import SearchPolicy


class SearchAdapter(Protocol):
    def search(self, query: SearchQuery) -> list[SearchResult]: ...


class ReaderAdapter(Protocol):
    def read(self, url: str, max_chars: int = 12000) -> PageContent: ...


class SearchGateway:
    def __init__(
        self,
        search_adapter: SearchAdapter,
        reader: ReaderAdapter | None = None,
        policy: SearchPolicy | None = None,
    ) -> None:
        self.search_adapter = search_adapter
        self.reader = reader
        self.policy = policy or SearchPolicy()

    def search(self, query: SearchQuery) -> list[SearchResult]:
        ranked = self.policy.rank(query, self.search_adapter.search(query))[: query.limit]
        if not self.reader or query.enrich_top <= 0:
            return ranked

        enriched: list[SearchResult] = []
        for index, result in enumerate(ranked):
            if index >= query.enrich_top:
                enriched.append(result)
                continue
            try:
                content = self.reader.read(result.url)
                enriched.append(replace(result, content=content))
            except Exception as exc:  # enrichment is explicitly best-effort
                metadata = dict(result.metadata)
                metadata["reader_error"] = f"{type(exc).__name__}: {exc}"
                enriched.append(replace(result, metadata=metadata))
        return enriched

    def read_url(self, url: str, max_chars: int = 12000) -> PageContent:
        if not self.reader:
            raise RuntimeError("reader is disabled")
        return self.reader.read(url, max_chars=max_chars)


def default_gateway(policy: SearchPolicy | None = None) -> SearchGateway:
    reader_enabled = os.getenv("SEARCH_GATEWAY_JINA_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
    return SearchGateway(
        search_adapter=SearxngSearchAdapter(),
        reader=JinaReader() if reader_enabled else None,
        policy=policy,
    )
