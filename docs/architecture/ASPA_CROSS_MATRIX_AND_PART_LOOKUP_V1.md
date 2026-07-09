# ASPA Cross Matrix and Deterministic Part Lookup v1

Status: Draft / deferred architecture direction

## Purpose

ASPA needs a systematic cross-reference block for automotive parts. The goal is not only to collect supplier crosses, but to build a controlled cross matrix with depth, provenance, trust, query roles and optimization rules.

## Core principle

```text
Supplier crosses are signals. ASPA Cross Matrix is the controlled truth layer.
```

## Scope

This direction covers:
- catalog number normalization;
- brand and article interpretation;
- deterministic lookup by article/catalog number;
- cross matrix depth;
- confidence and provenance;
- source roles: supplier API, files, web, ChatGPT, MCP connectors, agents;
- formatted result output for operators and future storefront/search UI.

## Conceptual layers

```text
Raw input
  -> normalized article and brand candidates
  -> source-specific lookup
  -> raw supplier/catalog cross signals
  -> validation and confidence scoring
  -> Cross Matrix
  -> offer/search expansion
  -> formatted result envelope
```

## Cross depth

Depth must be explicit:
- depth 0: exact normalized article/brand match;
- depth 1: direct supplier/catalog cross;
- depth 2: validated analog/replacement through trusted source;
- depth 3: weak candidate, requires validation;
- blocked: unsafe or ambiguous cross.

## Deterministic lookup rule

Article lookup must be deterministic first. LLM may explain, classify or format, but must not be the source of truth for compatibility.

Deterministic core should handle:
- article cleaning;
- brand synonym mapping;
- supplier-specific article formats;
- direct exact search;
- cross expansion by configured depth;
- source priority;
- deduplication;
- evidence links;
- stable output ordering.

## Source roles

- Supplier API: live offers, stock, prices, supplier crosses when available.
- Supplier files: bulk cross tables, price files, historical evidence.
- TecDoc/catalog sources: validation and vehicle/part structure where available.
- Web search: auxiliary enrichment only, not compatibility truth.
- ChatGPT: operator interface, reasoning summary, formatting, gap analysis.
- MCP connectors: transport/control plane for GitHub, files, WSL/VPS tools.
- Agents: scheduled or on-demand processors that update candidates, evidence and reports.

## Optimization goals

- Avoid uncontrolled cross explosion.
- Cache normalized article lookups.
- Limit depth by query intent and confidence.
- Prefer exact and validated edges before weak expansion.
- Batch supplier calls where possible.
- Store changed-only history.
- Keep raw source payloads separate from interpreted and business-ready layers.

## Output envelope direction

Formatted result should separate:
- requested article;
- interpreted brand/article;
- exact matches;
- cross candidates by depth;
- confidence and source;
- offers and stock;
- price/ETA/logistics;
- warnings and ambiguity;
- evidence summary.

## Future work

1. Define Cross Matrix schema.
2. Define cross edge types and confidence rules.
3. Define source priority and depth caps.
4. Define deterministic article lookup contract.
5. Define formatted SearchResultEnvelope for cross-aware results.
6. Add performance/load budgets for cross expansion.
7. Add tests with known catalog numbers and supplier APIs.

Related:
- ASPA Idea Graph v1
- ASPA System Sync Relay Plane v1
- ASPA Storage Safety v1
