from fastapi import APIRouter, Depends

from src.controllers.session import account, login
from src.schemas.inputs import Login

router = APIRouter()


@router.post('/session')
def sign_in(body: Login):
    return login(body)


@router.get('/session')
def profile(actor=Depends(account)):
    return actor
