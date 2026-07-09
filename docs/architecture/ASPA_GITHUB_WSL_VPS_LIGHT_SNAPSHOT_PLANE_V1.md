# ASPA GitHub / WSL / VPS Light Snapshot Plane v1

Status: implementation baseline

## 1. Goal

ASPA must remain understandable and partially operable when the main Windows/WSL workstation is offline.

The snapshot plane provides a small, sanitised and deterministic view of the current ASPA state that can be read from:

- GitHub connector in ChatGPT, including mobile;
- VPS services;
- WSL after boot;
- Codex/VS Code;
- future ASPA admin UI.

It is not a database replica and must not contain customer PII, VIN lists, order rows, balances or supplier secrets.

## 2. Three storage planes

### 2.1 Git repository

Stores durable engineering truth:

- source code;
- migrations;
- architecture documents;
- schemas and contracts;
- synthetic fixtures;
- issue/PR history;
- sanitised current snapshot metadata.

### 2.2 WSL operational store

Stores full internal state:

- PostgreSQL business data;
- raw and staging imports;
- local artifacts;
- detailed worker logs;
- private runtime status;
- credentials through environment/Vault.

### 2.3 VPS relay/read plane

Stores enough state to answer operational questions while WSL is offline:

- last published light snapshot;
- current queue/task summary;
- last known WSL health and sync timestamp;
- active architecture/schema versions;
- latest successful commit/branch references;
- sanitised supplier capability summary;
- public-safe business aggregate counts;
- links to GitHub issues, PRs and evidence.

The VPS must not become an uncontrolled second CRM database.

## 3. Snapshot contents

Recommended `current.json` payload:

```json
{
  "schema_version": "aspa-light-snapshot-v1",
  "generated_at": "2026-07-09T12:00:00Z",
  "source_host": "ROBOT-OMNI",
  "repo": {
    "remote": "ASPA1618/AI-VPS",
    "branch": "feat/example",
    "commit": "...",
    "dirty": false
  },
  "versions": {
    "business_schema": "v1",
    "legacy_import_contract": "v1",
    "supplier_registry": "..."
  },
  "runtime": {
    "wsl_status": "online",
    "last_worker_heartbeat": "...",
    "queue_depth": 0,
    "running_task_count": 0,
    "failed_task_count": 0
  },
  "business_aggregates": {
    "customer_count": 330,
    "vehicle_count": 1979,
    "request_count": 21792,
    "order_count": 0
  },
  "suppliers": {
    "enabled_count": 0,
    "healthy_count": 0,
    "degraded_count": 0
  },
  "work": {
    "active_issue_numbers": [],
    "active_pr_numbers": [],
    "last_completed_task": null
  },
  "evidence": {
    "snapshot_sha256": "...",
    "source_commit": "..."
  }
}
```

Allowed values are aggregate or operational metadata only.

## 4. Explicitly forbidden snapshot content

The publisher must reject payloads containing:

- customer names;
- phone numbers;
- email addresses;
- delivery addresses;
- full VIN or registration-number lists;
- raw order/request rows;
- individual balances or payments;
- API keys, tokens, passwords or cookies;
- raw supplier payloads;
- environment variables;
- unredacted log lines.

Identifiers may appear only when they are engineering identifiers such as commit SHA, issue number, schema version or task ID.

## 5. Publication model

Use two Git branches with different purposes:

- normal feature/main branches: durable code and documentation;
- `state/aspa-light-snapshot`: replaceable current-state mirror.

The state branch should contain only:

```text
snapshot/
  current.json
  CURRENT.md
  SHA256SUMS
  history/
    YYYY-MM-DD.json   # optional one daily sample, bounded retention
```

Publication policy:

- publish only after meaningful state change, task transition or slow heartbeat;
- minimum normal interval: 5 minutes;
- do not publish unchanged content;
- current payload target below 256 KiB;
- hard limit below 512 KiB;
- retain at most 30 daily historical snapshots in Git;
- detailed artifacts remain in WSL/VPS object storage;
- force-update of the dedicated state branch is permitted only through the snapshot publisher;
- ordinary development branches must never receive generated private runtime state.

