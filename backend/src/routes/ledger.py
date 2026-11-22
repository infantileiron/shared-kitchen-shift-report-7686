from fastapi import APIRouter, Depends

from src.constants.enums import Role
from src.controllers.session import account, allows
from src.models.db import connect
from src.schemas.inputs import BackfillInput, ReadingInput, RuleInput, ShiftInput
from src.services import ledger
from src.utils.encoding import payload

router = APIRouter()
writer = allows(Role.MANAGER, Role.RECORDER)
manager = allows(Role.MANAGER)


@router.get('/stations', dependencies=[Depends(account)])
def get_stations():
    with connect() as db:
        return db.execute('SELECT * FROM stations ORDER BY code').fetchall()


@router.get('/rules', dependencies=[Depends(account)])
def get_rules():
    with connect() as db:
        return payload(ledger.rules(db))


@router.post('/rules', status_code=201)
def publish_rule(body: RuleInput, actor=Depends(manager)):
    with connect() as db:
        return payload(ledger.new_rule(db, actor, body))


@router.get('/shifts', dependencies=[Depends(account)])
def get_shifts():
    with connect() as db:
        return payload(ledger.shifts(db))


@router.post('/shifts', status_code=201)
def create_shift(body: ShiftInput, actor=Depends(writer)):
    with connect() as db:
        return payload(ledger.new_shift(db, actor, body))


@router.get('/shifts/{shift_id}', dependencies=[Depends(account)])
def get_shift(shift_id: int):
    with connect() as db:
        return payload(ledger.shift_detail(db, shift_id))


@router.post('/shifts/{shift_id}/readings', status_code=201)
def record(shift_id: int, body: ReadingInput, actor=Depends(writer)):
    with connect() as db:
        return payload(ledger.new_reading(db, actor, shift_id, body))


@router.post('/shifts/{shift_id}/backfill', status_code=201)
def backfill(shift_id: int, body: BackfillInput, actor=Depends(writer)):
    with connect() as db:
        return payload(ledger.backfill(db, actor, shift_id, body))
