from fastapi import APIRouter

router = APIRouter()


# Healthcheck
@router.get("/health")
def check_health():
    return {"status": "ok"}
