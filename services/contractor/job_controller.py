from fastapi import APIRouter, HTTPException
from services.shared.db import SessionLocal
from services.contractor.contractor_model import Contractor

router = APIRouter(prefix="/api/contractor")

@router.post("/register")
def register_contractor(payload: dict):
    db = SessionLocal()
    if "email" not in payload or "name" not in payload:
        raise HTTPException(status_code=400, detail="name and email required")
    c = Contractor(name=payload["name"], email=payload["email"], profile=payload.get("profile", {}))
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "status": "created"}
