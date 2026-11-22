ALTER TABLE readings ADD COLUMN IF NOT EXISTS source_version integer NOT NULL DEFAULT 0;
CREATE TABLE IF NOT EXISTS recompute_jobs (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shift_id bigint NOT NULL REFERENCES shifts(id),
    source_version integer NOT NULL CHECK (source_version > 0),
    created_by bigint NOT NULL REFERENCES accounts(id),
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'done', 'failed')),
    attempts integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    finished_at timestamptz,
    UNIQUE (shift_id, source_version)
);
CREATE INDEX IF NOT EXISTS recompute_pending ON recompute_jobs (id) WHERE status = 'pending';
CREATE TABLE IF NOT EXISTS reminder_revisions (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_id bigint NOT NULL REFERENCES recompute_jobs(id),
    shift_id bigint NOT NULL REFERENCES shifts(id),
    seq integer NOT NULL,
    previous_outcome text NOT NULL,
    revised_outcome text NOT NULL,
    reason text NOT NULL CHECK (reason IN ('readings_backfilled', 'cooldown_boundary')),
    detail jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (job_id, shift_id)
);
