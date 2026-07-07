from fastapi import APIRouter

router = APIRouter()

@router.get("/listings/health")
def listings_health():
    return {"status": "ok", "service": "listings"}
