# tools/auto_search_county_gis.py
"""
Auto-search county GIS portals for Michigan counties.

Outputs:
  - data/county_gis_candidates.csv   (county,candidate_url,title,score,reason)
  - manifests/<County>.yaml          (one manifest per county with candidate source.url)

Dependencies:
  pip install requests beautifulsoup4 pyyaml

Usage:
  .venv\Scripts\python.exe tools/auto_search_county_gis.py
  Optional args:
    --counties-file PATH    (default: data/counties.txt)
    --out-csv PATH          (default: data/county_gis_candidates.csv)
    --manifests-dir PATH    (default: manifests)
    --pause FLOAT           (seconds between queries, default 1.5)
    --limit N               (limit to first N counties)
"""
import time
import re
import csv
import argparse
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import yaml

# --- Config / keywords ---
KEYWORDS = ["arcgis", "beacon", "qpublic", "parcel", "assessor", "gis", "maps", "viewer", "opendata", "open-data", "data"]
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# --- Helpers ---
def safe_name(name: str) -> str:
    s = re.sub(r"[\\/:\*\?\"<>\|]+", "_", name).strip()
    return re.sub(r"\s+", "_", s)

def read_counties(path: Path):
    txt = path.read_text(encoding="utf-8").replace("\ufeff", "").replace("\u200b", "")
    return [l.strip() for l in txt.splitlines() if l.strip()]

def ddg_search(query: str):
    q = urllib.parse.quote_plus(query)
    url = f"https://duckduckgo.com/html/?q={q}"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    a = soup.select_one("a.result__a")
    if a and a.get("href"):
        return a["href"], a.get_text(strip=True)
    return None, None

def bing_search(query: str):
    q = urllib.parse.quote_plus(query)
    url = f"https://www.bing.com/search?q={q}"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    a = soup.select_one("li.b_algo h2 a")
    if a and a.get("href"):
        return a["href"], a.get_text(strip=True)
    return None, None

def resolve_redirect(url: str):
    if not url:
        return ""
    # decode common Bing wrapper u= param
    try:
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        if "u" in qs:
            cand = qs["u"][0]
            dec = urllib.parse.unquote(cand)
            if dec.startswith("http"):
                return dec
    except Exception:
        pass
    # follow redirects to get final URL
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        return r.url
    except Exception:
        return url

def score_url(url: str):
    if not url:
        return 0, "empty"
    u = url.lower()
    reasons = [k for k in KEYWORDS if k in u]
    return len(reasons), ";".join(reasons) if reasons else "none"

def build_manifest(county: str, url: str, title: str, reason: str):
    return {
        "county": f"{county}, MI",
        "source": {"name": title or "County GIS candidate", "url": url or "", "license": "unknown"},
        "layers": [{"name": "parcels", "file": "", "format": "unknown", "parcel_id_field": "", "geometry_field": "", "last_updated": ""}],
        "ingest": {"frequency": "monthly"},
        "contact": {"name": "", "email": ""},
        "notes": f"Auto-candidate (score_reasons={reason}). Verify before ingest."
    }

# --- Main ---
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--counties-file", default="data/counties.txt")
    p.add_argument("--out-csv", default="data/county_gis_candidates.csv")
    p.add_argument("--manifests-dir", default="manifests")
    p.add_argument("--pause", type=float, default=1.5)
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args()

    counties_file = Path(args.counties_file)
    out_csv = Path(args.out_csv)
    manifests_dir = Path(args.manifests_dir)
    manifests_dir.mkdir(parents=True, exist_ok=True)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    counties = read_counties(counties_file)
    if args.limit and args.limit > 0:
        counties = counties[: args.limit]

    rows = []
    for i, county in enumerate(counties, start=1):
        query = f"{county} County MI GIS parcel viewer"
        print(f"[{i}/{len(counties)}] Searching: {query}")
        href, title = None, None
        try:
            href, title = ddg_search(query)
        except Exception:
            pass
        if not href:
            try:
                href, title = bing_search(query)
            except Exception:
                pass
        resolved = resolve_redirect(href) if href else ""
        sc, reason = score_url(resolved)
        print("  ->", resolved or "(none)", "score:", sc, reason)
        rows.append((county, resolved or "", title or "", sc, reason))
        manifest = build_manifest(county, resolved or "", title or "", reason)
        fname = manifests_dir / f"{safe_name(county)}.yaml"
        fname.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8")
        time.sleep(args.pause)

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["county", "candidate_url", "title", "score", "reason"])
        w.writerows(rows)

    print("Wrote:", out_csv)
    print("Wrote manifests to:", manifests_dir)

if __name__ == "__main__":
    main()
