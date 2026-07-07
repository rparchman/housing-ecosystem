# tools/fetch_county_gis_links_improved.py
"""
Improved discovery of county GIS/open-data portal URLs for counties listed in data/counties.txt.

Outputs:
  - data/county_gis_links.csv
  - manifests/<county>.yaml

Dependencies:
  pip install requests beautifulsoup4 pyyaml
"""
import csv, time, re, sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import yaml

ROOT = Path.cwd()
COUNTIES = ROOT / "data" / "counties.txt"
OUT_CSV = ROOT / "data" / "county_gis_links.csv"
MANIFESTS = ROOT / "manifests"
HEADERS = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
PAUSE = 2.0
RETRIES = 2

def safe_name(name):
    s = name.strip()
    s = re.sub(r"[\\/:\*\?\"<>\|]+","_",s)
    s = re.sub(r"\s+"," ",s).replace(" ","_")
    return s

def read_counties():
    txt = COUNTIES.read_text(encoding="utf-8")
    # remove BOM and invisible chars
    txt = txt.replace("\ufeff","").replace("\u200b","")
    return [l.strip() for l in txt.splitlines() if l.strip()]

def parse_bing(html):
    soup = BeautifulSoup(html, "html.parser")
    item = soup.select_one("li.b_algo h2 a")
    if item and item.get("href"):
        return item["href"], item.get_text(strip=True)
    return None, None

def parse_ddg(html):
    soup = BeautifulSoup(html, "html.parser")
    a = soup.select_one("a.result__a")
    if a and a.get("href"):
        return a["href"], a.get_text(strip=True)
    return None, None

def search(url):
    for attempt in range(RETRIES):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return r.text
        except Exception as e:
            if attempt + 1 == RETRIES:
                return None
            time.sleep(1)
    return None

def search_bing(query):
    q = requests.utils.requote_uri(query)
    url = f"https://www.bing.com/search?q={q}"
    html = search(url)
    if not html:
        return None, None
    href, title = parse_bing(html)
    return href, title

def search_ddg(query):
    q = requests.utils.requote_uri(query)
    url = f"https://duckduckgo.com/html/?q={q}"
    html = search(url)
    if not html:
        return None, None
    href, title = parse_ddg(html)
    return href, title

def build_manifest(county, url, title):
    return {
        "county": f"{county}, MI",
        "source": {"name": title or "County GIS / Open Data", "url": url or "", "license": "unknown"},
        "layers": [{"name":"parcels","file":"","format":"unknown","parcel_id_field":"","geometry_field":"","last_updated":""}],
        "ingest":{"frequency":"monthly","transform_script":"","validate_script":""},
        "contact":{"name":"","email":""},
        "notes":"Auto-discovered; verify URL and parcel layer names before ingest."
    }

def main():
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    counties = read_counties()
    rows = []
    for i, county in enumerate(counties, start=1):
        query = f"{county} County MI GIS parcel open data site"
        print(f"[{i}/{len(counties)}] {county}")
        href, title = search_bing(query)
        if not href:
            href, title = search_ddg(query)
        if not href:
            # fallback: search county domain
            href = f"https://www.{county.replace(' ','').lower()}county.org"
            title = "guessed county domain (verify)"
            print("  -> fallback guess:", href)
        else:
            print("  ->", href)
        rows.append((county, href or "", title or ""))
        manifest = build_manifest(county, href or "", title or "")
        fname = MANIFESTS / f"{safe_name(county)}.yaml"
        fname.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8")
        time.sleep(PAUSE)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["county","candidate_url","title"])
        w.writerows(rows)
    print("Done. Review data/county_gis_links.csv and manifests/*.yaml")

if __name__ == "__main__":
    main()
