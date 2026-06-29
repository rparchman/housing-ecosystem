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
REM services\shared\db.py
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
REM services\shared\schemas.py
REM -------------------------
> services\shared\schemas.py echo from pydantic import BaseModel
>> services\shared\schemas.py echo from typing import Optional, Dict
>> services\shared\schemas.py echo.
>> services\shared\schemas.py echo class Listing(BaseModel):
>> services\shared\schemas.py echo ^    listing_id: str
>> services\shared\schemas.py echo ^    address: str
>> services\shared\schemas.py echo ^    meta: Dict
>> services\shared\schemas.py echo ^    va_tag: bool = False

REM -------------------------
REM services\contractor\contractor_model.py
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
REM services\contractor\job_controller.py
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
REM services\contractor\notifications.py
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
REM services\landbank\scraper_county_MI_primary.py
REM -------------------------
> services\landbank\scraper_county_MI_primary.py echo import httpx
>> services\landbank\scraper_county_MI_primary.py echo from bs4 import BeautifulSoup
>> services\landbank\scraper_county_MI_primary.py echo import logging
>> services\landbank\scraper_county_MI_primary.py echo.
>> services\landbank\scraper_county_MI_primary.py echo logger = logging.getLogger(__name__)
>> services\landbank\scraper_county_MI_primary.py echo logging.basicConfig(level=logging.INFO)
>> services\landbank\scraper_county_MI_primary.py echo.
>> services\landbank\scraper_county_MI_primary.py echo TEST_URL = "https://httpbin.org/get"
>> services\landbank\scraper_county_MI_primary.py echo.
>> services\landbank\scraper_county_MI_primary.py echo def fetch_url(url, timeout=30):
>> services\landbank\scraper_county_MI_primary.py echo ^    try:
>> services\landbank\scraper_county_MI_primary.py echo ^        with httpx.Client(timeout=timeout, trust_env=False) as client:
>> services\landbank\scraper_county_MI_primary.py echo ^            resp = client.get(url)
>> services\landbank\scraper_county_MI_primary.py echo ^            resp.raise_for_status()
>> services\landbank\scraper_county_MI_primary.py echo ^            return resp.text
>> services\landbank\scraper_county_MI_primary.py echo ^    except Exception as exc:
>> services\landbank\scraper_county_MI_primary.py echo ^        logger.error("Fetch failed for %s: %s", url, exc)
>> services\landbank\scraper_county_MI_primary.py echo ^        return None
>> services\landbank\scraper_county_MI_primary.py echo.
>> services\landbank\scraper_county_MI_primary.py echo def run_scraper_sample(url=TEST_URL):
>> services\landbank\scraper_county_MI_primary.py echo ^    html = fetch_url(url)
>> services\landbank\scraper_county_MI_primary.py echo ^    if not html:
>> services\landbank\scraper_county_MI_primary.py echo ^        logger.info("Falling back to local sample data")
>> services\landbank\scraper_county_MI_primary.py echo ^        return [
>> services\landbank\scraper_county_MI_primary.py echo ^            {"source_id": "sample-1", "address": "123 Example St", "raw": "<div class='listing'>sample</div>"}
>> services\landbank\scraper_county_MI_primary.py echo ^        ]
>> services\landbank\scraper_county_MI_primary.py echo.
>> services\landbank\scraper_county_MI_primary.py echo ^    soup = BeautifulSoup(html, "html.parser")
>> services\landbank\scraper_county_MI_primary.py echo ^    results = []
>> services\landbank\scraper_county_MI_primary.py echo ^    for el in soup.select(".listing"):
>> services\landbank\scraper_county_MI_primary.py echo ^        results.append({
>> services\landbank\scraper_county_MI_primary.py echo ^            "source_id": el.get("data-id"),
>> services\landbank\scraper_county_MI_primary.py echo ^            "address": el.select_one(".address").get_text(strip=True) if el.select_one(".address") else None,
>> services\landbank\scraper_county_MI_primary.py echo ^            "raw": str(el),
>> services\landbank\scraper_county_MI_primary.py echo ^        })
>> services\landbank\scraper_county_MI_primary.py echo ^    return results

REM -------------------------
REM services\landbank\normalizer.py
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
REM services\pipeline\ingest_scheduler.py
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

REM -------------------------
REM api\routes\contractor\router.py
REM -------------------------
> api\routes\contractor\router.py echo from fastapi import APIRouter
>> api\routes\contractor\router.py echo from services.contractor.job_controller import router as contractor_router
>> api\routes\contractor\router.py echo.
>> api\routes\contractor\router.py echo router = APIRouter()
>> api\routes\contractor\router.py echo router.include_router(contractor_router)

