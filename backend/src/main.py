import logging

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from redis import RedisError

from src.middlewares.http import RequestContext, ResponsePolicy
from src.models.db import cache, connect
from src.routes import inbox, ledger, session

app = FastAPI(title='烘邻共享灶 · 燃气偏差班报')
app.add_middleware(RequestContext)
app.add_middleware(ResponsePolicy)
for router in (session.router, ledger.router, inbox.router):
    app.include_router(router)


@app.get('/health')
def health():
    try:
        with connect() as db:
            db.execute('SELECT 1 FROM shifts LIMIT 1')
        cache.ping()
    except (psycopg.Error, RedisError) as error:
        raise HTTPException(503, '数据服务暂不可用') from error
    return {'status': 'ok'}


@app.exception_handler(psycopg.Error)
def database_error(request, error):
    logging.getLogger('api').error('Database failure %s (%s)', request.state.request_id, error.sqlstate)
    return JSONResponse({'detail': '暂时无法访问数据，请稍后重试', 'request_id': request.state.request_id}, status_code=503)
