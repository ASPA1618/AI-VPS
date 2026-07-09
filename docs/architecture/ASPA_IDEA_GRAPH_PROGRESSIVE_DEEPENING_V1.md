# ASPA Idea Graph Progressive Deepening v1

Status: Draft / deferred architecture direction

## Purpose

ASPA Idea Graph should not force every idea to be fully designed immediately.

Many ideas begin as short direction nodes. When ASPA later touches a related branch, issue, task, supplier, subsystem or implementation slice, the system may deepen that node into detailed reasoning, solution options, trade-offs and execution plans.

## Core rule

```text
Capture broadly. Deepen only when useful.
```

## Node depth levels

1. Seed
- raw idea or short direction;
- no implementation pressure.

2. Framed
- clarified intent;
- related docs/issues known;
- rough risks and dependencies.

3. Explored
- possible solutions listed;
- trade-offs recorded;
- open questions identified.

4. Planned
- small implementation slices;
- executor choice;
- evidence boundary;
- rollback/safety notes.

5. Active
- linked to branch/task/PR;
- WSL/VPS execution path selected;
- minilog and evidence expected.

6. Archived or Done
- result recorded;
- links preserved;
- future continuation point clear.

## Trigger for deepening

Deepen a graph node when:
- the owner says "продолжаем дальше";
- a related GitHub issue is selected;
- WSL becomes available and a ready slice exists;
- a branch touches a related subsystem;
- a dependency changes;
- a failure or blocker appears;
- a decision requires trade-off analysis.

## Deepening output

When deepening a node, ASPA should produce:
- current understanding;
- relevant graph links;
- possible solution paths;
- risks and constraints;
- recommended next safe slice;
- what not to implement yet;
- evidence required for done;
- whether WSL/VPS/ChatGPT/human should execute.

## Anti-bloat rule

Do not expand every idea into a large document. Store compact seeds first. Create longer docs only when the idea becomes active, risky, strategic or implementation-near.

## Related

- ASPA Idea Graph v1
- ASPA System Sync Relay Plane v1
- ASPA Storage Safety v1
- Mobile GitHub workflow and Idea Graph issue
