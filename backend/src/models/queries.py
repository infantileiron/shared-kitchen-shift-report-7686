SHIFT_VIEW = '''
SELECT s.*, st.code AS station_code, st.label AS station_label, st.burner_count,
       r.version AS rule_version, r.threshold, r.consecutive, r.cooldown_minutes,
       r.delay_minutes, r.mailbox,
       (SELECT count(*) FROM readings WHERE shift_id=s.id) AS reading_count,
       report.id AS report_id, report.evidence->>'outcome' AS outcome
FROM shifts s JOIN stations st ON st.id=s.station_id JOIN rules r ON r.id=s.rule_id
LEFT JOIN deliveries report ON report.shift_id=s.id AND report.kind='report'
'''

RULE_VIEW = '''
SELECT r.*, st.label AS station_label, st.code AS station_code,
       r.version = max(r.version) OVER (PARTITION BY r.station_id,r.shift_kind) AS current
FROM rules r JOIN stations st ON st.id=r.station_id
'''

INBOX_VIEW = '''
SELECT d.id, d.kind, d.mailbox, d.delivered_at, s.id AS shift_id, s.code AS shift_code,
       s.shift_kind, s.starts_at, s.ends_at, s.due_at, st.label AS station_label,
       r.version AS rule_version, d.evidence->>'outcome' AS outcome
FROM deliveries d JOIN shifts s ON s.id=d.shift_id JOIN stations st ON st.id=s.station_id
JOIN rules r ON r.id=s.rule_id
'''

# Only revisions from completed jobs are visible; per shift the highest source version wins,
# so a stale recompute can never override a result computed from newer readings.
REVISION_VIEW = '''
SELECT rv.id, rv.shift_id, rv.previous_outcome, rv.revised_outcome, rv.reason, rv.detail,
       j.id AS job_id, j.source_version, j.finished_at,
       s.code AS shift_code, s.shift_kind, s.starts_at, s.ends_at, s.due_at,
       st.label AS station_label, r.mailbox, r.version AS rule_version
FROM reminder_revisions rv
JOIN recompute_jobs j ON j.id=rv.job_id AND j.status='done'
JOIN shifts s ON s.id=rv.shift_id
JOIN stations st ON st.id=s.station_id
JOIN rules r ON r.id=s.rule_id
WHERE rv.id = (SELECT rv2.id FROM reminder_revisions rv2
               JOIN recompute_jobs j2 ON j2.id=rv2.job_id AND j2.status='done'
               WHERE rv2.shift_id=rv.shift_id
               ORDER BY j2.source_version DESC, rv2.id DESC LIMIT 1)
'''
