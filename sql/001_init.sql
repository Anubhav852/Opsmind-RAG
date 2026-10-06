CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE events (
  id         UUID PRIMARY KEY,
  tenant_id  TEXT NOT NULL DEFAULT 'demo',
  source     TEXT NOT NULL,
  kind       TEXT NOT NULL,
  service    TEXT NOT NULL,
  ts         TIMESTAMPTZ NOT NULL,
  title      TEXT NOT NULL,
  body       TEXT NOT NULL DEFAULT '',
  acl        TEXT[] NOT NULL DEFAULT '{public}',
  flagged    BOOLEAN NOT NULL DEFAULT FALSE,
  embedding  vector(384),
  tsv        tsvector GENERATED ALWAYS AS
             (to_tsvector('english', title || ' ' || body)) STORED
);

CREATE INDEX events_tenant_ts_idx ON events (tenant_id, ts);
CREATE INDEX events_service_ts_idx ON events (service, ts);
CREATE INDEX events_tsv_idx ON events USING gin (tsv);

CREATE TABLE edges (
  id         BIGSERIAL PRIMARY KEY,
  src        TEXT NOT NULL,
  dst        TEXT NOT NULL,
  rel        TEXT NOT NULL DEFAULT 'DEPENDS_ON',
  valid_from TIMESTAMPTZ NOT NULL,
  valid_to   TIMESTAMPTZ,
  UNIQUE (src, dst, rel, valid_from)
);

CREATE TABLE investigations (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created     TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by  TEXT NOT NULL,
  alert       JSONB NOT NULL,
  result      JSONB NOT NULL,
  status      TEXT NOT NULL DEFAULT 'proposed',
  approved_by TEXT
);

CREATE TABLE audit_log (
  id      BIGSERIAL PRIMARY KEY,
  ts      TIMESTAMPTZ NOT NULL DEFAULT now(),
  actor   TEXT NOT NULL,
  action  TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'
);

CREATE FUNCTION audit_immutable() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'audit_log is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_no_mod
BEFORE UPDATE OR DELETE ON audit_log
FOR EACH ROW EXECUTE FUNCTION audit_immutable();
