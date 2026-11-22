from datetime import timedelta

from fastapi import HTTPException

from src.constants.enums import SLOT_MINUTES
from src.models.db import audit
from src.models.queries import RULE_VIEW, SHIFT_VIEW


def station_lock(db, station_id):
    station = db.execute('SELECT * FROM stations WHERE id=%s FOR UPDATE', (station_id,)).fetchone()
    if station is None:
        raise HTTPException(404, '灶台不存在')
    return station


def rules(db):
    return db.execute(RULE_VIEW + ' ORDER BY r.station_id, r.shift_kind DESC, r.version DESC').fetchall()


def new_rule(db, actor, body):
    station_lock(db, body.station_id)
    args = body.model_dump(mode='json')
    args['author'] = actor['id']
    rule = db.execute('''INSERT INTO rules (station_id,shift_kind,version,threshold,consecutive,
                          cooldown_minutes,delay_minutes,mailbox,created_by)
        VALUES (%(station_id)s,%(shift_kind)s,
          (SELECT coalesce(max(version),0)+1 FROM rules WHERE station_id=%(station_id)s AND shift_kind=%(shift_kind)s),
          %(threshold)s,%(consecutive)s,%(cooldown_minutes)s,%(delay_minutes)s,%(mailbox)s,%(author)s)
        RETURNING *''', args).fetchone()
    audit(db, actor['email'], 'rule.published', rule['id'])
    return rule


def shifts(db):
    return db.execute(SHIFT_VIEW + ' ORDER BY s.ends_at DESC,s.id DESC').fetchall()


def shift_detail(db, shift_id):
    shift = db.execute(SHIFT_VIEW + ' WHERE s.id=%s', (shift_id,)).fetchone()
    if shift is None:
        raise HTTPException(404, '班次不存在')
    entries = db.execute('SELECT * FROM readings WHERE shift_id=%s ORDER BY sampled_at', (shift_id,)).fetchall()
    return {'shift': shift, 'readings': entries}


def new_shift(db, actor, body):
    if not timedelta(minutes=1) <= body.ends_at - body.starts_at <= timedelta(hours=16):
        raise HTTPException(422, '班次长度须为 1 分钟至 16 小时')
    if body.starts_at.second or body.starts_at.microsecond:
        raise HTTPException(422, '开班时间须对齐整分钟')
    station_lock(db, body.station_id)
    rule = db.execute('''SELECT * FROM rules WHERE station_id=%s AND shift_kind=%s
                         ORDER BY version DESC LIMIT 1''', (body.station_id, body.shift_kind)).fetchone()
    if rule is None:
        raise HTTPException(409, '该灶台与班别尚未发布规则')
    due = body.ends_at + timedelta(minutes=rule['delay_minutes'])
    now = db.execute('SELECT clock_timestamp() AS now').fetchone()['now']
    if due <= now:
        raise HTTPException(422, '计划投递时刻须晚于现在')
    if db.execute('''SELECT 1 FROM shifts WHERE station_id=%s AND starts_at<%s AND ends_at>%s LIMIT 1''',
                  (body.station_id, body.ends_at, body.starts_at)).fetchone():
        raise HTTPException(409, '该灶台已有同一时段或与之重叠的班次')
    shift = db.execute('''INSERT INTO shifts (code,station_id,shift_kind,starts_at,ends_at,due_at,rule_id,created_by)
                          VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (code) DO NOTHING RETURNING *''',
                       (body.code, body.station_id, body.shift_kind, body.starts_at, body.ends_at,
                        due, rule['id'], actor['id'])).fetchone()
    if shift is None:
        raise HTTPException(409, '班次编号已存在')
    audit(db, actor['email'], 'shift.created', shift['id'])
    return shift


def new_reading(db, actor, shift_id, body):
    shift = db.execute('''SELECT s.*, st.burner_count FROM shifts s JOIN stations st ON st.id=s.station_id
                          WHERE s.id=%s FOR UPDATE OF s''', (shift_id,)).fetchone()
    if shift is None:
        raise HTTPException(404, '班次不存在')
    now = db.execute('SELECT clock_timestamp() AS now').fetchone()['now']
    if shift['evaluated_at'] or now >= shift['due_at']:
        raise HTTPException(409, '已到计划投递时间，班次用气账已冻结')
    offset = body.sampled_at - shift['starts_at']
    if offset < timedelta(0) or body.sampled_at >= shift['ends_at'] or offset % timedelta(minutes=SLOT_MINUTES):
        raise HTTPException(422, '读数时间须为班次内从开班起每 15 分钟的刻度')
    slot_end = min(shift['ends_at'], body.sampled_at + timedelta(minutes=SLOT_MINUTES))
    if slot_end > now:
        raise HTTPException(422, '该测量时格尚未结束')
    max_minutes = int((slot_end - body.sampled_at).total_seconds() * shift['burner_count'] // 60)
    if body.burner_minutes > max_minutes or (body.burner_minutes == 0 and body.gas_m3 > 0):
        raise HTTPException(422, '炉分钟须在灶眼与时格容量内，零炉分钟只允许零用气')
    reading = db.execute('''INSERT INTO readings (shift_id,sampled_at,gas_m3,burner_minutes,recorded_by)
                            VALUES (%s,%s,%s,%s,%s) ON CONFLICT (shift_id,sampled_at) DO NOTHING RETURNING *''',
                         (shift_id, body.sampled_at, body.gas_m3, body.burner_minutes, actor['id'])).fetchone()
    if reading is None:
        raise HTTPException(409, '同一班次的测量时格已登记')
    audit(db, actor['email'], 'reading.recorded', reading['id'])
    return reading
