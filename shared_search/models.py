from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class SearchQuery:
    query: str
    limit: int = 10
    language: str = "auto"
    categories: tuple[str, ...] = ("general",)
    consumer: str = "generic"
    preferred_domains: tuple[str, ...] = ()
    enrich_top: int = 0

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("query must not be empty")
        if not 1 <= self.limit <= 50:
            raise ValueError("limit must be between 1 and 50")
        if not 0 <= self.enrich_top <= self.limit:
            raise ValueError("enrich_top must be between 0 and limit")


@dataclass(frozen=True, slots=True)
class PageContent:
    url: str
    text: str
    title: str | None = None
    provider: str = "jina-reader"

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "text": self.text,
            "provider": self.provider,
        }


@dataclass(frozen=True, slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    engines: tuple[str, ...] = ()
    provider: str = "searxng"
    provider_score: float = 0.0
    rank_score: float = 0.0
    content: PageContent | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "engines": list(self.engines),
            "provider": self.provider,
            "provider_score": self.provider_score,
            "rank_score": self.rank_score,
            "content": self.content.to_dict() if self.content else None,
            "metadata": self.metadata,
        }
