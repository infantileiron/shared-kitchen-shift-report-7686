from datetime import timedelta

from scripts.demo_data import ACCOUNTS, RULES, STATIONS, windows
from src.models.db import connect
from src.utils.auth import password_hash


def main():
    with connect() as db:
        db.execute('SELECT pg_advisory_xact_lock(521301)')
        for email, name, role in ACCOUNTS:
            if db.execute('SELECT 1 FROM accounts WHERE email=%s', (email,)).fetchone() is None:
                db.execute('''INSERT INTO accounts (email,display_name,password_hash,role)
                              VALUES (%s,%s,%s,%s) ON CONFLICT (email) DO NOTHING''',
                           (email, name, password_hash('HobShift#21'), role))
        users = {row['role']: row['id'] for row in db.execute('SELECT role,id FROM accounts WHERE email=ANY(%s)',
                                                           ([entry[0] for entry in ACCOUNTS],))}
        for station in STATIONS:
            db.execute('''INSERT INTO stations (code,label,area,burner_count) VALUES (%s,%s,%s,%s)
                          ON CONFLICT (code) DO NOTHING''', station)
        ids = {row['code']: row['id'] for row in db.execute('SELECT code,id FROM stations')}
        for code, kind, threshold, streak, cooldown, delay, mailbox in RULES:
            db.execute('''INSERT INTO rules (station_id,shift_kind,version,threshold,consecutive,cooldown_minutes,
                          delay_minutes,mailbox,created_by) VALUES (%s,%s,1,%s,%s,%s,%s,%s,%s)
                          ON CONFLICT (station_id,shift_kind,version) DO NOTHING''',
                       (ids[code], kind, threshold, streak, cooldown, delay, mailbox, users['manager']))
        for code, station, kind, start, duration, samples in windows():
            if db.execute('SELECT 1 FROM shifts WHERE code=%s', (code,)).fetchone():
                continue
            rule = db.execute('SELECT id,delay_minutes FROM rules WHERE station_id=%s AND shift_kind=%s AND version=1',
                              (ids[station], kind)).fetchone()
            end = start + timedelta(minutes=duration)
            due = end + timedelta(minutes=rule['delay_minutes'])
            shift = db.execute('''INSERT INTO shifts (code,station_id,shift_kind,starts_at,ends_at,due_at,rule_id,created_by)
                                  VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id''',
                               (code, ids[station], kind, start, end, due, rule['id'], users['recorder'])).fetchone()
            if shift:
                for slot, gas, minutes in samples:
                    db.execute('''INSERT INTO readings (shift_id,sampled_at,gas_m3,burner_minutes,recorded_by)
                                  VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''',
                               (shift['id'], start + timedelta(minutes=15*slot), gas, minutes, users['recorder']))
    print('Seed complete (natural keys preserved)')


if __name__ == '__main__':
    main()
