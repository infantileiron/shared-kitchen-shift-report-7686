import psycopg
from psycopg.rows import dict_row
from redis import Redis

from src.config.settings import DB, REDIS_URL


def connect():
    return psycopg.connect(**DB, row_factory=dict_row)


cache = Redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=2, socket_connect_timeout=2)


def audit(db, actor, action, target):
    db.execute('INSERT INTO audit_log (actor, action, target) VALUES (%s,%s,%s)',
               (actor, action, str(target)))
