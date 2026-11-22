import json

from fastapi import APIRouter, Depends, Response
from redis import RedisError

from src.config.settings import WORKER_METRICS
from src.constants.enums import Mailbox
from src.controllers.session import account
from src.models.db import cache, connect
from src.services import inbox
from src.utils.encoding import payload

router = APIRouter(dependencies=[Depends(account)])


@router.get('/queue')
def get_queue():
    try:
        scheduler = json.loads(cache.get(WORKER_METRICS) or 'null')
    except RedisError:
        scheduler = None
    with connect() as db:
        return payload({'scheduler': scheduler, 'windows': inbox.queue(db)})


@router.get('/inbox')
def get_inbox(mailbox: Mailbox | None = None):
    with connect() as db:
        return payload(inbox.messages(db, mailbox))


@router.get('/reminder-revisions')
def get_revisions(mailbox: Mailbox | None = None):
    with connect() as db:
        return payload(inbox.revisions(db, mailbox))


@router.get('/inbox/{receipt_id}')
def get_receipt(receipt_id: int):
    with connect() as db:
        return payload(inbox.message(db, receipt_id))


@router.get('/inbox/{receipt_id}/export.csv')
def export(receipt_id: int):
    with connect() as db:
        receipt = inbox.message(db, receipt_id)
    return Response(inbox.csv_report(receipt), media_type='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="receipt-{receipt_id}.csv"'})
