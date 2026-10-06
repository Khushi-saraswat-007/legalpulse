from fastapi import APIRouter
router = APIRouter(prefix="/auth", tags=["auth"])


# TODO: POST /auth/register, POST /auth/login (JWT), GET /auth/me
@router.get("/ping")
def ping():
    return {"module": "auth", "status": "stub"}
