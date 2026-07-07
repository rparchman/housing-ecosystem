# tools/persist_listings.py
import json, sqlite3
from pathlib import Path

DB = Path("data") / "listings.db"
IN = Path("data") / "listings.json"

data = json.loads(IN.read_text(encoding="utf-8"))
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute('''
  CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY,
    parcel TEXT,
    address TEXT,
    price TEXT,
    status TEXT,
    raw TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  )
''')
for it in data:
  cur.execute('INSERT INTO listings (parcel,address,price,status,raw) VALUES (?,?,?,?,?)',
              (it.get("parcel"), it.get("address"), it.get("price"), it.get("status"), json.dumps(it.get("raw"))))
conn.commit()
conn.close()
print("persisted", len(data))
