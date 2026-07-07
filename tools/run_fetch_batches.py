# tools/run_fetch_batches.py
import time, json, sqlite3
from pathlib import Path
from subprocess import run, PIPE

PARCELS = Path("data/parcels.txt")
OUT_JSON = Path("data/listings.json")
DB = Path("data/listings.db")
BATCH_SIZE = 500
DELAY_BETWEEN_REQUESTS = 1.8
DELAY_BETWEEN_BATCHES = 15

def load_parcels():
    return [p.strip() for p in PARCELS.read_text(encoding="utf-8").splitlines() if p.strip()]

def run_fetch_for_list(parcels):
    # Assumes tools/fetch_parcels.py reads data/parcels.txt and writes data/listings.json
    Path("data/parcels.txt").write_text("\n".join(parcels), encoding="utf-8")
    r = run([".venv\\Scripts\\python.exe","tools\\fetch_parcels.py"], stdout=PIPE, stderr=PIPE, text=True)
    return r

def append_json(new_items):
    if OUT_JSON.exists():
        existing = json.loads(OUT_JSON.read_text(encoding="utf-8") or "[]")
    else:
        existing = []
    existing.extend(new_items)
    OUT_JSON.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

def persist_to_db():
    run([".venv\\Scripts\\python.exe","tools\\persist_listings.py"])

def main():
    parcels = load_parcels()
    total = len(parcels)
    for i in range(0, total, BATCH_SIZE):
        batch = parcels[i:i+BATCH_SIZE]
        print(f"Processing batch {i//BATCH_SIZE + 1} / {(total + BATCH_SIZE -1)//BATCH_SIZE}  ({len(batch)} items)")
        # write batch to parcels.txt and run fetcher
        Path("data/parcels.txt").write_text("\n".join(batch), encoding="utf-8")
        proc = run([".venv\\Scripts\\python.exe","tools\\fetch_parcels.py"], stdout=PIPE, stderr=PIPE, text=True)
        if proc.returncode != 0:
            print("Fetcher error:", proc.stderr)
            print("Sleeping 60s before retry")
            time.sleep(60)
            continue
        # read fetch output and append
        if Path("data/listings.json").exists():
            items = json.loads(Path("data/listings.json").read_text(encoding="utf-8") or "[]")
            append_json(items)
            persist_to_db()
            print("Appended", len(items), "items and persisted to DB")
        else:
            print("No listings.json produced for this batch")
        time.sleep(DELAY_BETWEEN_BATCHES)

if __name__ == "__main__":
    main()
