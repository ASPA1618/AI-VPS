# ASPA

ASPA is an internal-first, SaaS-ready platform for automotive-parts commerce, supplier integrations, vehicle fitment knowledge, CRM, order history and AI-assisted operator workflows.

## Canonical system boundaries

- **PostgreSQL:** canonical operational business data.
- **GitHub:** code, schemas, migrations, architecture decisions, synthetic tests and sanitised engineering metadata.
- **WSL on ROBOT-OMNI:** primary local development and heavy processing plane while the PC is online.
- **VPS:** relay, queue, connector and last-known read plane while WSL is offline.
- **Google Drive:** legacy source/evidence and business documents, not the future live CRM source of truth.
- **Telegram / web / ChatGPT / Codex:** interfaces over bounded ASPA application commands and read models.

Personal customer records, VIN collections, balances, raw orders, supplier credentials and legacy exports must never be committed to Git.

## Architecture principles

1. `Raw -> Interpreted -> Business` with immutable provenance.
2. One canonical customer/vehicle/order model shared by all interfaces.
3. Vehicle factory configuration and actual observed/retrofitted configuration coexist.
4. A quotation is not automatically an order; a sale is not automatically an installation.
5. Wrong crosses and fitment failures are retained as negative knowledge.
6. All mutations use actor context, idempotency and audit evidence.
7. Git stores desired engineering state; runtime state remains in PostgreSQL/VPS observability, with only a sanitised last-known snapshot for offline reading.

## Current architecture baseline

- [Legacy-to-Live Business Data Plane](docs/architecture/ASPA_LEGACY_TO_LIVE_BUSINESS_DATA_PLANE_V1.md)
- [GitHub / WSL / VPS Light Snapshot Plane](docs/architecture/ASPA_GITHUB_WSL_VPS_LIGHT_SNAPSHOT_PLANE_V1.md)
- [Worker WAL and Price Queue Reliability](docs/architecture/ASPA_WORKER_WAL_AND_PRICE_QUEUE_RELIABILITY_V1.md)
- [Business Core SQL Contract](docs/data/sql/ASPA_BUSINESS_CORE_SCHEMA_V1.sql)
- [Legacy Import Manifest](docs/data/legacy/ASPA_LEGACY_IMPORT_MANIFEST_V1.json)
- [ADR-0001: Business System of Record and Offline Mirror](docs/adr/0001-business-system-of-record-and-offline-mirror.md)

## Development workflow

```text
ChatGPT/mobile idea
  -> structured GitHub issue
  -> bounded feature branch/worktree
  -> Codex/VS Code/WSL implementation
  -> tests and evidence
  -> pull request
  -> review/ruleset checks
  -> merge
  -> VPS/WSL reconciliation and sanitised snapshot
```

Use the ASPA issue form for new work. Pull requests must state business meaning, scope, architecture boundaries, evidence, operational impact, limitations and the next bounded slices.

## Repository safety

The repository rejects or ignores:

- `.env` variants, keys and credentials;
- runtime `var/` data;
- database dumps and private exports;
- `ASPA_Legacy_*.csv/xlsx/zip` artifacts;
- raw customer, vehicle, balance or order history;
- private snapshot payloads.

GitHub Actions use read-only permissions by default. Sensitive workflow, schema, import-manifest and snapshot paths are covered by `CODEOWNERS`.

## Next implementation slices

1. Convert the SQL contract into the active WSL migration framework and run a PostgreSQL dry-run.
2. Register the legacy bundle under a protected import batch and prove replay/idempotency without production writes.
3. Implement bounded Customer, Vehicle, VehicleFact, Request and Order command handlers for ChatGPT connectors, Codex, Telegram and future web surfaces.
4. Connect the sanitised snapshot generator to WSL and VPS with changed-only publication.

## Status

The current branch contains architecture and implementation contracts. No production CRM migration, balance creation or customer-data import is performed by documentation changes alone.
