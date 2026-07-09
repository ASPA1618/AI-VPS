# Security policy

## Reporting a vulnerability or accidental data exposure

Do not open a public issue containing:

- API keys, tokens, passwords, cookies or private keys;
- customer names, phones, emails or addresses;
- VIN collections, registration numbers or vehicle-owner mappings;
- balances, payments, order rows or private supplier payloads;
- raw logs or screenshots containing any of the above.

Use GitHub private vulnerability reporting from the repository **Security** tab when available. Otherwise contact the repository owner through an established private channel and provide only the minimum evidence required.

## Immediate response for exposed credentials

1. Revoke or rotate the credential first.
2. Remove it from current files, workflow logs, artifacts and runtime systems.
3. Assess whether Git history contains the value.
4. Rewrite shared history only through a coordinated incident process.
5. Re-clone or clean affected working copies after a rewrite.
6. Verify secret scanning and push protection are active.

Deleting a file in a new commit does not remove it from Git history.

## Repository data boundary

This repository may contain code, documentation, migrations, architecture decisions, synthetic fixtures and sanitised aggregate snapshots.

It must not contain production CRM data, customer identities, VIN lists, balances, order history, raw legacy exports, supplier credentials, database dumps or private runtime snapshots.

## Workflow security

- `GITHUB_TOKEN` permissions default to read-only and are increased only per job when required.
- Third-party actions should be pinned to a full commit SHA.
- Privileged `pull_request_target` workflows must not check out untrusted code.
- Workflow and security changes are covered by CODEOWNERS.
- Long-lived cloud/VPS credentials should be replaced by short-lived scoped authentication where supported.

## Supported versions

ASPA is currently under active internal development. Security fixes are applied to the active integration/main line; historical experimental branches are not supported unless explicitly restored.
