import csv
from io import StringIO

from fastapi import HTTPException

from src.models.queries import INBOX_VIEW, REVISION_VIEW, SHIFT_VIEW


def queue(db):
    return db.execute(SHIFT_VIEW + ' ORDER BY (s.evaluated_at IS NOT NULL), '
                      'CASE WHEN s.evaluated_at IS NULL THEN s.due_at END, s.due_at DESC,s.id DESC').fetchall()


def revisions(db, mailbox=None):
    rows = db.execute(REVISION_VIEW + ' AND (%s::text IS NULL OR r.mailbox=%s) ORDER BY j.finished_at DESC,rv.id DESC',
                      (mailbox, mailbox)).fetchall()
    counts = db.execute("""SELECT count(*) FILTER (WHERE status='pending') AS pending,
                                  count(*) FILTER (WHERE status='failed') AS failed
                           FROM recompute_jobs""").fetchone()
    return {'pending': counts['pending'], 'failed': counts['failed'], 'revisions': rows}


def messages(db, mailbox=None):
    return db.execute(INBOX_VIEW + ' WHERE (%s::text IS NULL OR d.mailbox=%s) ORDER BY d.delivered_at DESC,d.id DESC',
                      (mailbox, mailbox)).fetchall()


def message(db, receipt_id):
    header = db.execute(INBOX_VIEW + ' WHERE d.id=%s', (receipt_id,)).fetchone()
    if header is None:
        raise HTTPException(404, '投递回执不存在')
    header['evidence'] = db.execute('SELECT evidence FROM deliveries WHERE id=%s', (receipt_id,)).fetchone()['evidence']
    return header


def csv_report(receipt):
    evidence = receipt['evidence']
    out = StringIO()
    writer = csv.writer(out)
    writer.writerow(['receipt_id', 'shift_code', 'kind', 'mailbox', 'due_at', 'delivered_at', 'rule_version',
                     'threshold_m3_per_h', 'consecutive', 'cooldown_minutes', 'cooldown_until', 'outcome',
                     'sample_at', 'state', 'gas_m3', 'burner_minutes', 'intensity_m3_per_h', 'streak'])
    rule = evidence['rule']
    for slot in evidence['slots']:
        writer.writerow([receipt['id'], receipt['shift_code'], receipt['kind'], receipt['mailbox'],
                         receipt['due_at'].isoformat(), receipt['delivered_at'].isoformat(), rule['rule_version'],
                         rule['threshold'], rule['consecutive'], rule['cooldown_minutes'], evidence['cooldown_until'],
                         evidence['outcome'], *[slot[key] for key in ('sampled_at', 'state', 'gas_m3', 'burner_minutes', 'intensity', 'streak')]])
    return '\ufeff' + out.getvalue()
