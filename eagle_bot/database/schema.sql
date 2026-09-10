PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS identities (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL CHECK (kind IN ('human','organization','agent')),
    display_name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS work_orders (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    objective TEXT NOT NULL,
    coworker TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES identities(id)
);

CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    details_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_work_orders_owner ON work_orders(owner_id);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_events(actor_id);
