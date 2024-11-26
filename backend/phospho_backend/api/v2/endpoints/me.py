from fastapi import APIRouter, Depends

# Auth
from phospho_backend.security.authentification import authenticate_org_key

router = APIRouter(tags=["Me"])


@router.get("/me")
def read_root(org=Depends(authenticate_org_key)):
    return org
