from fastapi import APIRouter, Depends
from propelauth_py.user import User  # type: ignore

from phospho_backend.security.authentification import propelauth

router = APIRouter(include_in_schema=False)


@router.get("/debug")
def read_root(user: User = Depends(propelauth.require_user)):
    return {"Hello": user.user_id}


@router.get("/health")
def health_check():
    return {"status": "OK"}
