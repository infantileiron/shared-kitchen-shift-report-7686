import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from src.config.settings import JWT_SECRET


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 310_000)
    return f'{salt}${digest.hex()}'


def valid_password(password, stored):
    salt, _, _ = stored.partition('$')
    return hmac.compare_digest(password_hash(password, salt), stored)


def issue_token(actor):
    now = datetime.now(timezone.utc)
    return jwt.encode({'sub': str(actor['id']), 'iat': now, 'exp': now + timedelta(hours=8)},
                      JWT_SECRET, algorithm='HS256')


def token_subject(token):
    claims = jwt.decode(token, JWT_SECRET, algorithms=['HS256'], options={'require': ['sub', 'exp']})
    return int(claims['sub'])
