@echo off
cd /d C:\Users\ricki\housing-ecosystem

REM -------------------------
REM Create folders (ignore errors if they exist)
REM -------------------------
mkdir services\shared\migrations 2>nul
mkdir services\landbank 2>nul
mkdir services\contractor\migrations 2>nul
mkdir services\pipeline 2>nul
mkdir api\routes\contractor 2>nul
mkdir api\routes\listings 2>nul
mkdir infra 2>nul
mkdir docs 2>nul
mkdir progress\week_checklists 2>nul
mkdir tests\unit 2>nul
mkdir tests\integration 2>nul
mkdir scripts 2>nul

REM -------------------------
REM Shared DB
REM -------------------------
> services\shared\db.py echo from sqlalchemy import create_engine
>> services\shared\db.py echo from sqlalchemy.orm import sessionmaker, declarative_base
>> services\shared\db.py echo.
>> services\shared\db.py echo DATABASE_URL = "sqlite:///./app.db"
>> services\shared\db.py echo.
>> services\shared\db.py echo engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
>> services\shared\db.py echo SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
>> services\shared\db.py echo Base = declarative_base()
>> services\shared\db.py echo.
>> services\shared\db.py echo def get_db_session():
>> services\shared\db.py echo ^    return SessionLocal()

REM -------------------------
REM Shared Schemas
REM -------------------------
> services\shared\schemas.py echo from pydantic import BaseModel
>> services\shared\schemas.py echo.
>> services\shared\schemas.py echo class Listing(BaseModel):
>> services\shared\schemas.py echo ^    listing_id: str
>> services\shared\schemas.py echo ^    address: str
>> services\shared\schemas.py echo ^    meta: dict
>> services\shared\schemas.py echo ^    va_tag: bool = False

REM -------------------------
REM Contractor Model
REM -------------------------
> services\contractor\contractor_model.py echo from sqlalchemy import Column, Integer, String, JSON, DateTime
>> services\contractor\contractor_model.py echo from services.shared.db import Base
>> services\contractor\contractor_model.py echo import datetime
>> services\contractor\contractor_model.py echo.
>> services\contractor\contractor_model.py echo class Contractor(Base):
>> services\contractor\contractor_model.py echo ^    __tablename__ = "contractors"
>> services\contractor\contractor_model.py echo ^    id = Column(Integer, primary_key=True)
>> services\contractor\contractor_model.py echo ^    name = Column(String, nullable=False)
>> services\contractor\contractor_model.py echo ^    email = Column(String, nullable=False, unique=True)
>> services\contractor\contractor_model.py echo ^    profile = Column(JSON, default={})
>> services\contractor\contractor_model.py echo ^    created_at = Column(DateTime, default=datetime.datetime.utcnow)

REM -------------------------
REM Contractor Job Controller
REM -------------------------
> services\contractor\job_controller.py echo from fastapi import APIRouter, HTTPException
>> services\contractor\job_controller.py echo from services.shared.db import SessionLocal
>> services\contractor\job_controller.py echo from services.contractor.contractor_model import Contractor
>> services\contractor\job_controller.py echo.
>> services\contractor\job_controller.py echo router = APIRouter(prefix="/api/contractor")
>> services\contractor\job_controller.py echo.
>> services\contractor\job_controller.py echo @router.post("/register")
>> services\contractor\job_controller.py echo def register_contractor(payload: dict):
>> services\contractor\job_controller.py echo ^    db = SessionLocal()
>> services\contractor\job_controller.py echo ^    if "email" not in payload or "name" not in payload:
>> services\contractor\job_controller.py echo ^        raise HTTPException(status_code=400, detail="name and email required")
>> services\contractor\job_controller.py echo ^    c = Contractor(name=payload["name"], email=payload["email"], profile=payload.get("profile", {}))
>> services\contractor\job_controller.py echo ^    db.add(c)
>> services\contractor\job_controller.py echo ^    db.commit()
>> services\contractor\job_controller.py echo ^    db.refresh(c)
>> services\contractor\job_controller.py echo ^    return {"id": c.id, "status": "created"}

