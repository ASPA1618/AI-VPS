# ADR-0001: Business system of record and offline ASPA mirror

- Status: Accepted
- Date: 2026-07-09
- Owners: ASPA1618
- Confidence: High for storage boundaries; Medium for the first snapshot transport

## Context

ASPA must combine legacy customer, vehicle, request, quotation, sale, balance, service and fitment history with future live operations.

The system is used from multiple execution planes:

- ChatGPT web/mobile connectors;
- Codex in VS Code;
- WSL terminal and workers;
- VPS services while the PC is offline;
- Telegram bot/Mini App;
- future `aspa.com.ua` retail and SaaS surfaces.

The main WSL workstation is not continuously online. GitHub is accessible from mobile and ChatGPT, but the connected repository is public and therefore cannot hold private business records. Google Sheets currently contains legacy evidence but is not suitable as the future operational CRM database.

## Options considered

### Option A — keep Google Sheets as the live CRM

Advantages:

- immediately familiar;
- easy manual editing;
- accessible from phone.

Rejected because:

- weak referential integrity and concurrency;
- difficult idempotency and audit guarantees;
- poor fit for multi-tenant APIs, Telegram and retail web;
- business logic would remain coupled to cell layout and formatting.

### Option B — store business records directly in Git

Advantages:

- version history and mobile access;
- easy connector reading.

Rejected because:

- public repository privacy risk;
- unsuitable for mutable transactional records and balances;
- merge/conflict model is wrong for CRM and commerce;
- fast runtime state would create repository noise and growth.

### Option C — PostgreSQL canonical store with Git engineering truth and VPS last-known relay

Advantages:

- transactional integrity, constraints and auditability;
- one model for CRM, vehicle facts, orders, balances and future channels;
- Git remains useful for schemas, migrations, ADRs and code;
- VPS can serve bounded last-known status while WSL is offline;
- legacy imports can remain replayable through manifests and hashes.

Selected.

## Decision

1. PostgreSQL is the canonical operational store for ASPA business data.
2. Google Drive/Sheets remain legacy source and evidence systems until import/cutover.
3. GitHub stores code, schema, migration, ADR, import metadata, synthetic fixtures and sanitised engineering snapshots only.
4. Private runtime and import artifacts remain outside Git under protected WSL/VPS storage.
5. All live writes from ChatGPT, Codex, WSL CLI, Telegram and web go through the same audited ASPA command/application layer.
6. The VPS may keep a bounded last-known operational/read snapshot, but it does not become an uncontrolled second CRM.
7. Git publication of runtime status is changed-only, sanitised and limited to a current snapshot; detailed history belongs in observability storage or expiring workflow artifacts.
8. Vehicle factory configuration, actual observations, retrofits and fitment exceptions coexist as temporal facts with evidence.
9. Customer balances are derived from immutable ledger entries, not manually overwritten totals.

## Consequences

### Positive

- consistent business logic across operator, Telegram, retail and agent interfaces;
- replayable and auditable legacy migration;
- safe mobile planning through issues and documentation;
- vehicle-specific actual configuration can override catalogue assumptions without deleting factory truth;
- future analytics can consume events/read models without mutating transactional data.

### Negative

- requires PostgreSQL migrations and application command handlers before full live use;
- WSL/VPS sync and snapshot publication need explicit implementation;
- legacy ambiguities remain in QA queues rather than disappearing;
- the public repository requires strict PII/secret controls and history audit.

### Risks

- accidental PII or credential publication;
- duplicate records if idempotency is incomplete;
- treating imported sale signals as confirmed installation;
- VPS drifting into a shadow system of record;
- direct SQL/tool mutations bypassing command policy.

## Controls

- `.gitignore`, CI artifact checks and secret scanning/push protection;
- CODEOWNERS and PR-required ruleset;
- import batch hashes, dry-run and record-level provenance;
- command idempotency and audit/outbox tables;
- snapshot allowlist and fail-closed privacy tests;
- explicit distinction between quotation, order, purchase, service and retrofit facts.

## Implementation sequence

1. Convert the SQL contract to the active WSL migration framework and dry-run it.
2. Register and validate the five-block legacy import bundle without business writes.
3. Load canonical customers/vehicles and relationships idempotently.
4. Load requests/offers/orders/ledger candidates and typed notes.
5. Expose bounded CRM/Vehicle/Order commands.
6. Publish sanitised changed-only snapshots to VPS/GitHub read surfaces.

## Supersession policy

This accepted ADR is append-only. A materially different storage or sync decision must be recorded in a new ADR that supersedes this one rather than rewriting the historical rationale.
