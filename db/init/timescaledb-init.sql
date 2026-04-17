CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS presence_events (
  ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  room TEXT NOT NULL,
  device_id TEXT NOT NULL,
  alias TEXT,
  distance_m DOUBLE PRECISION,
  rssi INTEGER,
  topic TEXT NOT NULL,
  payload JSONB NOT NULL
);

SELECT create_hypertable('presence_events', 'ts', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_presence_events_device_ts
  ON presence_events (device_id, ts DESC);

CREATE INDEX IF NOT EXISTS idx_presence_events_room_ts
  ON presence_events (room, ts DESC);

CREATE INDEX IF NOT EXISTS idx_presence_events_alias_ts
  ON presence_events (alias, ts DESC);
