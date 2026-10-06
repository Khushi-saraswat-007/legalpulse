from fastapi import APIRouter
router = APIRouter(prefix="/alerts", tags=["alerts"])


# TODO: GET /alerts (unseen first), POST /alerts/{id}/seen
@router.get("")
def list_alerts():
    return []