## 6. Sync flow

```text
WSL operational state
  -> bounded snapshot collector
  -> redact/allowlist validation
  -> canonical JSON serialisation
  -> SHA-256
  -> local current.json + CURRENT.md
  -> publish to state/aspa-light-snapshot over SSH
  -> VPS pulls or receives webhook
  -> ChatGPT/GitHub connector reads snapshot when PC is offline
```

On WSL boot:

```text
read VPS/GitHub last snapshot
  -> compare source commit and task state
  -> reconcile queue ownership
  -> mark WSL online
  -> resume eligible work
  -> publish new snapshot
```

## 7. Mobile GitHub workflow

GitHub is the durable mobile control surface, not the worker itself.

### Idea capture

From phone/ChatGPT:

1. create an issue using the ASPA task template;
2. describe business goal, source/evidence, boundaries and desired result;
3. do not paste secrets or raw customer data;
4. assign a stable area and implementation phase.

### Implementation

When WSL is available:

1. Codex or operator claims the issue;
2. creates `feat/<human-readable-slice>` branch/worktree;
3. implements bounded scope;
4. runs tests and evidence checks;
5. commits with business/architecture meaning;
6. pushes and opens PR;
7. updates issue with commit, tests, limitations and next slice.

### Offline reading

When WSL is unavailable:

- ChatGPT reads GitHub docs/issues/PRs and the state snapshot;
- VPS provides last known operational summary;
- planning and documentation can continue;
- tasks requiring private data or WSL execution remain queued, not simulated.

## 8. Commit and branch policy

Branch examples:

- `feat/aspa-legacy-to-live-business-data-plane-v1`;
- `feat/crm-customer-vehicle-schema-v1`;
- `feat/vehicle-effective-fitment-resolver-v1`;
- `ops/wsl-vps-light-snapshot-v1`;
- `fix/order-ledger-idempotency-v1`.

Commit body should explain:

- business meaning;
- architecture boundary;
- evidence/tests;
- limitations and deferred work.

Generated messages such as `update files`, `auto commit` or `changes` are not acceptable for ASPA agent/CI commits.

## 9. Repository hygiene

- one canonical repository mirror per active ASPA codebase;
- do not use Git branches as backup folders;
- use worktrees for simultaneous bounded slices;
- push every accepted clean branch before risky WSL/Windows operations;
- keep salvage branches temporary and document deletion conditions;
- protect primary integration branch with PR checks;
- run secret/PII validation before push;
- keep generated large artifacts outside Git;
- record release/snapshot manifests with hashes.

Historical commits containing secrets require a separate incident process:

1. identify exposed values;
2. rotate/revoke credentials first;
3. decide whether history rewrite is required;
4. coordinate force push and clone cleanup;
5. verify GitHub secret scanning and no live secret remains.

Never rewrite shared history casually.

## 10. Initial implementation slices

### Slice A — snapshot generator and validator

- add allowlisted collector;
- add forbidden-key/value checks;
- produce JSON, Markdown and SHA256SUMS;
- add tests with safe and unsafe fixtures.

### Slice B — state branch publisher and VPS pull

- create `state/aspa-light-snapshot`;
- publish only changed hashes over SSH;
- configure VPS read-only pull or webhook;
- expose last snapshot through bounded ASPA status tool.

### Slice C — GitHub issue-to-WSL relay

- standardise issue template;
- map issue to task board entry;
- claim only when WSL worker is online;
- link branch, commit, PR, tests and final evidence;
- publish state transition in light snapshot.

## 11. Acceptance criteria

1. snapshot can be read through GitHub when the PC is off;
2. snapshot contains no PII/secrets/raw business rows;
3. unchanged state does not produce a new commit;
4. WSL boot can reconcile against the last snapshot;
5. VPS can expose last-known state without becoming the canonical CRM;
6. mobile-created issue can be traced through branch, PR, tests and completion;
7. snapshot branch growth remains bounded;
8. snapshot validation fails closed on suspicious content.
