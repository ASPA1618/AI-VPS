# Shared Search Gateway V1

## Decision

Search is a shared infrastructure capability, not an ASPA-specific component.
The same gateway is intended for **Personal Agent** and **ASPA**. Domain logic
is supplied by the consumer as policy; the shared core must not contain VIN,
customer, automotive, device or personal-data assumptions.

## Zero-participation / zero-registration baseline

V1 intentionally uses only components that require no new user account, card,
API key or manual registration:

1. **SearXNG self-hosted** for metasearch.
2. Built-in no-key engines, currently enabled explicitly: Brave, DuckDuckGo,
   Startpage, Qwant and Mojeek.
3. **Jina Reader (`r.jina.ai`)** as best-effort page-to-markdown enrichment
   without an API key.

Jina Search (`s.jina.ai`) is not part of the zero-key baseline because its
no-key search endpoint is blocked. Mwmbl's developer API is not part of V1
because its current developer flow includes sign-up/API-key management.
Exa can remain an external discovery provider where already available, but the
shared zero-registration core must not depend on Exa credentials.

## Runtime boundary

```text
Personal Agent -----------\
                           -> Shared Search Gateway -> SearXNG -> no-key engines
ASPA Search/Knowledge ----/           |
                                      +-> Jina Reader (top-N enrichment only)
```

The Docker Compose contract publishes only the gateway on host loopback
`127.0.0.1:8877`. SearXNG is reachable only on the Compose network. If remote
access is later needed, it must be exposed through the existing authenticated
Universal HTTPS/Tunnel facade rather than publishing this service directly.

## API contract

- `GET /health`
- `GET /v1/capabilities`
- `POST /v1/search`
- `POST /v1/read`

Example search body:

```json
{
  "query": "systemd user service restart semantics",
  "consumer": "personal-agent",
  "limit": 10,
  "preferred_domains": ["freedesktop.org"],
  "enrich_top": 2
}
```

ASPA can pass automotive/OEM preferred domains in exactly the same contract
without changing the gateway implementation.

## Trust and ranking

The shared gateway performs only generic ranking: upstream score, lexical
coverage, engine diversity and caller-provided domain preference/weight.
Trust tiers such as `OEM manual > dealer > catalog > marketplace > forum` are
ASPA policy and belong above this module. Personal Agent can independently
prefer official project or OS documentation.

## Failure model

- Search engines are individually subject to anti-bot changes and throttling.
  SearXNG provides engine diversity; no single scraped engine is authoritative.
- Jina Reader no-key access is rate-limited. Enrichment is best-effort and a
  reader failure never discards the search result.
- The gateway returns provenance (`provider`, `engines`, scores and metadata)
  so consumers can retain evidence and detect conflicts.

## Identity boundary

No GitHub email, login, repository owner, API token or user-specific credential
is embedded in runtime code. Repository writes are performed using the current
GitHub connector permissions. This keeps the module independent of retired or
secondary GitHub accounts.

## Next integration slice

1. Deploy the Compose bundle on the shared VPS/WSL execution plane.
2. Expose bounded `search`/`read` capabilities through the existing Universal
   HTTPS/Tunnel facade rather than adding another public connector.
3. Add consumer policies: Personal Agent official-doc ranking and ASPA
   OEM/fitment/fluid source tiers.
4. Run the benchmark corpus and record top-1/top-3 hit rate, latency, source
   tier, reader success and per-provider failure rate.
