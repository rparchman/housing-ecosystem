# tools/normalize_template.py
"""
Usage:
  .venv\\Scripts\\python.exe tools\\normalize_template.py manifests/wayne_county.yaml data/raw/wayne_parcels.shp data/normalized/wayne_parcels.csv
This script is a template. Adjust field mappings and fallbacks per county manifest.
"""
import sys
import csv
import yaml
from pathlib import Path

# Optional dependencies: fiona or geopandas. This template uses fiona for shapefiles/geojson.
try:
    import fiona
except Exception as e:
    raise SystemExit("Install fiona in your venv: pip install fiona")

STANDARD_FIELDS = [
    "parcel_id",
    "owner_name",
    "address",
    "city",
    "state",
    "zip",
    "area_sqft",
    "assessed_value",
    "land_use",
    "geometry_wkt"
]

def load_manifest(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))

def open_layer(path):
    return fiona.open(str(path), encoding="utf-8")

def map_record(rec, manifest):
    props = rec.get("properties", {})
    # Common candidate fields; adjust order as needed
    parcel_candidates = [manifest.get("layers", [{}])[0].get("parcel_id_field"), "PID_All", "PARCELID", "APN", "parcel"]
    owner_candidates = ["OWNER", "owner_name", "OwnerName"]
    addr_candidates = ["ADDRESS", "addr_full", "ADDR"]
    city_candidates = ["CITY", "TOWN"]
    state_candidates = ["STATE"]
    zip_candidates = ["ZIP", "ZIPCODE", "POSTCODE"]
    area_candidates = ["AREA_SQFT", "Shape_Area", "AREA"]
    value_candidates = ["ASSESSED", "VALUE", "AV"]
    landuse_candidates = ["LANDUSE", "LU", "USE"]

    def first_present(cands):
        for c in cands:
            if not c:
                continue
            v = props.get(c)
            if v not in (None, ""):
                return v
        return ""

    parcel_id = first_present(parcel_candidates) or rec.get("id") or ""
    owner = first_present(owner_candidates)
    address = first_present(addr_candidates)
    city = first_present(city_candidates)
    state = first_present(state_candidates)
    zipc = first_present(zip_candidates)
    area = first_present(area_candidates)
    value = first_present(value_candidates)
    landuse = first_present(landuse_candidates)

    geom = rec.get("geometry")
    geom_wkt = ""
    if geom:
        # Minimal WKT conversion for point/polygon; for robust use shapely
        try:
            from shapely.geometry import shape
            geom_wkt = shape(geom).wkt
        except Exception:
            geom_wkt = str(geom)

    return {
        "parcel_id": str(parcel_id).strip(),
        "owner_name": str(owner).strip(),
        "address": str(address).strip(),
        "city": str(city).strip(),
        "state": str(state).strip(),
        "zip": str(zipc).strip(),
        "area_sqft": str(area).strip(),
        "assessed_value": str(value).strip(),
        "land_use": str(landuse).strip(),
        "geometry_wkt": geom_wkt
    }

def normalize(manifest_path, layer_path, out_csv):
    manifest = load_manifest(manifest_path)
    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open_layer(layer_path) as src, out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=STANDARD_FIELDS)
        writer.writeheader()
        for rec in src:
            row = map_record(rec, manifest)
            # Skip empty parcel ids
            if not row["parcel_id"]:
                continue
            writer.writerow(row)
    print("Wrote normalized CSV:", out_path)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python tools/normalize_template.py <manifest.yaml> <layer_path> <out_csv>")
        raise SystemExit(1)
    normalize(sys.argv[1], sys.argv[2], sys.argv[3])