REM -------------------------
REM Contractor Notifications
REM -------------------------
> services\contractor\notifications.py echo import redis, json
>> services\contractor\notifications.py echo.
>> services\contractor\notifications.py echo r = redis.Redis(host="localhost", port=6379, db=0)
>> services\contractor\notifications.py echo.
>> services\contractor\notifications.py echo def enqueue_notification(payload: dict):
>> services\contractor\notifications.py echo ^    r.lpush("notifications:queue", json.dumps(payload))
>> services\contractor\notifications.py echo ^    return True
>> services\contractor\notifications.py echo.
>> services\contractor\notifications.py echo def pop_notification():
>> services\contractor\notifications.py echo ^    item = r.rpop("notifications:queue")
>> services\contractor\notifications.py echo ^    if not item:
>> services\contractor\notifications.py echo ^        return None
>> services\contractor\notifications.py echo ^    return json.loads(item)

REM -------------------------
REM Landbank Scraper
REM -------------------------
> services\landbank\scraper_county_MI_primary.py echo import httpx
>> services\landbank\scraper_county_MI_primary.py echo from bs4 import BeautifulSoup
>> services\landbank\scraper_county_MI_primary.py echo.
>> services\landbank\scraper_county_MI_primary.py echo def run_scraper_sample():
>> services\landbank\scraper_county_MI_primary.py echo ^    url = "https://example-county-records.gov/sample-listings"
>> services\landbank\scraper_county_MI_primary.py echo ^    resp = httpx.get(url, timeout=30)
>> services\landbank\scraper_county_MI_primary.py echo ^    resp.raise_for_status()
>> services\landbank\scraper_county_MI_primary.py echo ^    soup = BeautifulSoup(resp.text, "html.parser")
>> services\landbank\scraper_county_MI_primary.py echo ^    results = []
>> services\landbank\scraper_county_MI_primary.py echo ^    for el in soup.select(".listing"):
>> services\landbank\scraper_county_MI_primary.py echo ^        results.append({
>> services\landbank\scraper_county_MI_primary.py echo ^            "source_id": el.get("data-id"),
>> services\landbank\scraper_county_MI_primary.py echo ^            "address": el.select_one(".address").get_text(strip=True),
>> services\landbank\scraper_county_MI_primary.py echo ^            "raw": str(el)
>> services\landbank\scraper_county_MI_primary.py echo ^        })
>> services\landbank\scraper_county_MI_primary.py echo ^    return results

REM -------------------------
REM Landbank Normalizer
REM -------------------------
> services\landbank\normalizer.py echo def normalize_record(raw):
>> services\landbank\normalizer.py echo ^    return {
>> services\landbank\normalizer.py echo ^        "listing_id": raw.get("source_id"),
>> services\landbank\normalizer.py echo ^        "address": raw.get("address"),
>> services\landbank\normalizer.py echo ^        "meta": {"raw_html": raw.get("raw")},
>> services\landbank\normalizer.py echo ^        "va_tag": False
>> services\landbank\normalizer.py echo ^    }
>> services\landbank\normalizer.py echo.
>> services\landbank\normalizer.py echo def normalize_batch(raw_list):
>> services\landbank\normalizer.py echo ^    return [normalize_record(r) for r in raw_list]

REM -------------------------
REM Pipeline Ingest Scheduler
REM -------------------------
> services\pipeline\ingest_scheduler.py echo from services.landbank.scraper_county_MI_primary import run_scraper_sample
>> services\pipeline\ingest_scheduler.py echo from services.landbank.normalizer import normalize_batch
>> services\pipeline\ingest_scheduler.py echo from services.shared.db import get_db_session
>> services\pipeline\ingest_scheduler.py echo.
>> services\pipeline\ingest_scheduler.py echo def main():
>> services\pipeline\ingest_scheduler.py echo ^    raw = run_scraper_sample()
>> services\pipeline\ingest_scheduler.py echo ^    normalized = normalize_batch(raw)
>> services\pipeline\ingest_scheduler.py echo ^    db = get_db_session()
>> services\pipeline\ingest_scheduler.py echo ^    for rec in normalized:
>> services\pipeline\ingest_scheduler.py echo ^        pass
>> services\pipeline\ingest_scheduler.py echo.
>> services\pipeline\ingest_scheduler.py echo if __name__ == "__main__":
>> services\pipeline\ingest_scheduler.py echo ^    main()

echo.
echo 🎉 ALL FILES AND BOILERPLATE CREATED SUCCESSFULLY!
