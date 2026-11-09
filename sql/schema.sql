-- ============================================================
-- SuperStore Sales Analytics — Database Schema
-- ============================================================
-- Database: SQLite
-- Table   : orders
--
-- This schema documents the structure of the orders table
-- as loaded from the cleaned dataset.
-- ============================================================

CREATE TABLE IF NOT EXISTS orders (
    order_id        TEXT,
    order_date      TEXT,        -- ISO date string (YYYY-MM-DD)
    ship_date       TEXT,        -- ISO date string (YYYY-MM-DD)
    ship_mode       TEXT,
    customer_name   TEXT,
    segment         TEXT,        -- Consumer, Corporate, Home Office
    state           TEXT,
    country         TEXT,
    market          TEXT,        -- APAC, EU, US, LATAM, EMEA, Africa, Canada
    region          TEXT,
    product_id      TEXT,
    category        TEXT,        -- Furniture, Office Supplies, Technology
    sub_category    TEXT,
    product_name    TEXT,
    sales           REAL,
    quantity        INTEGER,
    discount        REAL,        -- 0.0 to 0.85+
    profit          REAL,        -- can be negative (losses)
    shipping_cost   REAL,
    order_priority  TEXT,        -- Critical, High, Medium, Low
    year            INTEGER,
    month           INTEGER,
    quarter         INTEGER,
    order_month     TEXT,        -- YYYY-MM
    shipping_days   INTEGER,
    profit_margin   REAL         -- profit / sales
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_order_date   ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_market       ON orders(market);
CREATE INDEX IF NOT EXISTS idx_category     ON orders(category);
CREATE INDEX IF NOT EXISTS idx_segment      ON orders(segment);
CREATE INDEX IF NOT EXISTS idx_year         ON orders(year);
