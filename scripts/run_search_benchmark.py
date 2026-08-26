#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared_search.gateway import default_gateway  # noqa: E402
from shared_search.models import SearchQuery, SearchResult  # noqa: E402


def load_cases(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("benchmark file must be a non-empty JSON array")
    ids: set[str] = set()
    for case in payload:
        if not isinstance(case, dict):
            raise ValueError("every benchmark case must be an object")
        case_id = str(case.get("id") or "")
        query = str(case.get("query") or "")
        groups = case.get("expected_term_groups")
        if not case_id or case_id in ids:
            raise ValueError(f"missing or duplicate case id: {case_id!r}")
        if not query.strip():
            raise ValueError(f"case {case_id}: query is empty")
        if not isinstance(groups, list) or not groups or any(not isinstance(g, list) or not g for g in groups):
            raise ValueError(f"case {case_id}: expected_term_groups must contain non-empty lists")
        ids.add(case_id)
    return payload


def result_text(result: SearchResult) -> str:
    content = result.content.text if result.content else ""
    return f"{result.title}\n{result.snippet}\n{content}".casefold()


def matches(result: SearchResult, case: dict) -> bool:
    text = result_text(result)
    groups = case["expected_term_groups"]
    terms_ok = all(any(str(term).casefold() in text for term in group) for group in groups)
    domains = [str(item).casefold().lstrip(".") for item in case.get("expected_domain_suffixes", [])]
    if not domains:
        return terms_ok
    host = (urlparse(result.url).hostname or "").casefold()
    domain_ok = any(host == domain or host.endswith("." + domain) for domain in domains)
    return terms_ok and domain_ok


def first_match_rank(results: list[SearchResult], case: dict) -> int | None:
    for index, result in enumerate(results, start=1):
        if matches(result, case):
            return index
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Shared Search Gateway benchmark corpus")
    parser.add_argument("--cases", default=str(ROOT / "benchmarks/shared_search_cases_v1.json"))
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--enrich-top", type=int, default=2)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    cases = load_cases(Path(args.cases))
    if args.validate_only:
        print(json.dumps({"valid": True, "cases": len(cases)}, ensure_ascii=False))
        return 0

    gateway = default_gateway()
    observations: list[dict] = []

    for case in cases:
        query = SearchQuery(
            query=case["query"],
            limit=args.limit,
            consumer=case.get("domain", "generic"),
            preferred_domains=tuple(case.get("preferred_domains", [])),
            enrich_top=min(args.enrich_top, args.limit),
        )
        started = time.perf_counter()
        error = None
        results: list[SearchResult] = []
        try:
            results = gateway.search(query)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        rank = first_match_rank(results, case) if results else None
        reader_success = sum(1 for result in results[: query.enrich_top] if result.content is not None)
        engines = sorted({engine for result in results for engine in result.engines})
        row = {
            "id": case["id"],
            "domain": case.get("domain", "generic"),
            "latency_ms": latency_ms,
            "match_rank": rank,
            "top1": rank == 1,
            "top3": rank is not None and rank <= 3,
            "top5": rank is not None and rank <= 5,
            "result_count": len(results),
            "reader_success": reader_success,
            "engines": engines,
            "error": error,
        }
        observations.append(row)
        print(json.dumps(row, ensure_ascii=False))

    latencies = [row["latency_ms"] for row in observations]
    total = len(observations)
    summary = {
        "summary": True,
        "cases": total,
        "top1_rate": round(sum(row["top1"] for row in observations) / total, 4),
        "top3_rate": round(sum(row["top3"] for row in observations) / total, 4),
        "top5_rate": round(sum(row["top5"] for row in observations) / total, 4),
        "error_rate": round(sum(row["error"] is not None for row in observations) / total, 4),
        "latency_ms_median": round(statistics.median(latencies), 2),
        "latency_ms_mean": round(statistics.mean(latencies), 2),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
