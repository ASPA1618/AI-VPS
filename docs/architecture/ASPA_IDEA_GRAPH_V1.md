# ASPA Idea Graph v1

Status: Draft / deferred architecture direction

## Purpose

ASPA must not store strategic ideas as isolated chat fragments or one-off notes. Ideas should become graph nodes that can be connected to architecture documents, GitHub issues, task packets, branches, PRs, commits, evidence and minilogs.

## Core graph

```text
Idea
  -> Architecture document
  -> GitHub Issue
  -> Task packet
  -> Branch / PR / Commit
  -> Evidence / minilog
  -> Done or deferred
```

## Why this matters

Linear chat history is fragile. A graph keeps durable relationships between:
- strategic directions;
- deferred implementation tasks;
- architecture documents;
- dependencies and blockers;
- approval gates;
- branches, commits and PRs;
- runtime evidence and reports.

## Initial node types

- Idea
- ArchitectureDirection
- DeferredTask
- ImplementationTask
- GitHubIssue
- ArchitectureDocument
- Branch
- PullRequest
- Commit
- Evidence
- Minilog
- ApprovalGate
- RuntimeStatus

## Initial ASPA graph nodes

- System Sync Relay Plane
- Phone-to-GitHub task intake
- VPS relay dashboard
- WSL online/offline monitor
- HTTP trigger bells / webhook intake
- OpenAI Agents SDK layer
- LangGraph long-running workflow layer
- Human Approval Runtime
- Minilog / evidence reporting
- Mobile GitHub workflow

## Rules

- GitHub repository documentation remains the canonical source for architecture.
- ChatGPT memory may only keep compact principles and pointers, not full graph state.
- GitHub Issues may represent deferred tasks and future implementation slices.
- Labels and structured fields must be deterministic enough for future VPS/WSL agents to parse without LLM interpretation.
- LLMs may help summarize, classify and propose links, but graph state must be stored in durable project artifacts.

## Deferred implementation sketch

1. Define a lightweight graph schema in repo docs.
2. Add a machine-readable `idea_graph.json` or `idea_graph.yaml` later.
3. Link architecture docs to GitHub issues.
4. Link issues to branches, PRs and commits.
5. Add minilog/evidence references after each run.
6. Add dashboard visualization later on VPS.

## Related files and issues

- `docs/architecture/ASPA_SYSTEM_SYNC_RELAY_PLANE_V1.md`
- GitHub Issue #1: Phone-to-GitHub task relay with VPS dashboard and WSL online executor
- GitHub Issue #2: Mobile GitHub workflow and Idea Graph for ASPA task intake
