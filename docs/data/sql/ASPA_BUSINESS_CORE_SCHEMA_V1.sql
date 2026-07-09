-- ASPA Business Core Schema v1
-- Status: implementation contract / not yet applied to production
-- PostgreSQL 16+

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA IF NOT EXISTS aspa_business;
SET search_path TO aspa_business, public;

CREATE TYPE identity_kind AS ENUM (
    'phone', 'email', 'telegram_user', 'telegram_chat', 'web_account',
    'external_customer_code', 'other'
);

CREATE TYPE relationship_kind AS ENUM (
    'owner', 'previous_owner', 'driver', 'requester', 'payer', 'fleet_member',
    'service_contact', 'unknown'
);

CREATE TYPE vehicle_fact_source AS ENUM (
    'vin_decoder', 'tecdoc_catalog', 'oem_catalog', 'model_catalog',
    'operator_observation', 'customer_statement', 'service_event',
    'legacy_note', 'supplier_fitment', 'inference'
);

CREATE TYPE request_status AS ENUM (
    'open', 'quoted', 'ordered', 'closed_no_sale', 'cancelled', 'legacy_unknown'
);

CREATE TYPE order_status AS ENUM (
    'draft', 'confirmed', 'procurement', 'ready', 'shipped', 'completed',
    'cancelled', 'returned', 'legacy_imported'
);

CREATE TYPE ledger_direction AS ENUM ('debit', 'credit');

CREATE TABLE tenant (
    tenant_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug text NOT NULL UNIQUE,
    display_name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE actor_identity (
    actor_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    actor_type text NOT NULL,
    external_ref text,
    display_name text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, actor_type, external_ref)
);

CREATE TABLE import_batch (
    batch_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    source_system text NOT NULL,
    source_document_id text,
    source_artifact_uri text NOT NULL,
    source_sha256 text NOT NULL,
    parser_version text NOT NULL,
    contract_version text NOT NULL,
    idempotency_key text NOT NULL,
    code_commit_sha text,
    status text NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    counts_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    evidence_uri text,
    approved_by_actor_id uuid REFERENCES actor_identity(actor_id),
    approved_at timestamptz,
    UNIQUE (tenant_id, idempotency_key),
    UNIQUE (tenant_id, source_sha256, parser_version, contract_version)
);

CREATE TABLE customer (
    customer_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    customer_type text NOT NULL DEFAULT 'person',
    display_name text NOT NULL,
    status text NOT NULL DEFAULT 'active',
    legacy_primary_key text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    merged_into_customer_id uuid REFERENCES customer(customer_id),
    UNIQUE (tenant_id, legacy_primary_key)
);

CREATE TABLE customer_identity (
    customer_identity_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    customer_id uuid NOT NULL REFERENCES customer(customer_id),
    kind identity_kind NOT NULL,
    raw_value text NOT NULL,
    normalized_value text NOT NULL,
    is_verified boolean NOT NULL DEFAULT false,
    is_primary boolean NOT NULL DEFAULT false,
    valid_from timestamptz,
    valid_to timestamptz,
    source_type text NOT NULL,
    source_reference text,
    confidence numeric(4,3) NOT NULL DEFAULT 1.000,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, kind, normalized_value, customer_id)
);

CREATE INDEX customer_identity_lookup_idx
    ON customer_identity (tenant_id, kind, normalized_value)
    WHERE valid_to IS NULL;

CREATE TABLE customer_address (
    customer_address_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    customer_id uuid NOT NULL REFERENCES customer(customer_id),
    address_type text NOT NULL,
    country_code text,
    region text,
    city text,
    address_line text,
    postal_code text,
    carrier_branch_ref text,
    source_reference text,
    valid_from timestamptz,
    valid_to timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE vehicle (
    vehicle_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    display_name text,
    make_canonical text,
    model_canonical text,
    production_date date,
    status text NOT NULL DEFAULT 'active',
    legacy_primary_key text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, legacy_primary_key)
);

CREATE TABLE vehicle_identifier (
    vehicle_identifier_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    vehicle_id uuid NOT NULL REFERENCES vehicle(vehicle_id),
    identifier_type text NOT NULL,
    raw_value text NOT NULL,
    normalized_value text NOT NULL,
    is_primary boolean NOT NULL DEFAULT false,
    is_standard boolean NOT NULL DEFAULT false,
    source_reference text,
    confidence numeric(4,3) NOT NULL DEFAULT 1.000,
    valid_from timestamptz,
    valid_to timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, identifier_type, normalized_value, vehicle_id)
);

CREATE UNIQUE INDEX vehicle_primary_vin_idx
    ON vehicle_identifier (tenant_id, normalized_value)
    WHERE identifier_type = 'vin' AND is_primary = true AND valid_to IS NULL;

CREATE TABLE customer_vehicle_relationship (
    customer_vehicle_relationship_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    customer_id uuid NOT NULL REFERENCES customer(customer_id),
    vehicle_id uuid NOT NULL REFERENCES vehicle(vehicle_id),
    relationship relationship_kind NOT NULL,
    valid_from timestamptz,
    valid_to timestamptz,
    source_reference text,
    confidence numeric(4,3) NOT NULL DEFAULT 1.000,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, customer_id, vehicle_id, relationship, valid_from)
);

