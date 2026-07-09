# ASPA System Sync Relay Plane v1

Status: Draft

Goals:
- Deterministic task relay between ChatGPT, GitHub, VPS and WSL.
- Durable queue and boot synchronization.
- Human approval support.
- Minilog and audit trail.
- Explicit execution mode selection depending on whether the user's PC and WSL are online.

Core rule:
- When the user's PC is OFF or WSL is unavailable, VPS acts as the relay, durable queue holder, observer and lightweight coordinator.
- When the user's PC is ON and WSL is available, the local WSL ASPA agent becomes the preferred active executor for local repository work, MCP 8011/8012/8013/8020 operations, heavy processing and tasks requiring local files/tools.
- GitHub remains the durable cross-session handoff layer for tasks, architecture notes, branch state, commits, PRs and recovery checkpoints.
- VPS and WSL must synchronize before execution so tasks are not duplicated or silently lost.

Execution modes:
1. Phone-only / PC offline:
   ChatGPT -> GitHub task or note -> VPS relay queue -> wait for WSL resume or execute only safe VPS-side work.

2. PC ON / WSL available:
   ChatGPT -> GitHub task or connector command -> WSL ASPA agent -> local MCP/tools -> execution -> minilog -> GitHub/VPS/Telegram report.

3. Hybrid:
   VPS keeps durable queue and monitoring while WSL performs local execution after boot, then writes back status and evidence.

Phases:
1. Deterministic relay plane.
2. OpenAI Agents SDK integration for planning, tool routing and tracing.
3. LangGraph for resumable long-running workflows.

Boot flow:
ChatGPT -> GitHub task -> VPS queue -> WSL boot -> sync -> MCP -> execution -> minilog -> report.

Required boot checks:
- Confirm Windows is online.
- Confirm WSL is available.
- Confirm ASPA local services and MCP endpoints are healthy.
- Pull/fetch GitHub branches and task packets.
- Compare VPS queue and WSL queue.
- Claim only one task at a time unless explicitly approved for parallel execution.
- Write a startup minilog before running long tasks.
