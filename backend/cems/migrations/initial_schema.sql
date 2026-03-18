-- =============================================================================
-- CEMS - Company Equipment & Inventory Management System
-- PostgreSQL DDL - Initial Schema
-- =============================================================================

-- ---------- Extension ----------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------- ENUM types ----------
CREATE TYPE cems_user_role        AS ENUM ('ADMIN', 'MANAGER', 'EMPLOYEE');
CREATE TYPE cems_asset_status     AS ENUM ('ACTIVE', 'IN_TRANSFER', 'IN_WAREHOUSE', 'RETIRED');
CREATE TYPE cems_transfer_status  AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'COMPLETED');
CREATE TYPE cems_return_status    AS ENUM ('PENDING', 'APPROVED', 'REJECTED');
CREATE TYPE cems_retirement_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED');
CREATE TYPE cems_signature_type   AS ENUM ('TRANSFER_RECEIPT', 'WAREHOUSE_RETURN', 'RETIREMENT_APPROVAL');
CREATE TYPE cems_alert_type       AS ENUM ('LOW_STOCK', 'OUT_OF_STOCK');
CREATE TYPE cems_document_type    AS ENUM ('WARRANTY', 'INVOICE', 'OTHER');

-- ---------- Helper: auto-update updated_at ----------
CREATE OR REPLACE FUNCTION cems_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW() AT TIME ZONE 'utc';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- USERS
-- =============================================================================
CREATE TABLE cems_users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    role            cems_user_role NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    warehouse_id    UUID,                   -- FK added after cems_warehouses
    created_at      TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at      TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX idx_cems_users_email ON cems_users (email);

CREATE TRIGGER trg_cems_users_updated_at
    BEFORE UPDATE ON cems_users
    FOR EACH ROW EXECUTE FUNCTION cems_set_updated_at();

