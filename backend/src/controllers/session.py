from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from src.models.db import audit, connect
from src.utils.auth import issue_token, token_subject, valid_password

bearer = HTTPBearer(auto_error=False)


def login(body):
    with connect() as db:
        actor = db.execute('SELECT * FROM accounts WHERE email=%s', (body.email.strip().lower(),)).fetchone()
        if actor is None or not valid_password(body.password, actor['password_hash']):
            raise HTTPException(401, '邮箱或密码无效')
        del actor['password_hash']
        audit(db, actor['email'], 'session.login', actor['id'])
        return {'token': issue_token(actor), 'account': actor}


def account(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    try:
        identity = token_subject(credentials.credentials) if credentials else None
    except (ValueError, InvalidTokenError):
        identity = None
    if identity is not None:
        with connect() as db:
            actor = db.execute('SELECT id,email,display_name,role FROM accounts WHERE id=%s', (identity,)).fetchone()
            if actor:
                return actor
    raise HTTPException(401, '登录已失效，请重新登录', headers={'WWW-Authenticate': 'Bearer'})


def allows(*roles):
    def permission(actor=Depends(account)):
        if actor['role'] not in roles:
            raise HTTPException(403, '当前角色无此操作权限')
        return actor
    return permission
