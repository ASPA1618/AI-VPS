# ASPA Legacy-to-Live Business Data Plane v1

Status: architecture baseline for staged implementation

## 1. Purpose

This document defines how ASPA must combine legacy Google Sheets history with future live CRM, vehicle, quotation, order, balance, fitment and e-commerce data.

The target is not a one-time spreadsheet import. The target is a durable business data plane that can be used consistently from:

- ChatGPT connectors;
- Codex in VS Code IDE;
- WSL terminal and workers;
- internal ASPA operator UI;
- Telegram bot and Telegram Mini App;
- future `aspa.com.ua` retail web;
- future SaaS tenants and roles.

## 2. Canonical storage decision

PostgreSQL is the canonical operational store.

CRM is a domain/application layer over canonical database entities. CRM must not become a separate data silo.

Google Drive and Google Sheets remain source/evidence systems for the legacy import. They are not the live source of truth after cutover.

Git stores only:

- schema and migrations;
- import contracts and manifests;
- deterministic parsers and tests;
- runbooks and architecture decisions;
- synthetic fixtures without personal data.

Git must not store customer names, phones, addresses, balances, order history, VIN collections or raw legacy exports.

Recommended WSL runtime layout:

```text
/home/cebas/ASPA/
  docs/
  migrations/
  runtime/
  tests/
  var/
    imports/
      legacy/
        <batch_id>/
          raw/
          staging/
          evidence/
          rejected/
    artifacts/
    exports/
```

`var/` must be gitignored. Long-lived raw files may later move to object storage, but PostgreSQL keeps metadata, hashes and immutable provenance.

## 3. Layering

ASPA keeps the existing Raw -> Interpreted -> Business principle.

```text
Raw
  immutable source rows, source files, colours, formatting, source coordinates

Interpreted
  parsed contacts, VINs, dates, part numbers, prices, quantities, note types

Business
  canonical customers, vehicles, requests, offers, orders, ledger entries,
  service events and effective vehicle configuration
```

No parser is allowed to destroy the raw value while normalising it.

## 4. Core domains

### 4.1 Identity and CRM

Canonical entities:

- `customer` — person or organisation;
- `customer_identity` — phone, email, Telegram user, external account;
- `customer_address` — delivery, billing or service address;
- `customer_note` — typed CRM note;
- `customer_vehicle_relationship` — historical relation between a customer and a vehicle;
- `customer_account` — accounting/commerce account;
- `ledger_entry` — immutable debit/credit event.

A balance is calculated from ledger entries. It must not be stored as an editable number without history.

One customer may have multiple phones and Telegram identities. One phone may require review before being linked to multiple customer records.

### 4.2 Vehicle digital record

Canonical entities:

- `vehicle` — stable ASPA vehicle identity;
- `vehicle_identifier` — VIN, local VIN, registration number, fleet ID;
- `vehicle_catalog_binding` — TecDoc or other catalogue identity;
- `vehicle_attribute_fact` — asserted property with source, confidence and validity;
- `vehicle_component_fact` — actual observed/installed component;
- `vehicle_retrofit` — added, removed or converted equipment;
- `vehicle_fitment_exception` — negative or exceptional applicability knowledge;
- `vehicle_service_event` — confirmed service, repair or installation event.

The vehicle record must preserve both factory baseline and actual current configuration.

Example:

```text
VIN baseline: front fog lamps absent
Observed actual: front fog lamps installed
Retrofit event: fog lamps added after production
Effective state: fog lamps present as of the retrofit date
```

Another example:

```text
Catalogue expectation: fuel filter A
Observed actual: fuel filter B was physically installed
Reason: engine/fuel system conversion or previous retrofit
Future lookup: prefer observed actual B for this vehicle, but retain A as factory baseline
```

### 4.3 Requests, quotations and orders

Canonical entities:

