from __future__ import annotations

from dataclasses import dataclass, field, replace
from urllib.parse import urlparse

from .models import SearchQuery, SearchResult


def _hostname(url: str) -> str:
    return (urlparse(url).hostname or "").lower().rstrip(".")


def _matches_domain(host: str, domain: str) -> bool:
    domain = domain.lower().strip().lstrip(".").rstrip(".")
    return bool(domain) and (host == domain or host.endswith("." + domain))


@dataclass(frozen=True, slots=True)
class SearchPolicy:
    """Consumer-neutral ranking policy.

    ASPA and Personal Agent should pass their own preferred/blocked domains or
    domain weights. The shared layer intentionally contains no automotive,
    customer, VIN, device or personal-data rules.
    """

    preferred_domains: tuple[str, ...] = ()
    blocked_domains: tuple[str, ...] = ()
    domain_weights: dict[str, float] = field(default_factory=dict)
    require_https: bool = False

    def rank(self, query: SearchQuery, results: list[SearchResult]) -> list[SearchResult]:
        terms = {part.casefold() for part in query.query.split() if len(part) > 1}
        preferred = self.preferred_domains + query.preferred_domains
        ranked: list[SearchResult] = []

        for result in results:
            host = _hostname(result.url)
            if any(_matches_domain(host, domain) for domain in self.blocked_domains):
                continue
            if self.require_https and not result.url.lower().startswith("https://"):
                continue

            haystack = f"{result.title} {result.snippet}".casefold()
            term_hits = sum(1 for term in terms if term in haystack)
            lexical = term_hits / max(len(terms), 1)
            diversity = min(len(set(result.engines)), 4) * 0.10
            preferred_bonus = 1.5 if any(_matches_domain(host, d) for d in preferred) else 0.0
            domain_bonus = sum(
                weight for domain, weight in self.domain_weights.items() if _matches_domain(host, domain)
            )
            score = float(result.provider_score) + lexical + diversity + preferred_bonus + domain_bonus
            ranked.append(replace(result, rank_score=round(score, 6)))

        return sorted(ranked, key=lambda item: item.rank_score, reverse=True)