-- =============================================================================
-- WAREHOUSES
-- =============================================================================
CREATE TABLE cems_warehouses (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                VARCHAR(255) NOT NULL,
    location            VARCHAR(500),
    current_manager_id  UUID REFERENCES cems_users(id) ON DELETE SET NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at          TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TRIGGER trg_cems_warehouses_updated_at
    BEFORE UPDATE ON cems_warehouses
    FOR EACH ROW EXECUTE FUNCTION cems_set_updated_at();

-- Now add the FK from users -> warehouses
ALTER TABLE cems_users
    ADD CONSTRAINT fk_cems_users_warehouse
    FOREIGN KEY (warehouse_id) REFERENCES cems_warehouses(id) ON DELETE SET NULL;

-- =============================================================================
-- AREAS
-- =============================================================================
CREATE TABLE cems_areas (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name         VARCHAR(255) NOT NULL,
    warehouse_id UUID NOT NULL REFERENCES cems_warehouses(id) ON DELETE CASCADE,
    description  TEXT,
    created_at   TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at   TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TRIGGER trg_cems_areas_updated_at
    BEFORE UPDATE ON cems_areas
    FOR EACH ROW EXECUTE FUNCTION cems_set_updated_at();

-- =============================================================================
-- MANAGER HISTORY
-- =============================================================================
CREATE TABLE cems_manager_history (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    warehouse_id        UUID NOT NULL REFERENCES cems_warehouses(id) ON DELETE CASCADE,
    previous_manager_id UUID REFERENCES cems_users(id) ON DELETE SET NULL,
    new_manager_id      UUID NOT NULL REFERENCES cems_users(id) ON DELETE CASCADE,
    changed_by_id       UUID NOT NULL REFERENCES cems_users(id) ON DELETE CASCADE,
    changed_at          TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    reason              TEXT
);

-- =============================================================================
-- ASSET CATEGORIES
-- =============================================================================
CREATE TABLE cems_asset_categories (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at  TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TRIGGER trg_cems_asset_categories_updated_at
    BEFORE UPDATE ON cems_asset_categories
    FOR EACH ROW EXECUTE FUNCTION cems_set_updated_at();

-- =============================================================================
-- PROJECTS
-- =============================================================================
CREATE TABLE cems_projects (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL,
    code        VARCHAR(50)  NOT NULL UNIQUE,
    description TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at  TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX idx_cems_projects_code ON cems_projects (code);

CREATE TRIGGER trg_cems_projects_updated_at
    BEFORE UPDATE ON cems_projects
    FOR EACH ROW EXECUTE FUNCTION cems_set_updated_at();

-- =============================================================================
-- FIXED ASSETS
-- =============================================================================
CREATE TABLE cems_fixed_assets (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                 VARCHAR(255) NOT NULL,
    serial_number        VARCHAR(255) NOT NULL UNIQUE,
    category_id          UUID NOT NULL REFERENCES cems_asset_categories(id) ON DELETE RESTRICT,
    current_custodian_id UUID REFERENCES cems_users(id) ON DELETE SET NULL,
    current_area_id      UUID REFERENCES cems_areas(id) ON DELETE SET NULL,
    project_id           UUID REFERENCES cems_projects(id) ON DELETE SET NULL,
    status               cems_asset_status NOT NULL DEFAULT 'ACTIVE',
    purchase_date        DATE,
    warranty_expiry      DATE,
    notes                TEXT,
    created_at           TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at           TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX idx_cems_fixed_assets_serial      ON cems_fixed_assets (serial_number);
CREATE INDEX idx_cems_fixed_assets_status       ON cems_fixed_assets (status);
CREATE INDEX idx_cems_fixed_assets_custodian    ON cems_fixed_assets (current_custodian_id);
CREATE INDEX idx_cems_fixed_assets_area         ON cems_fixed_assets (current_area_id);
CREATE INDEX idx_cems_fixed_assets_category     ON cems_fixed_assets (category_id);
CREATE INDEX idx_cems_fixed_assets_project      ON cems_fixed_assets (project_id);

CREATE TRIGGER trg_cems_fixed_assets_updated_at
    BEFORE UPDATE ON cems_fixed_assets
    FOR EACH ROW EXECUTE FUNCTION cems_set_updated_at();

-- =============================================================================
-- ASSET HISTORY
-- =============================================================================
CREATE TABLE cems_asset_history (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id          UUID NOT NULL REFERENCES cems_fixed_assets(id) ON DELETE CASCADE,
    action            VARCHAR(100) NOT NULL,
    actor_id          UUID NOT NULL REFERENCES cems_users(id) ON DELETE SET NULL,
    from_custodian_id UUID REFERENCES cems_users(id) ON DELETE SET NULL,
    to_custodian_id   UUID REFERENCES cems_users(id) ON DELETE SET NULL,
    from_area_id      UUID REFERENCES cems_areas(id) ON DELETE SET NULL,
    to_area_id        UUID REFERENCES cems_areas(id) ON DELETE SET NULL,
    notes             TEXT,
    timestamp         TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX idx_cems_asset_history_asset ON cems_asset_history (asset_id);

-- =============================================================================
-- CONSUMABLE ITEMS
-- =============================================================================
CREATE TABLE cems_consumable_items (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                 VARCHAR(255) NOT NULL,
    category_id          UUID NOT NULL REFERENCES cems_asset_categories(id) ON DELETE RESTRICT,
    area_id              UUID NOT NULL REFERENCES cems_areas(id) ON DELETE CASCADE,
    quantity             NUMERIC(10,4) NOT NULL DEFAULT 0,
    unit                 VARCHAR(50)  NOT NULL,
    low_stock_threshold  NUMERIC(10,4) NOT NULL DEFAULT 0,
    reorder_quantity     NUMERIC(10,4) NOT NULL DEFAULT 0,
    created_at           TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at           TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    CONSTRAINT chk_quantity_non_negative CHECK (quantity >= 0)
);

CREATE INDEX idx_cems_consumable_items_category ON cems_consumable_items (category_id);
CREATE INDEX idx_cems_consumable_items_area     ON cems_consumable_items (area_id);

CREATE TRIGGER trg_cems_consumable_items_updated_at
    BEFORE UPDATE ON cems_consumable_items
    FOR EACH ROW EXECUTE FUNCTION cems_set_updated_at();

-- =============================================================================
-- CONSUMPTION LOGS
-- =============================================================================
CREATE TABLE cems_consumption_logs (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id           UUID NOT NULL REFERENCES cems_consumable_items(id) ON DELETE CASCADE,
    consumed_by_id    UUID NOT NULL REFERENCES cems_users(id) ON DELETE SET NULL,
    project_id        UUID REFERENCES cems_projects(id) ON DELETE SET NULL,
    quantity_consumed NUMERIC(10,4) NOT NULL,
    consumed_at       TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    notes             TEXT,
    CONSTRAINT chk_consumed_positive CHECK (quantity_consumed > 0)
);

CREATE INDEX idx_cems_consumption_logs_item ON cems_consumption_logs (item_id);

-- =============================================================================
-- STOCK ALERTS
-- =============================================================================
CREATE TABLE cems_stock_alerts (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id           UUID NOT NULL REFERENCES cems_consumable_items(id) ON DELETE CASCADE,
    alert_type        cems_alert_type NOT NULL,
    quantity_at_alert NUMERIC(10,4) NOT NULL,
    resolved          BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at       TIMESTAMP,
    created_at        TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX idx_cems_stock_alerts_item ON cems_stock_alerts (item_id);

-- =============================================================================
-- SIGNATURES
-- =============================================================================
CREATE TABLE cems_signatures (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signer_id       UUID NOT NULL REFERENCES cems_users(id) ON DELETE CASCADE,
    signature_hash  VARCHAR(64)  NOT NULL,
    signed_at       TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    signature_type  cems_signature_type NOT NULL,
    reference_id    UUID NOT NULL,
    ip_address      VARCHAR(45)
);

-- =============================================================================
-- TRANSFERS
-- =============================================================================
CREATE TABLE cems_transfers (
    id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id               UUID NOT NULL REFERENCES cems_fixed_assets(id) ON DELETE CASCADE,
    from_user_id           UUID NOT NULL REFERENCES cems_users(id) ON DELETE CASCADE,
    to_user_id             UUID NOT NULL REFERENCES cems_users(id) ON DELETE CASCADE,
    from_area_id           UUID REFERENCES cems_areas(id) ON DELETE SET NULL,
    to_area_id             UUID REFERENCES cems_areas(id) ON DELETE SET NULL,
    initiated_by_id        UUID NOT NULL REFERENCES cems_users(id) ON DELETE CASCADE,
    initiated_at           TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    status                 cems_transfer_status NOT NULL DEFAULT 'PENDING',
    recipient_signature_id UUID REFERENCES cems_signatures(id) ON DELETE SET NULL,
    notes                  TEXT,
    created_at             TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at             TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX idx_cems_transfers_asset  ON cems_transfers (asset_id);
CREATE INDEX idx_cems_transfers_status ON cems_transfers (status);

CREATE TRIGGER trg_cems_transfers_updated_at
    BEFORE UPDATE ON cems_transfers
    FOR EACH ROW EXECUTE FUNCTION cems_set_updated_at();

-- =============================================================================
-- WAREHOUSE RETURNS
-- =============================================================================
CREATE TABLE cems_warehouse_returns (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id             UUID NOT NULL REFERENCES cems_fixed_assets(id) ON DELETE CASCADE,
    returned_by_id       UUID NOT NULL REFERENCES cems_users(id) ON DELETE CASCADE,
    warehouse_id         UUID NOT NULL REFERENCES cems_warehouses(id) ON DELETE CASCADE,
    return_area_id       UUID REFERENCES cems_areas(id) ON DELETE SET NULL,
    manager_id           UUID REFERENCES cems_users(id) ON DELETE SET NULL,
    status               cems_return_status NOT NULL DEFAULT 'PENDING',
    manager_signature_id UUID REFERENCES cems_signatures(id) ON DELETE SET NULL,
    return_reason        TEXT,
    requested_at         TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    resolved_at          TIMESTAMP,
    created_at           TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at           TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX idx_cems_warehouse_returns_asset ON cems_warehouse_returns (asset_id);

CREATE TRIGGER trg_cems_warehouse_returns_updated_at
    BEFORE UPDATE ON cems_warehouse_returns
    FOR EACH ROW EXECUTE FUNCTION cems_set_updated_at();

-- =============================================================================
-- ASSET RETIREMENTS
-- =============================================================================
CREATE TABLE cems_asset_retirements (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id        UUID NOT NULL REFERENCES cems_fixed_assets(id) ON DELETE CASCADE,
    requested_by_id UUID NOT NULL REFERENCES cems_users(id) ON DELETE CASCADE,
    approved_by_id  UUID REFERENCES cems_users(id) ON DELETE SET NULL,
    reason          TEXT NOT NULL,
    disposal_method VARCHAR(255) NOT NULL,
    status          cems_retirement_status NOT NULL DEFAULT 'PENDING',
    requested_at    TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    approved_at     TIMESTAMP,
    notes           TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at      TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX idx_cems_asset_retirements_asset ON cems_asset_retirements (asset_id);

CREATE TRIGGER trg_cems_asset_retirements_updated_at
    BEFORE UPDATE ON cems_asset_retirements
    FOR EACH ROW EXECUTE FUNCTION cems_set_updated_at();

-- =============================================================================
-- DOCUMENTS
-- =============================================================================
CREATE TABLE cems_documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type     VARCHAR(50)   NOT NULL,
    entity_id       UUID          NOT NULL,
    document_type   cems_document_type NOT NULL,
    filename        VARCHAR(500)  NOT NULL,
    file_path       VARCHAR(1000) NOT NULL,
    uploaded_by_id  UUID NOT NULL REFERENCES cems_users(id) ON DELETE SET NULL,
    uploaded_at     TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    expiry_date     DATE,
    created_at      TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at      TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX idx_cems_documents_entity ON cems_documents (entity_type, entity_id);

CREATE TRIGGER trg_cems_documents_updated_at
    BEFORE UPDATE ON cems_documents
    FOR EACH ROW EXECUTE FUNCTION cems_set_updated_at();