- `business_day_session` — imported legacy date boundary;
- `part_request` — customer need or question;
- `part_request_item` — requested part position;
- `offer_line` — proposed brand/article/price/source;
- `sales_order` — commercial order;
- `sales_order_line` — ordered item;
- `order_status_event` — append-only order lifecycle;
- `payment_event` — payment, refund or adjustment;
- `shipment` — delivery and carrier information;
- `return_event` — return/cancellation;
- `legacy_note` — typed source comment linked by ID.

A quotation is not automatically an order. A green legacy signal may create an imported sale candidate or confirmed legacy sale according to the import policy, but not a confirmed installation.

### 4.4 Product, part and cross logic

Customer/order tables reference canonical part identity rather than embedding free text wherever possible.

The business data plane must integrate with the existing ASPA part/cross architecture:

- brand normalisation and aliases;
- article normalisation;
- OEM references;
- replacement/supersession chains;
- supplier cross candidates;
- TecDoc validation;
- fitment validation against effective vehicle facts;
- provenance for every relation.

Legacy wrong-cross notes are valuable negative edges. They must be retained as `vehicle_fitment_exception` or `cross_validation_event`, never deleted as noise.

## 5. Vehicle fact model

Every vehicle fact has:

- `fact_type`;
- `value_json`;
- `source_type`;
- `source_reference`;
- `confidence`;
- `valid_from` and `valid_to`;
- `observed_at`;
- `recorded_at`;
- optional `supersedes_fact_id`;
- tenant and provenance fields.

Recommended source types:

- `vin_decoder`;
- `tecdoc_catalog`;
- `oem_catalog`;
- `model_catalog`;
- `operator_observation`;
- `customer_statement`;
- `service_event`;
- `legacy_note`;
- `supplier_fitment`;
- `inference`.

Resolution is attribute-specific and temporal. Do not use one global source-priority number for every property.

General rule:

```text
actual confirmed observation/service
  > explicit retrofit declaration
  > VIN/OEM factory configuration
  > model-level catalogue assumption
```

However, lower-priority facts remain stored. The resolver returns an effective value plus its evidence chain.

## 6. TecDoc integration boundary

TecDoc data must bind to ASPA vehicles through a versioned mapping rather than overwrite the vehicle row.

`vehicle_catalog_binding` should store:

- provider;
- provider vehicle/type ID;
- binding method: VIN, engine, model/year, manual;
- binding confidence;
- provider dataset/version;
- matched attributes;
- mismatch warnings;
- valid_from/valid_to;
- raw snapshot reference.

The lookup flow should be:

```text
Vehicle
  -> effective factory + actual facts
  -> TecDoc binding candidates
  -> fitment query
  -> apply retrofit/observed exceptions
  -> ranked result with evidence
```

## 7. Legacy import model

Every import run creates an immutable `import_batch`.

Required properties:

- source system and document ID;
- source file hash;
- parser version;
- contract version;
- started/completed timestamps;
- row counts;
- accepted/rejected/review counts;
- dry-run report;
- operator approval;
- code commit SHA;
- idempotency key.

Each imported business record stores an `import_record_link` with:

- `batch_id`;
- source file/sheet/row/cell range;
- raw record hash;
- target entity type and ID;
- merge/link basis;
- confidence;
- parser rule/version.

Re-running the same batch must not duplicate entities, orders, notes or ledger entries.

## 8. Live write architecture

All operator surfaces must use the same application service/API.

```text
ChatGPT connector
Codex / VS Code
WSL CLI
Web admin
Telegram bot / Mini App
Retail web
        |
        v
ASPA Business API / command handlers
        |
        +-> validation and policy
        +-> PostgreSQL transaction
        +-> outbox event
        +-> evidence/audit log
```

Direct SQL writes from ChatGPT, Codex scripts or UI clients are prohibited outside migrations and controlled maintenance tools.

Representative commands:

