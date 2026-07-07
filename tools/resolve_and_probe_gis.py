# tools/resolve_and_probe_gis.py
"""
Resolve wrapper links and probe candidate GIS portals for parcel layer + parcel id field.

Outputs:
  - data/county_gis_probed.csv   (county,resolved_url,probe_status,layer_candidate,parcel_id_field,notes)
  - updates manifests/<County>.yaml with source.url and candidate layer/field when found

Usage:
  .venv\Scripts\python.exe tools\resolve_and_probe_gis.py [--limit N] [--pause 1.5]

Dependencies:
  pip install requests beautifulsoup4 pyyaml
"""
import time
import csv
import argparse
import urllib.parse
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import yaml
import re

ROOT = Path.cwd()
IN_CSV = ROOT / "data" / "county_gis_candidates.csv"
OUT_CSV = ROOT / "data" / "county_gis_probed.csv"
MANIFESTS = ROOT / "manifests"
HEADERS = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
APN_CANDIDATES = ["PID_All","PARCELID","APN","PARCEL","parcel","ParcelID","PARCEL_ID","PIN","PIN_NUM","APN_NUM","APN_NO"]

def decode_wrapper(url: str) -> str:
    if not url:
        return ""
    # DuckDuckGo wrapper: //duckduckgo.com/l/?uddg=<urlencoded>
    if "duckduckgo.com/l/?" in url and "uddg=" in url:
        try:
            q = urllib.parse.urlparse(url).query
            qs = urllib.parse.parse_qs(q)
            if "uddg" in qs:
                return urllib.parse.unquote(qs["uddg"][0])
        except Exception:
            pass
    # Bing wrapper: contains u= param
    try:
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        if "u" in qs:
            return urllib.parse.unquote(qs["u"][0])
    except Exception:
        pass
    return url

def follow_redirect(url: str, timeout=20) -> str:
    if not url:
        return ""
    try:
        # ensure scheme
        if url.startswith("//"):
            url = "https:" + url
        if not urllib.parse.urlparse(url).scheme:
            url = "https://" + url
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return r.url
    except Exception:
        return url

def find_arcgis_rest_links(html: str, base_url: str):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/rest/services" in href or "arcgis.com" in href and "/rest/services" in href:
            if href.startswith("/"):
                href = urllib.parse.urljoin(base_url, href)
            links.add(href)
    # also search raw text for rest/services
    for m in re.finditer(r"https?://[^\s'\"<>]*?/rest/services[^\s'\"<>]*", html):
        links.add(m.group(0))
    return list(links)

