# tools/download_parcels_from_manifests.py
"""
Download parcel layers from manifests into data/raw/<County>/parcels.geojson

Usage:
  .venv\Scripts\python.exe tools/download_parcels_from_manifests.py [--limit N] [--pause 1.5] [--force]

Outputs:
  - data/raw/<County>/parcels.geojson
  - data/county_parcel_downloads.csv (summary)
Notes:
  - Prefers explicit ArcGIS REST layer URLs (MapServer/<layer>).
  - If manifest source.url is a webapp, the script will try to find a REST endpoint on that page.
  - Beacon/qPublic and vendor viewers are skipped for automatic download; use manual export for those.
"""
import argparse
import csv
import time
import re
import urllib.parse
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup

ROOT = Path.cwd()
MANIFESTS = ROOT / "manifests"
OUT_ROOT = ROOT / "data" / "raw"
SUMMARY_CSV = ROOT / "data" / "county_parcel_downloads.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
APN_CANDIDATES = ["PID_All","PARCELID","APN","PARCEL","ParcelID","PARCEL_ID","PIN","PIN_NUM","APN_NUM","APN_NO"]

def find_mapserver_in_text(text, base_url=""):
    urls = set()
    for m in re.finditer(r"https?://[^\s'\"<>]*?/rest/services[^\s'\"<>]*", text):
        urls.add(m.group(0))
    # also find MapServer/<n>
    for m in re.finditer(r"https?://[^\s'\"<>]*/MapServer(?:/\d+)?", text, flags=re.IGNORECASE):
        urls.add(m.group(0))
    # join with base_url if relative
    return list(urls)

def normalize_layer_url(url):
    if not url:
        return ""
    # if it's an app page, leave as-is for probing
    if "/MapServer" in url or "/rest/services" in url:
        # strip query
        return url.split("?")[0]
    return ""

def probe_layer_fields(layer_url):
    try:
        q = layer_url.rstrip("/") + "?f=json"
        r = requests.get(q, headers=HEADERS, timeout=20)
        r.raise_for_status()
        j = r.json()
        # if this is a service root with layers, return first layer endpoint
        if "layers" in j and isinstance(j["layers"], list) and j["layers"]:
            # pick layer with 'Parcel' or similar in name if present
            for layer in j["layers"]:
                name = layer.get("name","") or ""
                if "parcel" in name.lower() or "tax" in name.lower() or "property" in name.lower():
                    lid = layer.get("id")
                    base = layer_url.split("/rest/services")[0] + "/rest/services"
                    # attempt to reconstruct service root + MapServer/<id>
                    # fallback to using the service URL's base
                    candidate = None
                    if "/MapServer" in layer_url:
                        candidate = re.sub(r"/MapServer.*$", "", layer_url).rstrip("/") + f"/MapServer/{lid}"
                    else:
                        candidate = layer_url.rstrip("/") + f"/MapServer/{lid}"
                    return candidate
            # fallback to first layer id
            lid = j["layers"][0].get("id")
            candidate = re.sub(r"/MapServer.*$", "", layer_url).rstrip("/") + f"/MapServer/{lid}"
            return candidate
        # if this is a layer with fields
        if "fields" in j:
            return layer_url
    except Exception:
        pass
    return ""

def download_geojson(layer_query_url, out_path, out_fields="*"):
    # layer_query_url should be MapServer/<n>
    query_url = layer_query_url.rstrip("/") + "/query"
    params = {
        "where": "1=1",
        "outFields": out_fields,
        "f": "geojson",
        "resultRecordCount": 100000
    }
    try:
        r = requests.get(query_url, params=params, headers=HEADERS, timeout=60)
        r.raise_for_status()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(r.content)
        return True, r.status_code
    except Exception as e:
        return False, str(e)

def try_find_rest_on_page(url):
    try:
        if url.startswith("//"):
            url = "https:" + url
        if not urllib.parse.urlparse(url).scheme:
            url = "https://" + url
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        text = r.text
        found = find_mapserver_in_text(text, r.url)
        if found:
            return found[0]
        # try searching script tags for rest/services
        soup = BeautifulSoup(text, "html.parser")
        for s in soup.find_all("script"):
            if s.string and "rest/services" in s.string:
                for m in re.finditer(r"https?://[^\s'\"<>]*?/rest/services[^\s'\"<>]*", s.string):
                    return m.group(0)
    except Exception:
        pass
    return ""

def process_manifest(path, force=False):
    name = path.stem
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    src = (data.get("source") or {}).get("url","") or ""
    layer_file = ""
    if data.get("layers"):
        layer_file = data["layers"][0].get("file","") or ""
    candidate = ""
    notes = ""
    # prefer explicit MapServer layer in manifest file field
    if layer_file and ("/MapServer" in layer_file or "/rest/services" in layer_file):
        candidate = normalize_layer_url(layer_file)
    # else try source url
    if not candidate and src:
        candidate = normalize_layer_url(src)
    # if still not candidate, try to find rest on the page
    if not candidate and src:
        candidate = try_find_rest_on_page(src)
        if candidate:
            notes += "found_rest_on_page;"
    # if candidate looks like a service root, probe for a parcel layer
    layer_candidate = ""
    if candidate:
        layer_candidate = probe_layer_fields(candidate)
        if layer_candidate:
            notes += "probed_layer;"
    # if we have a layer_candidate, attempt download
    out_file = OUT_ROOT / name / "parcels.geojson"
    success = False
    info = ""
    if layer_candidate:
        ok, info = download_geojson(layer_candidate, out_file, out_fields="*")
        success = ok
    else:
        info = "no_layer_candidate"
    return {
        "county": name,
        "source_url": src,
        "layer_candidate": layer_candidate,
        "downloaded": "yes" if success else "no",
        "info": str(info),
        "notes": notes
    }

def main(limit=0, pause=1.5, force=False):
    manifests = sorted(MANIFESTS.glob("*.yaml"))
    if limit and limit > 0:
        manifests = manifests[:limit]
    results = []
    for i, m in enumerate(manifests, start=1):
        print(f"[{i}/{len(manifests)}] {m.stem}")
        res = process_manifest(m, force=force)
        print("  ->", res["downloaded"], res["layer_candidate"], res["info"])
        results.append(res)
        time.sleep(pause)
    # write summary
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["county","source_url","layer_candidate","downloaded","info","notes"])
        w.writeheader()
        w.writerows(results)
    print("Wrote summary:", SUMMARY_CSV)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--pause", type=float, default=1.5)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    main(limit=args.limit, pause=args.pause, force=args.force)
