from fastapi import APIRouter

router = APIRouter()

@router.get("/contractors/health")
def contractor_health():
    return {"status": "ok", "service": "contractor"}
