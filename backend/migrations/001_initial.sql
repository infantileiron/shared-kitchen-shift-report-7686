CREATE TABLE IF NOT EXISTS accounts (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email text NOT NULL UNIQUE,
    display_name text NOT NULL,
    password_hash text NOT NULL,
    role text NOT NULL CHECK (role IN ('manager', 'recorder', 'observer'))
);
CREATE TABLE IF NOT EXISTS stations (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code text NOT NULL UNIQUE,
    label text NOT NULL,
    area text NOT NULL,
    burner_count integer NOT NULL CHECK (burner_count BETWEEN 1 AND 12)
);
CREATE TABLE IF NOT EXISTS rules (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    station_id bigint NOT NULL REFERENCES stations(id),
    shift_kind text NOT NULL CHECK (shift_kind IN ('morning', 'evening')),
    version integer NOT NULL CHECK (version > 0),
    threshold numeric(9,3) NOT NULL CHECK (threshold > 0),
    consecutive integer NOT NULL CHECK (consecutive BETWEEN 2 AND 12),
    cooldown_minutes integer NOT NULL CHECK (cooldown_minutes BETWEEN 0 AND 1440),
    delay_minutes integer NOT NULL CHECK (delay_minutes BETWEEN 0 AND 120),
    mailbox text NOT NULL CHECK (mailbox IN ('kitchen', 'operations')),
    created_by bigint NOT NULL REFERENCES accounts(id),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (station_id, shift_kind, version),
    UNIQUE (id, station_id, shift_kind)
);
CREATE TABLE IF NOT EXISTS shifts (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code text NOT NULL UNIQUE,
    station_id bigint NOT NULL REFERENCES stations(id),
    shift_kind text NOT NULL,
    starts_at timestamptz NOT NULL,
    ends_at timestamptz NOT NULL,
    due_at timestamptz NOT NULL,
    rule_id bigint NOT NULL,
    created_by bigint NOT NULL REFERENCES accounts(id),
    evaluated_at timestamptz,
    FOREIGN KEY (rule_id, station_id, shift_kind) REFERENCES rules(id, station_id, shift_kind),
    CONSTRAINT fixed_window UNIQUE (station_id, starts_at, ends_at),
    CHECK (starts_at < ends_at AND ends_at <= due_at)
);
CREATE INDEX IF NOT EXISTS shifts_pending ON shifts (due_at, id) WHERE evaluated_at IS NULL;
CREATE TABLE IF NOT EXISTS readings (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shift_id bigint NOT NULL REFERENCES shifts(id),
    sampled_at timestamptz NOT NULL,
    gas_m3 numeric(10,3) NOT NULL CHECK (gas_m3 >= 0),
    burner_minutes integer NOT NULL CHECK (burner_minutes >= 0),
    recorded_by bigint NOT NULL REFERENCES accounts(id),
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CHECK (burner_minutes > 0 OR gas_m3 = 0),
    UNIQUE (shift_id, sampled_at)
);
CREATE TABLE IF NOT EXISTS deliveries (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shift_id bigint NOT NULL REFERENCES shifts(id),
    kind text NOT NULL CHECK (kind IN ('report', 'alert')),
    mailbox text NOT NULL CHECK (mailbox IN ('kitchen', 'operations')),
    delivered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    evidence jsonb NOT NULL,
    UNIQUE (shift_id, kind)
);
CREATE INDEX IF NOT EXISTS delivery_alerts ON deliveries (shift_id) WHERE kind = 'alert';
CREATE TABLE IF NOT EXISTS audit_log (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor text NOT NULL,
    action text NOT NULL,
    target text NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
