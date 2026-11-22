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
