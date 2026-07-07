import json
from pipeline.ingestion.gis_fetcher import fetch_gis_parcels
from pipeline.ingestion.parcel_normalizer import normalize_parcel
from pipeline.ingestion.db_writer import write_parcels_to_db
from pipeline.ingestion.ingestion_logger import log_ingestion

def run_ingestion():
    """
    Full ingestion workflow:
    - load county config
    - fetch GIS data
    - normalize parcels
    - write to database
    - log results
    """

    with open("pipeline/config/counties.json") as f:
        counties = json.load(f)

    results = []

    for key, county in counties.items():
        gis_url = county["gis_url"]

        raw = fetch_gis_parcels(gis_url)

        # If fetch_gis_parcels returned an error dict
        if isinstance(raw, dict) and "error" in raw:
            results.append({
                "county": county["name"],
                "error": raw["error"],
                "fetched": 0,
                "normalized": 0,
                "written": 0
            })
            continue

        # Normal ingestion path
        normalized = [normalize_parcel(f) for f in raw]
        written = write_parcels_to_db(normalized)

        log_ingestion(county["name"], written)

        results.append({
            "county": county["name"],
            "fetched": len(raw),
            "normalized": len(normalized),
            "written": written
        })

    return {
        "message": "Ingestion completed",
        "results": results
    }
