CREATE TABLE IF NOT EXISTS schema_urls (
    id TEXT PRIMARY KEY NOT NULL UNIQUE,
    url TEXT NOT NULL UNIQUE,
    Status TEXT DEFAULT 'Pending'
    CHECK (Status IN ('Pending', 'In Progress', 'Success', 'Failed','Dropped')),
    no_attempts INT DEFAULT 0,
    last_attempt TIMESTAMP DEFAULT NULL
);