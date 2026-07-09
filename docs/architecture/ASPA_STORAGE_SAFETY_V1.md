# ASPA Storage Safety v1

Status: Draft / deferred architecture direction

ASPA sync, relay, minilog, extended-memory and watchdog loops must be storage-safe.

Core principle:
- Durable memory must be compact, rate-limited and bounded.

Future ASPA sync loops should check:
- free disk space;
- log directory growth;
- temp and artifact growth;
- repeated writes of unchanged state;
- heartbeat frequency;
- oversized raw traces.

Rules:
- Write durable heartbeat only on state change or slow interval.
- Prefer compact checkpoints over repeated full snapshots.
- Rotate logs by size and date.
- Keep raw traces only for failures or explicit debug mode.
- Use hashes to skip unchanged graph/task writes.
- Clean temp/cache/artifact directories at startup and after runs.
- Warn on disk pressure before long tasks.

Suggested initial thresholds:
- disk warning below 15 percent free;
- disk critical below 8 percent free;
- durable heartbeat no more than once per 5 minutes unless state changes;
- full minilog once per session or task transition.

Related:
- ASPA System Sync Relay Plane
- ASPA Idea Graph
- ASPA Extended Memory