- `customer.create_or_resolve`;
- `customer.add_identity`;
- `vehicle.create_or_resolve`;
- `vehicle.assert_fact`;
- `vehicle.record_retrofit`;
- `vehicle.record_fitment_exception`;
- `request.create`;
- `offer.record`;
- `order.create_from_offer`;
- `payment.record`;
- `shipment.record`;
- `return.record`;
- `service.record`.

Every command requires an idempotency key and actor context.

## 9. Telegram, retail web and SaaS readiness

Telegram identity is stored as one customer identity, not as the customer primary key.

A logged-in customer may be linked through:

- verified phone;
- Telegram user ID;
- Telegram WebApp signed init data;
- email;
- future web account identity.

The customer portal should expose only policy-approved views:

- own vehicles;
- own requests and quotations;
- own orders and shipments;
- own payments/balance statement;
- service and fitment history where appropriate;
- notifications and approvals.

Multi-tenant fields must exist from the beginning even while ASPA is operated as internal single-tenant:

- `tenant_id` on business entities;
- role/policy checks;
- tenant-scoped uniqueness;
- no cross-tenant identity resolution.

## 10. Events and analytics

Transactional writes emit outbox events such as:

- `CustomerResolved`;
- `VehicleResolved`;
- `VehicleFactAsserted`;
- `VehicleRetrofitRecorded`;
- `FitmentExceptionRecorded`;
- `RequestCreated`;
- `OfferRecorded`;
- `OrderCreated`;
- `PaymentRecorded`;
- `ShipmentChanged`;
- `ReturnRecorded`;
- `ServiceRecorded`.

Analytics must consume events or replicated read models. It must not modify canonical transactional records.

Initial useful analytics:

- customer lifetime purchases;
- quote-to-order conversion;
- margin by supplier/brand/category;
- repeat demand by vehicle;
- observed cross failures;
- retrofit-driven fitment overrides;
- outstanding balances;
- order and shipment lead time;
- supplier price/availability performance.

## 11. Security and privacy

- PII and VINs stay out of Git and public logs.
- Secrets remain in environment/Vault.
- Raw import access is restricted.
- Connector tools expose bounded business commands and read models.
- Every mutation records actor, channel, timestamp and idempotency key.
- Data exports are explicit audited operations.
- Telegram/web access requires verified identity and tenant policy.

## 12. Implementation sequence

### Slice 1 — schema and dry-run import

- add PostgreSQL migrations for import, CRM, vehicle facts and commercial history;
- place existing generated artifacts in protected `var/imports/legacy/<batch_id>`;
- register hashes and manifest;
- run dry-run validation without business writes;
- produce counts and referential-integrity evidence.

### Slice 2 — idempotent legacy load

- import customers and identities;
- import vehicles, identifiers and customer relationships;
- import business sessions, requests, offers and transaction signals;
- import typed notes, vehicle observations and fitment exceptions;
- reconcile balances only through ledger opening entries;
- produce an immutable import report and rollback boundary.

### Slice 3 — live CRM command plane

- expose bounded Customer/Vehicle/Request/Order commands through ASPA tools;
- add outbox events and audit trail;
- add Telegram identity binding and customer-scoped read endpoints;
- add operator screens/read models;
- begin recording new live facts in the same canonical model as legacy history.

## 13. Non-goals for v1

- no automatic deletion of legacy duplicates;
- no irreversible merge without evidence;
- no automatic assumption that a sale means installation;
- no direct mutation of TecDoc/vendor data into canonical facts;
- no personal legacy files committed to Git;
- no customer-facing portal exposure before identity and policy controls exist.

## 14. Acceptance criteria

The architecture slice is ready for implementation when:

1. schema migration and import manifest are versioned;
2. dry-run can process the complete legacy bundle without business writes;
3. every accepted row has provenance and idempotency identity;
4. unresolved/ambiguous records remain in QA rather than being silently guessed;
5. a vehicle can retain factory baseline, actual observation and retrofit state simultaneously;
6. repeated import produces zero duplicate business records;
7. ChatGPT, Codex, WSL CLI and future UI use the same command contracts.
