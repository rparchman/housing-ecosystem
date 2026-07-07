from fastapi import APIRouter, HTTPException
import json
from pathlib import Path

router = APIRouter()

DATA_PATH = Path("pipeline/config/statewide_landbank_dataset.json")

@router.get("/{parcel_id}")
def get_parcel(parcel_id: str):
    """
    Returns unified parcel data + land bank enrichment.
    """
    if not DATA_PATH.exists():
        raise HTTPException(500, "Dataset not found")

    data = json.loads(DATA_PATH.read_text())

    for record in data:
        if record["parcel_id"] == parcel_id.upper():
            return record

    raise HTTPException(404, "Parcel not found")


@router.get("/county/{county}")
def get_parcels_by_county(county: str):
    """
    Returns all parcels for a given county.
    """
    data = json.loads(DATA_PATH.read_text())
    county = county.lower()

    results = [r for r in data if r["county"].lower() == county]
    return {"count": len(results), "results": results}
