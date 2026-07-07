# tools/extract_pid_all.py
"""
Extract PID_All (parcel IDs) from a shapefile ZIP and write data/parcels.txt.

Usage (CMD):
  .venv\Scripts\python.exe tools\extract_pid_all.py "C:\\Users\\ricki\\Downloads\\wayne_county_allcomm_n.zip"
"""
import sys, zipfile, tempfile, shutil
from pathlib import Path
from dbfread import DBF

if len(sys.argv) < 2:
    print("Usage: python tools/exact_pid_all.py <path-to-zip>")
    sys.exit(1)

zip_path = Path(sys.argv[1])
if not zip_path.exists():
    print("ZIP not found:", zip_path)
    sys.exit(2)

out = Path("data") / "parcels.txt"
tmpdir = Path(tempfile.mkdtemp())
try:
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(tmpdir)
    dbf = next(tmpdir.rglob("*.dbf"), None)
    if not dbf:
        print("No .dbf found in ZIP")
        sys.exit(3)
    table = DBF(str(dbf), load=True, ignorecase=True)
    # Prefer PID_All, fallback to packedParc or first matching numeric field
    FIELD_CANDIDATES = ["PID_All", "packedParc", "PID_Dborn"]
    chosen = None
    for f in FIELD_CANDIDATES:
        if f in table.field_names:
            chosen = f
            break
    if not chosen:
        # fallback: pick the first field that contains long numeric-looking values in the first 20 rows
        for f in table.field_names:
            count = 0
            for i, rec in enumerate(table):
                if i >= 20:
                    break
                v = rec.get(f)
                if v and any(ch.isdigit() for ch in str(v)):
                    count += 1
            # reload table to reset iterator
            table = DBF(str(dbf), load=True, ignorecase=True)
            if count >= 5:
                chosen = f
                break
    if not chosen:
        chosen = table.field_names[0]
    print("Using field:", chosen)
    vals = []
    for rec in table:
        v = rec.get(chosen) or rec.get("packedParc") or rec.get("PID_All")
        if v:
            s = str(v).strip()
            if s:
                vals.append(s)
    # dedupe while preserving order
    seen = set()
    uniq = []
    for v in vals:
        if v not in seen:
            seen.add(v)
            uniq.append(v)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(uniq), encoding="utf-8")
    print("Wrote", out, "rows:", len(uniq))
finally:
    shutil.rmtree(tmpdir)
