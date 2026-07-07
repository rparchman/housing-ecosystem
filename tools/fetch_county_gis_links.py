# tools/fetch_county_gis_links.py
"""
Discover Michigan county GIS/open-data portal URLs and write manifests.

Usage:
  .venv\Scripts\python.exe tools\fetch_county_gis_links.py

Outputs:
  - data/county_gis_links.csv   (county, candidate_url, title)
  - manifests/<safe_county_name>.yaml  (one manifest per county with discovered URL)
Requirements:
  - requests
  - beautifulsoup4
  - pyyaml

Install deps:
  .venv\Scripts\pip.exe install requests beautifulsoup4 pyyaml
"""
import csv
import time
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import yaml

ROOT = Path.cwd()
COUNTIES_TXT = ROOT / "data" / "counties.txt"
OUT_CSV = ROOT / "data" / "county_gis_links.csv"
MANIFESTS_DIR = ROOT / "manifests"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}
SEARCH_PAUSE = 1.5  # seconds between queries to be polite

# Simple safe filename
def safe_name(name: str) -> str:
    s = name.strip()
    s = re.sub(r"[\\/:\*\?\"<>\|]+", "_", s)
    s = re.sub(r"\s+", " ", s)
    s = s.replace(" ", "_")
    return s

def read_counties():
    if not COUNTIES_TXT.exists():
        raise SystemExit(f"{COUNTIES_TXT} not found. Create data/counties.txt first.")
    return [line.strip() for line in COUNTIES_TXT.read_text(encoding="utf-8").splitlines() if line.strip()]

def search_bing(query: str):
    # Use Bing search results page and parse first organic result.
    # This is a lightweight heuristic; for production use an official search API.
    q = requests.utils.requote_uri(query)
    url = f"https://www.bing.com/search?q={q}"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # Bing organic results often in <li class="b_algo"> with <h2><a href=...>
    item = soup.select_one("li.b_algo h2 a")
    if item and item.get("href"):
        title = item.get_text(strip=True)
        href = item["href"]
        return href, title
    # fallback: look for first <a> with data-cturl or similar
    a = soup.find("a", href=True)
    if a:
        return a["href"], a.get_text(strip=True) or a["href"]
    return None, None

def build_manifest(county: str, url: str, title: str):
    manifest = {
        "county": f"{county}, MI",
        "source": {
            "name": title or "County GIS / Open Data",
            "url": url or "",
            "license": "unknown"
        },
        "layers": [
            {
                "name": "parcels",
                "file": "",
                "format": "unknown",
                "parcel_id_field": "",
                "geometry_field": "",
                "last_updated": ""
            }
        ],
        "ingest": {
            "frequency": "monthly",
            "transform_script": "",
            "validate_script": ""
        },
        "contact": {
            "name": "",
            "email": ""
        },
        "notes": "Discovered automatically; verify URL and parcel layer/file names before ingest."
    }
    return manifest

def main():
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    counties = read_counties()
    rows = []
    for i, county in enumerate(counties, start=1):
        query = f"{county} County MI GIS parcel open data site"
        print(f"[{i}/{len(counties)}] Searching: {query}")
        try:
            href, title = search_bing(query)
        except Exception as e:
            print("  search failed:", e)
            href, title = None, None
        if href:
            print("  ->", href)
        else:
            print("  -> no candidate found")
        rows.append((county, href or "", title or ""))
        # write manifest even if URL empty so you can fill it manually
        manifest = build_manifest(county, href or "", title or "")
        fname = MANIFESTS_DIR / f"{safe_name(county)}.yaml"
        fname.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8")
        time.sleep(SEARCH_PAUSE)
    # write CSV
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["county", "candidate_url", "title"])
        w.writerows(rows)
    print("Wrote CSV:", OUT_CSV)
    print("Wrote manifests to:", MANIFESTS_DIR)
    print("Review data/county_gis_links.csv and manifests/*.yaml and update any missing/incorrect URLs.")

if __name__ == "__main__":
    main()