CREATE TABLE vehicle_catalog_binding (
    vehicle_catalog_binding_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    vehicle_id uuid NOT NULL REFERENCES vehicle(vehicle_id),
    provider text NOT NULL,
    provider_vehicle_id text NOT NULL,
    binding_method text NOT NULL,
    binding_confidence numeric(4,3) NOT NULL,
    provider_version text,
    matched_attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    mismatch_warnings jsonb NOT NULL DEFAULT '[]'::jsonb,
    raw_snapshot_uri text,
    valid_from timestamptz,
    valid_to timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, vehicle_id, provider, provider_vehicle_id, provider_version)
);

CREATE TABLE vehicle_attribute_fact (
    vehicle_attribute_fact_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    vehicle_id uuid NOT NULL REFERENCES vehicle(vehicle_id),
    attribute_code text NOT NULL,
    value_json jsonb NOT NULL,
    source_type vehicle_fact_source NOT NULL,
    source_reference text,
    confidence numeric(4,3) NOT NULL,
    observed_at timestamptz,
    valid_from timestamptz,
    valid_to timestamptz,
    supersedes_fact_id uuid REFERENCES vehicle_attribute_fact(vehicle_attribute_fact_id),
    created_by_actor_id uuid REFERENCES actor_identity(actor_id),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX vehicle_attribute_effective_idx
    ON vehicle_attribute_fact (tenant_id, vehicle_id, attribute_code, valid_from, valid_to);

CREATE TABLE vehicle_component_fact (
    vehicle_component_fact_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    vehicle_id uuid NOT NULL REFERENCES vehicle(vehicle_id),
    component_code text NOT NULL,
    position_code text,
    brand_raw text,
    article_raw text,
    canonical_part_id uuid,
    state text NOT NULL,
    quantity numeric(12,3),
    source_type vehicle_fact_source NOT NULL,
    source_reference text,
    confidence numeric(4,3) NOT NULL,
    observed_at timestamptz,
    valid_from timestamptz,
    valid_to timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE vehicle_retrofit (
    vehicle_retrofit_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    vehicle_id uuid NOT NULL REFERENCES vehicle(vehicle_id),
    retrofit_type text NOT NULL,
    affected_system text NOT NULL,
    description text NOT NULL,
    before_state jsonb,
    after_state jsonb,
    performed_at timestamptz,
    confirmed boolean NOT NULL DEFAULT false,
    source_reference text,
    confidence numeric(4,3) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE vehicle_fitment_exception (
    vehicle_fitment_exception_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    vehicle_id uuid NOT NULL REFERENCES vehicle(vehicle_id),
    component_code text,
    brand_raw text,
    article_raw text,
    canonical_part_id uuid,
    exception_type text NOT NULL,
    reason text NOT NULL,
    source_reference text,
    observed_at timestamptz,
    confidence numeric(4,3) NOT NULL,
    valid_from timestamptz,
    valid_to timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE business_day_session (
    business_day_session_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    business_date date NOT NULL,
    source_boundary_row integer,
    date_resolution_status text NOT NULL,
    source_reference text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, source_reference)
);

CREATE TABLE part_request (
    part_request_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    customer_id uuid REFERENCES customer(customer_id),
    vehicle_id uuid REFERENCES vehicle(vehicle_id),
    business_day_session_id uuid REFERENCES business_day_session(business_day_session_id),
    status request_status NOT NULL DEFAULT 'open',
    channel text NOT NULL,
    requested_at timestamptz NOT NULL,
    legacy_primary_key text,
    created_by_actor_id uuid REFERENCES actor_identity(actor_id),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, legacy_primary_key)
);

CREATE TABLE part_request_item (
    part_request_item_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    part_request_id uuid NOT NULL REFERENCES part_request(part_request_id),
    component_name_raw text NOT NULL,
    original_reference_raw text,
    cross_chain_raw text,
    quantity_requested numeric(12,3),
    canonical_part_id uuid,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE offer_line (
    offer_line_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    part_request_item_id uuid NOT NULL REFERENCES part_request_item(part_request_item_id),
    supplier_id uuid,
    supplier_account_id uuid,
    brand_raw text,
    article_raw text,
    canonical_part_id uuid,
    purchase_unit_price numeric(18,4),
    sale_unit_price numeric(18,4),
    quantity numeric(12,3),
    purchase_total numeric(18,4),
    sale_total numeric(18,4),
    currency_code char(3) NOT NULL DEFAULT 'UAH',
    warehouse_raw text,
    lead_time_raw text,
    offer_status text NOT NULL,
    source_reference text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sales_order (
    sales_order_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    customer_id uuid REFERENCES customer(customer_id),
    vehicle_id uuid REFERENCES vehicle(vehicle_id),
    originating_request_id uuid REFERENCES part_request(part_request_id),
    status order_status NOT NULL,
    channel text NOT NULL,
    ordered_at timestamptz,
    currency_code char(3) NOT NULL DEFAULT 'UAH',
    total_amount numeric(18,4),
    legacy_primary_key text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, legacy_primary_key)
);

CREATE TABLE sales_order_line (
    sales_order_line_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    sales_order_id uuid NOT NULL REFERENCES sales_order(sales_order_id),
    offer_line_id uuid REFERENCES offer_line(offer_line_id),
    canonical_part_id uuid,
    brand_raw text,
    article_raw text,
    quantity numeric(12,3) NOT NULL,
    unit_price numeric(18,4) NOT NULL,
    line_total numeric(18,4) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE order_status_event (
    order_status_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    sales_order_id uuid NOT NULL REFERENCES sales_order(sales_order_id),
    from_status order_status,
    to_status order_status NOT NULL,
    reason text,
    occurred_at timestamptz NOT NULL,
    actor_id uuid REFERENCES actor_identity(actor_id),
    source_reference text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE customer_account (
    customer_account_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    customer_id uuid NOT NULL REFERENCES customer(customer_id),
    currency_code char(3) NOT NULL DEFAULT 'UAH',
    account_type text NOT NULL DEFAULT 'trade',
    opened_at timestamptz NOT NULL DEFAULT now(),
    closed_at timestamptz,
    UNIQUE (tenant_id, customer_id, currency_code, account_type)
);

CREATE TABLE ledger_entry (
    ledger_entry_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    customer_account_id uuid NOT NULL REFERENCES customer_account(customer_account_id),
    direction ledger_direction NOT NULL,
    amount numeric(18,4) NOT NULL CHECK (amount >= 0),
    currency_code char(3) NOT NULL,
    entry_type text NOT NULL,
    sales_order_id uuid REFERENCES sales_order(sales_order_id),
    external_reference text,
    idempotency_key text NOT NULL,
    occurred_at timestamptz NOT NULL,
    source_reference text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, idempotency_key)
);

CREATE VIEW customer_account_balance AS
SELECT
    tenant_id,
    customer_account_id,
    currency_code,
    SUM(CASE WHEN direction = 'debit' THEN amount ELSE -amount END) AS balance
FROM ledger_entry
GROUP BY tenant_id, customer_account_id, currency_code;

CREATE TABLE vehicle_service_event (
    vehicle_service_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    vehicle_id uuid NOT NULL REFERENCES vehicle(vehicle_id),
    customer_id uuid REFERENCES customer(customer_id),
    sales_order_id uuid REFERENCES sales_order(sales_order_id),
    event_type text NOT NULL,
    description text NOT NULL,
    odometer_km integer,
    confirmed boolean NOT NULL DEFAULT false,
    performed_at timestamptz,
    source_reference text,
    confidence numeric(4,3) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE legacy_note (
    legacy_note_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    business_day_session_id uuid REFERENCES business_day_session(business_day_session_id),
    note_type text NOT NULL,
    raw_text text NOT NULL,
    target_entity_type text,
    target_entity_id uuid,
    secondary_target_entity_type text,
    secondary_target_entity_id uuid,
    attachment_basis text,
    confidence numeric(4,3) NOT NULL,
    source_reference text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, source_reference)
);

CREATE TABLE import_record_link (
    import_record_link_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    batch_id uuid NOT NULL REFERENCES import_batch(batch_id),
    source_sheet text NOT NULL,
    source_row integer,
    source_cell_range text,
    raw_record_sha256 text NOT NULL,
    target_entity_type text,
    target_entity_id uuid,
    link_basis text NOT NULL,
    confidence numeric(4,3) NOT NULL,
    parser_rule text NOT NULL,
    parser_version text NOT NULL,
    status text NOT NULL,
    rejection_reason text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, batch_id, source_sheet, source_row, source_cell_range, parser_rule)
);

CREATE TABLE command_audit (
    command_audit_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    command_name text NOT NULL,
    idempotency_key text NOT NULL,
    actor_id uuid REFERENCES actor_identity(actor_id),
    channel text NOT NULL,
    request_json jsonb NOT NULL,
    result_json jsonb,
    status text NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, command_name, idempotency_key)
);

CREATE TABLE outbox_event (
    outbox_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    aggregate_type text NOT NULL,
    aggregate_id uuid NOT NULL,
    event_type text NOT NULL,
    event_version integer NOT NULL DEFAULT 1,
    payload jsonb NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz,
    publish_attempts integer NOT NULL DEFAULT 0
);

CREATE INDEX outbox_unpublished_idx
    ON outbox_event (occurred_at)
    WHERE published_at IS NULL;

-- Implementation notes:
-- 1. canonical_part_id and supplier foreign keys are intentionally not constrained here;
--    the implementation migration must bind them to the existing ASPA product/supplier schemas.
-- 2. target_entity_id in legacy_note is polymorphic for staging compatibility;
--    application services must validate entity existence.
-- 3. row-level security and tenant policies must be added before SaaS/customer exposure.
-- 4. this contract must be converted into the repository's canonical migration framework
--    after inspecting the active WSL branch and existing database conventions.
