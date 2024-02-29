from fastapi import APIRouter, Depends
from propelauth_fastapi import init_auth
from propelauth_py.user import User

from app.core import config
from app.security.authentification import propelauth

router = APIRouter(include_in_schema=False)


@router.get("/debug")
def read_root(user: User = Depends(propelauth.require_user)):
    return {"Hello": user.user_id}


@router.get("/health")
def health_check():
    return {"status": "OK"}
