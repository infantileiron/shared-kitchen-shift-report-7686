import logging
from datetime import timedelta

from psycopg.types.json import Jsonb

from src.constants.enums import Outcome, Reason
from src.models.db import audit, connect
from src.models.queries import SHIFT_VIEW
from src.services.evaluate import evaluate
from src.utils.encoding import payload

log = logging.getLogger('scheduler')

MAX_ATTEMPTS = 5

# Effective state = recorded report outcomes amended by completed recompute jobs. The job
# currently running is excluded so the chain walk always converges towards the state that
# was visible before its own backfill started.
EFFECTIVE = '''
    SELECT s.id, s.due_at, s.station_id, s.shift_kind,
           coalesce(best.revised_outcome, rpt.evidence->>'outcome') AS outcome
    FROM shifts s
    JOIN deliveries rpt ON rpt.shift_id=s.id AND rpt.kind='report'
    LEFT JOIN (
        SELECT DISTINCT ON (rv.shift_id) rv.shift_id, rv.revised_outcome
        FROM reminder_revisions rv
        JOIN recompute_jobs j ON j.id=rv.job_id AND j.status='done' AND j.id!=%s
        ORDER BY rv.shift_id, j.source_version DESC, rv.id DESC
    ) best ON best.shift_id=s.id
'''


def alert_due_before(db, shift, exclude_job):
    row = db.execute(f'''WITH effective AS ({EFFECTIVE})
                         SELECT due_at FROM effective
                         WHERE station_id=%s AND shift_kind=%s AND (due_at,id)<(%s,%s) AND outcome=%s
                         ORDER BY due_at DESC,id DESC LIMIT 1''',
                     (exclude_job, shift['station_id'], shift['shift_kind'],
                      shift['due_at'], shift['id'], Outcome.ALERTED)).fetchone()
    return row['due_at'] if row else None


def effective_state(db, shift, exclude_job):
    revision = db.execute('''SELECT rv.revised_outcome, rv.detail FROM reminder_revisions rv
                             JOIN recompute_jobs j ON j.id=rv.job_id AND j.status='done'
                             WHERE rv.shift_id=%s AND j.id!=%s
                             ORDER BY j.source_version DESC, rv.id DESC LIMIT 1''',
                          (shift['id'], exclude_job)).fetchone()
    recorded = db.execute("SELECT evidence FROM deliveries WHERE shift_id=%s AND kind='report'",
                          (shift['id'],)).fetchone()
    if recorded is None:
        raise ValueError(f"shift {shift['id']} has no dispatched report to recompute")
    if revision:
        streak = (revision['detail'].get('longest_streak') or {}).get('new')
        return {'outcome': revision['revised_outcome'], 'streak': streak}
    return {'outcome': recorded['evidence']['outcome'], 'streak': recorded['evidence']['longest_streak']}


def run_chain(db, job):
    trigger = db.execute(SHIFT_VIEW + ' WHERE s.id=%s', (job['shift_id'],)).fetchone()
    if trigger is None or trigger['evaluated_at'] is None:
        raise ValueError(f"shift {job['shift_id']} has no dispatched report to recompute")
    prev_due = alert_due_before(db, trigger, job['id'])
    current, first, seq = trigger, True, 0
    while current:
        entries = db.execute('SELECT * FROM readings WHERE shift_id=%s ORDER BY sampled_at', (current['id'],)).fetchall()
        # Each shift is recomputed under its originally bound rule and planned due time.
        evidence = evaluate(current, entries, prev_due)
        baseline = effective_state(db, current, job['id'])
        baseline_due = alert_due_before(db, current, job['id'])
        if not first and baseline_due == prev_due and baseline['outcome'] == evidence['outcome']:
            break  # Cooldown state coincides with the pre-backfill state again.
        if evidence['outcome'] != baseline['outcome']:
            seq += 1
            cooldown = timedelta(minutes=current['cooldown_minutes'])
            detail = {'trigger': first, 'source_version': job['source_version'],
                      'previous_alert_due': {'old': baseline_due, 'new': prev_due},
                      'cooldown_until': {'old': baseline_due + cooldown if baseline_due else None,
                                         'new': evidence['cooldown_until']},
                      'longest_streak': {'old': baseline['streak'], 'new': evidence['longest_streak']},
                      'consecutive': current['consecutive'], 'threshold': str(current['threshold'])}
            db.execute('''INSERT INTO reminder_revisions (job_id,shift_id,seq,previous_outcome,revised_outcome,reason,detail)
                          VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (job_id,shift_id) DO NOTHING''',
                       (job['id'], current['id'], seq, baseline['outcome'], evidence['outcome'],
                        Reason.READINGS_BACKFILLED if first else Reason.COOLDOWN_BOUNDARY,
                        Jsonb(payload(detail))))
        if evidence['outcome'] == Outcome.ALERTED:
            prev_due = current['due_at']
        following = db.execute('''SELECT id FROM shifts WHERE station_id=%s AND shift_kind=%s
                                  AND evaluated_at IS NOT NULL AND (due_at,id)>(%s,%s)
                                  ORDER BY due_at,id LIMIT 1''',
                               (current['station_id'], current['shift_kind'],
                                current['due_at'], current['id'])).fetchone()
        current = db.execute(SHIFT_VIEW + ' WHERE s.id=%s', (following['id'],)).fetchone() if following else None
        first = False


def recompute_one():
    job_id = None
    try:
        with connect() as db:
            # Share the scheduler lock so a recompute never races a live dispatch.
            if not db.execute('SELECT pg_try_advisory_xact_lock(521313) AS acquired').fetchone()['acquired']:
                return False
            job = db.execute("SELECT * FROM recompute_jobs WHERE status='pending' ORDER BY id LIMIT 1 FOR UPDATE").fetchone()
            if job is None:
                return False
            job_id = job['id']
            # Revisions, job state and audit commit together: a failed run leaves nothing
            # behind, so a retry never duplicates records, and changes appear only once
            # the whole chain has been recomputed.
            run_chain(db, job)
            db.execute("UPDATE recompute_jobs SET status='done', finished_at=clock_timestamp() WHERE id=%s", (job_id,))
            audit(db, 'worker', 'recompute.completed', job_id)
            return True
    except Exception:
        log.exception('Recompute job %s failed', job_id)
        if job_id is not None:
            try:
                with connect() as db:
                    row = db.execute('''UPDATE recompute_jobs SET attempts=attempts+1,
                                        status=CASE WHEN attempts+1>=%s THEN 'failed' ELSE 'pending' END
                                        WHERE id=%s AND status='pending' RETURNING status''',
                                     (MAX_ATTEMPTS, job_id)).fetchone()
                    if row:
                        audit(db, 'worker', 'recompute.failed' if row['status'] == 'failed' else 'recompute.retry', job_id)
            except Exception:
                log.exception('Could not mark recompute job %s', job_id)
        return True
