# tools/extract_parcels_from_zip.py
"""
Extract parcel ID values from a downloaded county parcels ZIP (shapefile archive).
Writes unique parcel IDs to data/parcels.txt (one per line).

Usage (from project root):
  .venv\Scripts\python.exe tools\extract_parcels_from_zip.py "C:\\Users\\ricki\\Downloads\\wayne_county_allcomm_n.zip"

Notes:
- Requires the dbfread package to read the shapefile DBF table.
- The script will try common parcel ID field names automatically.
- If no common field is found, it prints available fields and writes the first non-empty field.
"""
import sys
import zipfile
import tempfile
from pathlib import Path
from dbfread import DBF

COMMON_FIELDS = [
    "PARCELID", "PARCEL_ID", "PARCEL", "PIN", "PIN_NUM", "PARID", "PARCELNO", "PARCEL_NO", "PARCELNUM", "PARCELNUMBER"
]

def find_dbf(extract_dir: Path):
    for p in extract_dir.rglob("*.dbf"):
        return p
    return None

def choose_field(fields):
    upper = {f.upper(): f for f in fields}
    for cand in COMMON_FIELDS:
        if cand in upper:
            return upper[cand]
    # fallback: return first field
    return fields[0] if fields else None

def extract_parcels(zip_path: Path, out_path: Path):
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP not found: {zip_path}")
    with tempfile.TemporaryDirectory() as td:
        tdpath = Path(td)
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(tdpath)
        dbf_path = find_dbf(tdpath)
        if not dbf_path:
            raise RuntimeError("No .dbf file found inside the ZIP. Ensure this is a shapefile archive.")
        # read DBF and inspect fields
        table = DBF(str(dbf_path), load=True, ignorecase=True)
        fields = table.field_names
        chosen = choose_field(fields)
        if not chosen:
            raise RuntimeError("No fields found in DBF.")
        print("DBF file:", dbf_path)
        print("Available fields:", ", ".join(fields))
        print("Chosen field for parcel id:", chosen)
        seen = set()
        out_lines = []
        for rec in table:
            val = rec.get(chosen)
            if val is None:
                # try other common fields per-record
                for alt in fields:
                    v2 = rec.get(alt)
                    if v2:
                        val = v2
                        break
            if val:
                s = str(val).strip()
                if s and s not in seen:
                    seen.add(s)
                    out_lines.append(s)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(out_lines), encoding="utf-8")
        print(f"Wrote {len(out_lines)} unique parcel ids to {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/extract_parcels_from_zip.py <path-to-zip>")
        sys.exit(1)
    zipfile_path = Path(sys.argv[1])
    out = Path("data") / "parcels.txt"
    try:
        extract_parcels(zipfile_path, out)
    except Exception as e:
        print("Error:", e)
        sys.exit(2)