REM -------------------------
REM api\routes\listings\router.py
REM -------------------------
> api\routes\listings\router.py echo from fastapi import APIRouter
>> api\routes\listings\router.py echo router = APIRouter(prefix="/api/listings")
>> api\routes\listings\router.py echo.
>> api\routes\listings\router.py echo @router.get("/health")
>> api\routes\listings\router.py echo def health():
>> api\routes\listings\router.py echo ^    return {"status": "ok"}

REM -------------------------
REM docs files
REM -------------------------
> docs\scraper_runbook.md echo # Scraper Runbook
>> docs\scraper_runbook.md echo
>> docs\scraper_runbook.md echo This document explains how to run and troubleshoot the landbank scrapers.
>> docs\contractor_onboarding.md echo # Contractor Onboarding
>> docs\contractor_onboarding.md echo
>> docs\contractor_onboarding.md echo Steps to onboard a contractor.
>> docs\acceptance_contractors.md echo # Acceptance Criteria for Contractors
>> docs\acceptance_contractors.md echo
>> docs\acceptance_contractors.md echo Acceptance tests and criteria.

REM -------------------------
REM progress files
REM -------------------------
> progress\status.json echo {"week": 0, "completed": []}
>> progress\week_checklists\week13.md echo # Week 13 Checklist
>> progress\week_checklists\week13.md echo
>> progress\week_checklists\week13.md echo - Task A
>> progress\week_checklists\week13.md echo - Task B

REM -------------------------
REM tests unit
REM -------------------------
> tests\unit\test_normalizer.py echo import pytest
>> tests\unit\test_normalizer.py echo from services.landbank.normalizer import normalize_record
>> tests\unit\test_normalizer.py echo.
>> tests\unit\test_normalizer.py echo def test_normalize_record():
>> tests\unit\test_normalizer.py echo ^    raw = {"source_id":"s1","address":"1 Main St","raw":"<div/>"}
>> tests\unit\test_normalizer.py echo ^    out = normalize_record(raw)
>> tests\unit\test_normalizer.py echo ^    assert out["listing_id"] == "s1"

> tests\unit\test_contractor_model.py echo import pytest
>> tests\unit\test_contractor_model.py echo from services.contractor.contractor_model import Contractor
>> tests\unit\test_contractor_model.py echo.
>> tests\unit\test_contractor_model.py echo def test_contractor_fields():
>> tests\unit\test_contractor_model.py echo ^    c = Contractor()
>> tests\unit\test_contractor_model.py echo ^    assert hasattr(c, "__tablename__")

> tests\unit\test_job_controller.py echo import pytest
>> tests\unit\test_job_controller.py echo from services.contractor.job_controller import register_contractor
>> tests\unit\test_job_controller.py echo.
>> tests\unit\test_job_controller.py echo def test_register_missing_fields():
>> tests\unit\test_job_controller.py echo ^    try:
>> tests\unit\test_job_controller.py echo ^        register_contractor({})
>> tests\unit\test_job_controller.py echo ^    except Exception as e:
>> tests\unit\test_job_controller.py echo ^        assert "name and email required" in str(e)

REM -------------------------
REM tests integration
REM -------------------------
> tests\integration\smoke_ingest_to_db.py echo # Integration smoke test placeholder
>> tests\integration\smoke_ingest_to_db.py echo def test_smoke_ingest():
>> tests\integration\smoke_ingest_to_db.py echo ^    assert True

> tests\integration\smoke_job_flow.py echo # Integration smoke test placeholder
>> tests\integration\smoke_job_flow.py echo def test_smoke_job_flow():
>> tests\integration\smoke_job_flow.py echo ^    assert True

> tests\integration\smoke_ingest_to_lead_dispatch.py echo # Integration smoke test placeholder
>> tests\integration\smoke_ingest_to_lead_dispatch.py echo def test_smoke_dispatch():
>> tests\integration\smoke_ingest_to_lead_dispatch.py echo ^    assert True

REM -------------------------
REM scripts
REM -------------------------
> scripts\mark_week_complete.sh echo #!/usr/bin/env bash
>> scripts\mark_week_complete.sh echo echo "Marking week complete"
>> scripts\staging_setup.sh echo #!/usr/bin/env bash
>> scripts\staging_setup.sh echo echo "Staging setup placeholder"

REM -------------------------
REM Final message
REM -------------------------
echo.
echo ALL FILES AND BOILERPLATE CREATED SUCCESSFULLY!
