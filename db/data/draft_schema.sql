CREATE TABLE IF NOT EXISTS betters (
    id INTEGER PRIMARY KEY,
    draft_id INTEGER,
    value REAL,
    needed REAL,
    current REAL
);

CREATE UNIQUE INDEX better_base ON betters (id, draft_id);
CREATE INDEX better_needed ON betters (needed);

CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    draft_id INTEGER,
    item_id INTEGER,
    value REAL,
    better INTEGER REFERENCES betters
);

CREATE INDEX item_base ON items (id, draft_id, item_id);
CREATE INDEX item_value ON items (value);

