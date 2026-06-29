from fastapi import APIRouter
router = APIRouter(prefix="/api/listings")

@router.get("/health")
def health():
    return {"status": "ok"}
