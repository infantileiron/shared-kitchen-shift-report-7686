from psycopg.types.json import Jsonb

from src.constants.enums import Outcome
from src.models.db import audit, connect
from src.models.queries import SHIFT_VIEW
from src.services.evaluate import evaluate
from src.utils.encoding import payload


def dispatch_one():
    with connect() as db:
        # Dispatch in global schedule order so another worker cannot advance a cooldown mid-evaluation.
        if not db.execute('SELECT pg_try_advisory_xact_lock(521313) AS acquired').fetchone()['acquired']:
            return False
        job = db.execute('''SELECT id FROM shifts WHERE evaluated_at IS NULL AND due_at <= statement_timestamp()
                            ORDER BY due_at,id LIMIT 1 FOR UPDATE''').fetchone()
        if job is None:
            return False
        shift = db.execute(SHIFT_VIEW + ' WHERE s.id=%s', (job['id'],)).fetchone()
        entries = db.execute('SELECT * FROM readings WHERE shift_id=%s ORDER BY sampled_at', (shift['id'],)).fetchall()
        prior = db.execute('''SELECT s.due_at FROM shifts s JOIN deliveries d ON d.shift_id=s.id AND d.kind='alert'
                              WHERE s.station_id=%s AND s.shift_kind=%s AND (s.due_at,s.id)<(%s,%s)
                              ORDER BY s.due_at DESC,s.id DESC LIMIT 1''',
                           (shift['station_id'], shift['shift_kind'], shift['due_at'], shift['id'])).fetchone()
        evidence = evaluate(shift, entries, prior['due_at'] if prior else None)
        kinds = ['report']
        if evidence['outcome'] == Outcome.ALERTED:
            kinds.append('alert')
        for kind in kinds:
            receipt = db.execute('''INSERT INTO deliveries (shift_id,kind,mailbox,evidence) VALUES (%s,%s,%s,%s)
                        ON CONFLICT (shift_id,kind) DO NOTHING RETURNING id''',
                        (shift['id'], kind, shift['mailbox'], Jsonb(payload(evidence)))).fetchone()
            if receipt:
                audit(db, 'worker', f'delivery.{kind}', receipt['id'])
        db.execute('UPDATE shifts SET evaluated_at=clock_timestamp() WHERE id=%s', (shift['id'],))
        return True
