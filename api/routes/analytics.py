from fastapi import APIRouter
import json
from pathlib import Path
from collections import Counter

router = APIRouter()

DATA_PATH = Path("pipeline/config/statewide_landbank_dataset.json")

@router.get("/counts")
def counts():
    """
    Returns basic statewide analytics:
        - parcels per county
        - land bank availability counts
        - program distribution
    """
    data = json.loads(DATA_PATH.read_text())

    counties = Counter([r["county"] for r in data])
    programs = Counter([r["landbank"]["program"] for r in data if r["landbank"]])
    statuses = Counter([r["landbank"]["status"] for r in data if r["landbank"]])

    return {
        "counties": counties,
        "programs": programs,
        "statuses": statuses
    }


@router.get("/summary")
def summary():
    """
    Returns high-level statewide summary.
    """
    data = json.loads(DATA_PATH.read_text())

    total_parcels = len(data)
    total_landbank = len([r for r in data if r["landbank"]])
    available = len([r for r in data if r["landbank"] and r["landbank"]["status"] == "available"])

    return {
        "total_parcels": total_parcels,
        "landbank_properties": total_landbank,
        "available_landbank": available,
        "coverage_percent": round((total_landbank / total_parcels) * 100, 2)
    }
