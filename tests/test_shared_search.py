from __future__ import annotations

import unittest

from shared_search.gateway import SearchGateway
from shared_search.models import PageContent, SearchQuery, SearchResult
from shared_search.policy import SearchPolicy


class FakeSearch:
    def search(self, query: SearchQuery) -> list[SearchResult]:
        return [
            SearchResult(
                title="Community mirror result",
                url="https://example.net/item",
                snippet=query.query,
                engines=("duckduckgo",),
                provider_score=1.0,
            ),
            SearchResult(
                title="Official documentation",
                url="https://docs.example.com/item",
                snippet=query.query,
                engines=("brave", "startpage"),
                provider_score=0.5,
            ),
        ]


class FakeReader:
    def read(self, url: str, max_chars: int = 12000) -> PageContent:
        return PageContent(url=url, text=f"content:{url}")


class SharedSearchTests(unittest.TestCase):
    def test_consumer_preferred_domain_changes_ranking(self) -> None:
        gateway = SearchGateway(FakeSearch(), policy=SearchPolicy())
        results = gateway.search(
            SearchQuery(query="test item", preferred_domains=("docs.example.com",))
        )
        self.assertEqual(results[0].url, "https://docs.example.com/item")

    def test_reader_enriches_only_requested_top_results(self) -> None:
        gateway = SearchGateway(FakeSearch(), reader=FakeReader())
        results = gateway.search(SearchQuery(query="test item", enrich_top=1))
        self.assertIsNotNone(results[0].content)
        self.assertIsNone(results[1].content)

    def test_query_bounds_are_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            SearchQuery(query="", limit=10)
        with self.assertRaises(ValueError):
            SearchQuery(query="x", limit=51)
        with self.assertRaises(ValueError):
            SearchQuery(query="x", enrich_top=11, limit=10)


if __name__ == "__main__":
    unittest.main()
