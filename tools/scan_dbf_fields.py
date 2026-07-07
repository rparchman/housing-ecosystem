# tools/scan_dbf_fields.py
"""
Scan a raw county folder for a .dbf, list fields, and print sample values.
Usage:
  .venv\\Scripts\\python.exe tools\\scan_dbf_fields.py data/raw/wayne
"""
import sys
from pathlib import Path
from dbfread import DBF

CANDIDATES = ["PID_All","PARCELID","APN","PARCEL","parcel","ParcelID","PARCEL_ID","PIN","PIN_NUM"]

def find_dbf(folder):
    p = Path(folder)
    if not p.exists():
        raise SystemExit(f"Folder not found: {p}")
    dbfs = list(p.rglob("*.dbf"))
    if not dbfs:
        raise SystemExit(f"No .dbf files found under: {p}")
    return dbfs[0]

def choose_field(field_names):
    for c in CANDIDATES:
        if c in field_names:
            return c
    # fallback: prefer any field with ID-like name
    for f in field_names:
        if any(tok in f.lower() for tok in ("parcel","apn","pin","id")):
            return f
    return field_names[0]

def sample_values(table, field, n=20):
    vals = []
    for i, rec in enumerate(table):
        if i >= n:
            break
        v = rec.get(field)
        if v is None:
            vals.append("")
        else:
            vals.append(str(v).strip())
    return vals

def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/scan_dbf_fields.py <raw-county-folder>")
        raise SystemExit(1)
    folder = sys.argv[1]
    dbf_path = find_dbf(folder)
    print("Found DBF:", dbf_path)
    # try common encodings if needed by passing encoding param to DBF
    table = DBF(str(dbf_path), load=True, ignorecase=True)
    fields = table.field_names
    print("Fields:", ", ".join(fields))
    chosen = choose_field(fields)
    print("Heuristic parcel field:", chosen)
    samples = sample_values(table, chosen, n=20)
    print("Sample values (first 20):")
    for s in samples:
        print(" ", s)
    # show a short uniqueness check
    uniq = [v for v in samples if v]
    print("Non-empty sample count:", len(uniq))
    if uniq:
        print("Example unique values:", ", ".join(uniq[:5]))

if __name__ == "__main__":
    main()
