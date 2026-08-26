from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .gateway import default_gateway
from .models import SearchQuery


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    gateway = default_gateway()
    server_version = "SharedSearchGateway/1.0"

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(200, {"status": "ok"})
            return
        if self.path == "/v1/capabilities":
            self._send(
                200,
                {
                    "search": ["searxng"],
                    "reader": ["jina-reader"] if self.gateway.reader else [],
                    "accounts_required": False,
                    "consumer_neutral": True,
                },
            )
            return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self._read_json()
            if self.path == "/v1/search":
                query = SearchQuery(
                    query=str(payload.get("query") or ""),
                    limit=int(payload.get("limit", 10)),
                    language=str(payload.get("language", "auto")),
                    categories=tuple(payload.get("categories") or ["general"]),
                    consumer=str(payload.get("consumer", "generic")),
                    preferred_domains=tuple(payload.get("preferred_domains") or []),
                    enrich_top=int(payload.get("enrich_top", 0)),
                )
                results = self.gateway.search(query)
                self._send(200, {"query": query.query, "consumer": query.consumer, "results": [r.to_dict() for r in results]})
                return
            if self.path == "/v1/read":
                page = self.gateway.read_url(
                    str(payload.get("url") or ""),
                    max_chars=int(payload.get("max_chars", 12000)),
                )
                self._send(200, page.to_dict())
                return
            self._send(404, {"error": "not_found"})
        except (TypeError, ValueError) as exc:
            self._send(400, {"error": "bad_request", "detail": str(exc)})
        except Exception as exc:
            self._send(502, {"error": "upstream_failure", "detail": f"{type(exc).__name__}: {exc}"})

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 1_000_000:
            raise ValueError("invalid Content-Length")
        parsed = json.loads(self.rfile.read(length))
        if not isinstance(parsed, dict):
            raise ValueError("JSON body must be an object")
        return parsed

    def _send(self, status: int, payload: Any) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        if os.getenv("SEARCH_GATEWAY_ACCESS_LOG", "0") == "1":
            super().log_message(fmt, *args)


def main() -> None:
    host = os.getenv("SEARCH_GATEWAY_HOST", "127.0.0.1")
    port = int(os.getenv("SEARCH_GATEWAY_PORT", "8877"))
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
