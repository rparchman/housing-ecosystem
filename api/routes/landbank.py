from fastapi import APIRouter, HTTPException
import json
from pathlib import Path

router = APIRouter()

DATA_PATH = Path("pipeline/config/statewide_landbank_dataset.json")

@router.get("/available")
def available_properties():
    """
    Returns all land bank properties currently available.
    """
    data = json.loads(DATA_PATH.read_text())
    results = [r for r in data if r["landbank"] and r["landbank"].get("status") == "available"]
    return {"count": len(results), "results": results}


@router.get("/program/{program}")
def get_by_program(program: str):
    """
    Returns land bank properties by program type (demo, rehab, auction, etc.)
    """
    data = json.loads(DATA_PATH.read_text())
    program = program.lower()

    results = [
        r for r in data
        if r["landbank"] and r["landbank"].get("program", "").lower() == program
    ]

    return {"count": len(results), "results": results}
