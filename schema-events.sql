CREATE TABLE IF NOT EXISTS schema_events (
    id TEXT PRIMARY KEY NOT NULL UNIQUE,
    title TEXT NOT NULL,
    day_of_week SMALLINT NOT NULL,
    time_of_day TEXT,
    location_city TEXT NOT NULL,
    venue_zone_type TEXT NOT NULL
);