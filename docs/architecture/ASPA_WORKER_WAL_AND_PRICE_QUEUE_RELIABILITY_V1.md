# ASPA Worker WAL and Price Queue Reliability v1

Status: Draft / deferred architecture direction

## Purpose

ASPA needs a reliable worker and WAL-style queue plane for processing supplier prices and other incoming sources when the PC is ON and WSL is available.

Primary examples:
- price files from email;
- supplier API snapshots;
- FTP/HTTP file drops;
- manual uploads;
- future connector/import events.

## Core principle

```text
Every source event must be durable before processing.
```

Workers may crash, WSL may stop, Windows may reboot, and power may fail. ASPA must be able to resume without duplicating, losing or corrupting price processing.

## Target flow

```text
source event
  -> inbox record
  -> durable WAL/task queue
  -> worker claim with lease
  -> staged processing
  -> validation
  -> changed-only apply
  -> evidence/minilog
  -> done or retry/dead-letter
```

## Worker rules

- Claim one task with lease before processing.
- Renew lease only while making progress.
- Use idempotency keys per source file/message/supplier/profile.
- Never delete source artifact until processing is committed and evidence exists.
- Store raw source separately from normalized/interpreted/business layers.
- Use retry with capped attempts.
- Move poison tasks to dead-letter queue with reason.
- Write compact progress events, not noisy per-row logs.

## WAL direction

Use a WAL or append-only event journal for task lifecycle and recovery:
- received;
- stored;
- claimed;
- processing_started;
- checkpoint;
- applied;
- failed;
- retried;
- dead_lettered;
- completed.

The WAL must be compact, bounded and storage-safe.

## Price queue stages

1. Intake
- identify source: email/API/FTP/manual;
- save raw file or payload reference;
- compute content hash;
- create durable task.

2. Parse
- detect file type;
- parse CSV/XLS/XLSX/ZIP/XML/JSON where supported;
- record parser version and source metadata.

3. Normalize
- supplier account/profile;
- currency;
- article/brand;
- stock/warehouse;
- price and quantity fields.

4. Validate
- required fields;
- abnormal price/stock jumps;
- duplicate rows;
- supplier-specific rules.

5. Apply
- changed-only current tables;
- changed-only history;
- evidence summary;
- optional Parquet/lake snapshot later.

6. Report
- minilog;
- task status;
- metrics;
- warnings and blockers.

## WSL online behavior

When Windows and WSL are online:
- WSL ASPA worker becomes the preferred executor for heavy price/file processing;
- VPS keeps dashboard/relay state;
- worker syncs queue before claim;
- long jobs checkpoint progress;
- on restart, worker resumes from durable state.

## Observability and storage safety

Track:
- queue depth;
- task age;
- last heartbeat;
- rows processed;
- changed/unchanged counts;
- failures and retry count;
- disk free space;
- log growth;
- WAL growth;
- temp/artifact growth.

Apply storage rules:
- rotate logs;
- compact WAL when safe;
- avoid rewriting large state files;
- keep raw traces only on failure/debug;
- warn before long tasks if disk pressure exists.

## Future implementation slices

1. Define task and WAL schema.
2. Define idempotency keys for email price files and supplier snapshots.
3. Add worker claim/lease/retry/dead-letter protocol.
4. Add staged price processing contract.
5. Add observability dashboard counters.
6. Add storage safety thresholds.
7. Add resume tests for crash/reboot/WSL restart.

Related:
- ASPA Storage Safety v1
- ASPA System Sync Relay Plane v1
- ASPA Agent Runtime Test Matrix v1
- ASPA Cross Matrix and Deterministic Part Lookup v1