def probe_arcgis_service(service_url: str):
    """
    Given a MapServer or service URL, try to enumerate layers and fields.
    Returns (best_layer_url, best_layer_name, best_field, notes)
    """
    # normalize: if service_url ends with /MapServer or /MapServer/0 etc.
    try:
        if not service_url:
            return ("", "", "", "no service url")
        # if it's a webapp viewer, try to find rest/services links on the page
        if "/rest/services" not in service_url and not service_url.endswith("/MapServer"):
            # try to fetch page and search for rest links
            r = requests.get(service_url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            rest_links = find_arcgis_rest_links(r.text, r.url)
            if rest_links:
                service_url = rest_links[0]
            else:
                # try common pattern: replace /apps/... with /rest/services
                if "maps.arcgis.com" in service_url or "arcgis.com/apps" in service_url:
                    # attempt to find a MapServer by appending /rest/services (best-effort)
                    # leave as-is for now
                    pass
        # if the URL points to a MapServer layer (ends with /0 etc), query fields
        # try both as-is and with ?f=json
        candidates = [service_url]
        if not service_url.endswith("?f=json"):
            candidates.append(service_url.rstrip("/") + "?f=json")
        # if it's a service root, try to list layers
        for cand in candidates:
            try:
                r = requests.get(cand, headers=HEADERS, timeout=15)
                if r.status_code != 200:
                    continue
                j = r.json()
                # if this is a MapServer with 'layers' or 'fields'
                if "layers" in j or "fields" in j or "featureTypes" in j:
                    # if top-level has layers list, iterate
                    layers = []
                    if "layers" in j and isinstance(j["layers"], list):
                        layers = j["layers"]
                        # try to probe each layer's endpoint
                        for layer in layers:
                            lid = layer.get("id")
                            lname = layer.get("name")
                            layer_url = re.sub(r"/MapServer.*$", "", cand).rstrip("/") + f"/MapServer/{lid}"
                            try:
                                r2 = requests.get(layer_url + "?f=json", headers=HEADERS, timeout=15)
                                if r2.status_code != 200:
                                    continue
                                j2 = r2.json()
                                fields = j2.get("fields", [])
                                # find best field
                                for f in fields:
                                    fname = f.get("name","").upper()
                                    for cand_field in APN_CANDIDATES:
                                        if cand_field.upper() == fname or cand_field.upper() in fname:
                                            return (layer_url, lname, f.get("name"), "matched_field")
                            except Exception:
                                continue
                    # if this response itself is a layer with fields
                    if "fields" in j:
                        fields = j.get("fields", [])
                        for f in fields:
                            fname = f.get("name","").upper()
                            for cand_field in APN_CANDIDATES:
                                if cand_field.upper() == fname or cand_field.upper() in fname:
                                    # return this layer
                                    base = cand.split("?")[0]
                                    return (base, j.get("name",""), f.get("name"), "matched_field")
            except Exception:
                continue
        return ("", "", "", "no_arcgis_layer_found")
    except Exception as e:
        return ("", "", "", f"error:{e}")

def update_manifest(county: str, url: str, layer_url: str, parcel_field: str):
    fname = MANIFESTS / (county.replace(" ", "_") + ".yaml")
    if not fname.exists():
        # create a basic manifest
        manifest = {
            "county": f"{county}, MI",
            "source": {"name": "Auto-discovered", "url": url or "", "license": "unknown"},
            "layers": [{"name":"parcels","file": layer_url or "", "format":"arcgis-rest" if layer_url else "unknown", "parcel_id_field": parcel_field or ""}],
            "notes": "Auto-probed; verify before ingest."
        }
    else:
        try:
            manifest = yaml.safe_load(fname.read_text(encoding="utf-8")) or {}
        except Exception:
            manifest = {}
        manifest.setdefault("source", {})
        manifest["source"]["url"] = url or manifest["source"].get("url","")
        manifest.setdefault("layers", [{"name":"parcels","file":"","format":"unknown","parcel_id_field":""}])
        manifest["layers"][0]["file"] = layer_url or manifest["layers"][0].get("file","")
        manifest["layers"][0]["parcel_id_field"] = parcel_field or manifest["layers"][0].get("parcel_id_field","")
    fname.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8")

def main(limit=0, pause=1.5):
    if not IN_CSV.exists():
        print("Input CSV not found:", IN_CSV)
        return
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    rows = []
    with IN_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        items = list(reader)
    if limit and limit > 0:
        items = items[:limit]
    for i, r in enumerate(items, start=1):
        county = r.get("county","").strip()
        candidate = (r.get("candidate_url") or r.get("candidate_url","") or r.get("candidate_url","")).strip()
        print(f"[{i}/{len(items)}] {county}")
        resolved = decode_wrapper(candidate)
        resolved = follow_redirect(resolved)
        print("  resolved ->", resolved)
        layer_candidate = ""
        parcel_field = ""
        notes = ""
        # quick heuristics
        if "arcgis" in (resolved or "").lower() or "maps.arcgis.com" in (resolved or "").lower():
            layer_url, layer_name, field, note = probe_arcgis_service(resolved)
            layer_candidate = layer_url or layer_name or ""
            parcel_field = field or ""
            notes = note
            print("  probe:", notes, "layer:", layer_candidate, "field:", parcel_field)
        else:
            # try fetching page and searching for rest/services links
            try:
                rpage = requests.get(resolved, headers=HEADERS, timeout=15)
                if rpage.status_code == 200:
                    rest_links = find_arcgis_rest_links(rpage.text, rpage.url)
                    if rest_links:
                        # probe first rest link
                        layer_url, layer_name, field, note = probe_arcgis_service(rest_links[0])
                        layer_candidate = layer_url or layer_name or rest_links[0]
                        parcel_field = field or ""
                        notes = "found_rest_on_page:" + note
                        print("  found rest on page ->", rest_links[0], "probe:", note)
                    else:
                        notes = "no_rest_found_on_page"
                else:
                    notes = f"page_status_{rpage.status_code}"
            except Exception as e:
                notes = f"page_fetch_error:{e}"
        # update manifest with best guesses
        update_manifest(county, resolved, layer_candidate, parcel_field)
        rows.append({
            "county": county,
            "resolved_url": resolved,
            "probe_status": notes,
            "layer_candidate": layer_candidate,
            "parcel_id_field": parcel_field
        })
        time.sleep(pause)
    # write CSV
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["county","resolved_url","probe_status","layer_candidate","parcel_id_field"])
        w.writeheader()
        w.writerows(rows)
    print("Wrote:", OUT_CSV)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--pause", type=float, default=1.5)
    args = p.parse_args()
    main(limit=args.limit, pause=args.pause)
