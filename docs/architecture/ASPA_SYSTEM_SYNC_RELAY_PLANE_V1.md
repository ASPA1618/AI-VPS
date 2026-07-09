# ASPA System Sync Relay Plane v1

Status: Draft

Goals:
- Deterministic task relay between ChatGPT, GitHub, VPS and WSL.
- Durable queue and boot synchronization.
- Human approval support.
- Minilog and audit trail.

Phases:
1. Deterministic relay plane.
2. OpenAI Agents SDK integration for planning, tool routing and tracing.
3. LangGraph for resumable long-running workflows.

Boot flow:
ChatGPT -> GitHub task -> VPS queue -> WSL boot -> MCP -> execution -> minilog -> report.
