# ASPA Agent Runtime Test Matrix v1

Status: Draft / deferred architecture direction

## Purpose

ASPA needs a future test matrix for all agent and connector execution paths before relying on autonomous or semi-autonomous work.

The test matrix must verify that each runtime can be reached, identified, authorized, observed and safely bounded.

## Runtime surfaces

- WSL ASPA agent
- Windows AI agent
- VPS relay/API
- OpenAI API key and models
- ChatGPT MCP connectors
- GitHub connector
- Local MCP endpoints 8011 / 8012 / 8013 / 8020
- Future OpenAI Agents SDK layer
- Future LangGraph workflow layer

## Core test groups

1. Identity
- confirm which agent is running;
- confirm host: WSL / Windows / VPS / ChatGPT;
- confirm environment name and safe mode.

2. Connectivity
- ping/healthcheck each endpoint;
- check GitHub access;
- check VPS reachability;
- check WSL availability;
- check Windows agent availability.

3. Authorization
- verify secrets are loaded from approved env/vault only;
- never expose API keys in logs or ChatGPT;
- verify read/write/destructive permissions are separated.

4. OpenAI API
- verify API key exists without printing it;
- list/confirm allowed model families only when safe;
- test small non-sensitive request;
- record latency, cost class and failure mode.

5. MCP and connector routing
- ChatGPT connector can create/read GitHub issues/docs;
- MCP 8011 handles admin/local operations only when WSL online;
- MCP 8012 remains read-only;
- MCP 8013 handles owner workspace/file visibility;
- MCP 8020 handles dev facade/status.

6. Execution safety
- no shell execution from untrusted webhook;
- WSL agent claims one task at a time by default;
- destructive actions require explicit approval;
- commit/push only when requested or policy allows.

7. Observability
- every test writes compact status;
- logs are rate-limited;
- failures produce evidence without secrets;
- disk/log growth checks are included.

## Expected result format

```text
surface: WSL ASPA agent
status: pass / fail / degraded / unavailable
host: WSL
capabilities: read / write / exec / git / mcp
last_checked: timestamp
risk: low / medium / high
notes: compact evidence
```

## Future command

A future owner command like:

```text
проверь агентов
```

should run the safe read-only subset first and report which execution paths are available.

## Related

- ASPA System Sync Relay Plane v1
- ASPA Idea Graph v1
- ASPA Storage Safety v1
- ASPA Cross Matrix and Deterministic Part Lookup v1
