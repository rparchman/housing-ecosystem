# tools/extract_arcgis_item_and_probe.py
"""
Extract ArcGIS itemId or rest/services links from manifest source.url pages,
query ArcGIS item JSON when possible, probe MapServer layers for parcel fields,
and update manifests with candidate layer and parcel_id_field.

Usage:
  .venv\\Scripts\\python.exe tools\\extract_arcgis_item_and_probe.py [--limit N] [--pause 1.5]

Outputs:
  - data/county_arcgis_probe.csv
  - updates manifests/<County>.yaml with layers[0].file and layers[0].parcel_id_field when detected

Dependencies:
  pip install requests beautifulsoup4 pyyaml
"""
import re, time, argparse, urllib.parse
from pathlib import Path
import requests, yaml
from bs4 import BeautifulSoup

ROOT = Path.cwd()
MANIFESTS = ROOT / "manifests"
OUT_CSV = ROOT / "data" / "county_arcgis_probe.csv"
HEADERS = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
APN_CANDIDATES = ["PID_All","PARCELID","APN","PARCEL","ParcelID","PARCEL_ID","PIN","PIN_NUM","APN_NUM","APN_NO"]

def find_itemid_and_rest(html, base_url):
    itemids = set()
    rest_links = set()
    # search for itemId patterns
    for m in re.finditer(r"itemId['\"]?\s*[:=]\s*['\"]([a-zA-Z0-9]{20,40})['\"]", html):
        itemids.add(m.group(1))
    for m in re.finditer(r"\"itemId\"\s*:\s*\"([a-zA-Z0-9]{20,40})\"", html):
        itemids.add(m.group(1))
    # search for arcgis REST service links
    for m in re.finditer(r"https?://[^\s'\"<>]*?/rest/services[^\s'\"<>]*", html):
        rest_links.add(m.group(0))
    # search for maps.arcgis.com app ids
    for m in re.finditer(r"apps/(?:webappviewer|mapviewer|experience)/index.html\\?id=([a-zA-Z0-9_-]{20,40})", html):
        itemids.add(m.group(1))
    # search for item id in data attributes
    for m in re.finditer(r"data-itemid=['\"]([a-zA-Z0-9]{20,40})['\"]", html):
        itemids.add(m.group(1))
    return list(itemids), list(rest_links)

def query_arcgis_item(itemid):
    # ArcGIS Online item JSON
    url = f"https://www.arcgis.com/sharing/rest/content/items/{itemid}?f=json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def extract_service_urls_from_item(item_json):
    urls = set()
    if not item_json:
        return []
    # look in itemData for operationalLayers or webMap
    itemdata = item_json.get("data") or item_json.get("itemData") or item_json.get("data", {})
    if isinstance(itemdata, dict):
        # webmap structure
        for k in ("operationalLayers","operationalLayers"):
            for layer in itemdata.get(k, []) if itemdata.get(k) else []:
                url = layer.get("url") or layer.get("layerUrl")
                if url:
                    urls.add(url)
        # experience builder or webapp config may have widgets with config
        for v in itemdata.values():
            try:
                s = str(v)
                for m in re.finditer(r"https?://[^\s'\"<>]*?/rest/services[^\s'\"<>]*", s):
                    urls.add(m.group(0))
            except Exception:
                pass
    # also check itemJson's url fields
    for key in ("url","serviceItemId"):
        if key in item_json and isinstance(item_json[key], str) and "/rest/services" in item_json[key]:
            urls.add(item_json[key])
    return list(urls)

def probe_mapserver_for_parcel(layer_url):
    # normalize to MapServer or MapServer/<n>
    base = layer_url.split("?")[0]
    # if it's a service root, try to list layers
    try:
        if base.endswith("/MapServer") or "/MapServer/" in base:
            # if ends with /MapServer, query service JSON
            if base.endswith("/MapServer"):
                r = requests.get(base + "?f=json", headers=HEADERS, timeout=20)
                r.raise_for_status()
                j = r.json()
                layers = j.get("layers", []) or []
                # prefer layer with parcel in name
                for layer in layers:
                    name = layer.get("name","") or ""
                    if "parcel" in name.lower() or "tax" in name.lower() or "property" in name.lower():
                        lid = layer.get("id")
                        candidate = base.rstrip("/") + f"/{lid}"
                        # probe fields
                        try:
                            r2 = requests.get(candidate + "?f=json", headers=HEADERS, timeout=20)
                            r2.raise_for_status()
                            j2 = r2.json()
                            for f in j2.get("fields", []):
                                fname = f.get("name","").upper()
                                for cand in APN_CANDIDATES:
                                    if cand.upper() == fname or cand.upper() in fname:
                                        return candidate, f.get("name")
                        except Exception:
                            continue
                # fallback to first layer
                if layers:
                    lid = layers[0].get("id")
                    candidate = base.rstrip("/") + f"/{lid}"
                    return candidate, ""
            else:
                # if base already points to a layer, query fields
                r = requests.get(base + "?f=json", headers=HEADERS, timeout=20)
                r.raise_for_status()
                j = r.json()
                for f in j.get("fields", []):
                    fname = f.get("name","").upper()
                    for cand in APN_CANDIDATES:
                        if cand.upper() == fname or cand.upper() in fname:
                            return base, f.get("name")
                return base, ""
    except Exception:
        pass
    return "", ""

def update_manifest(county, url, layer, field):
    fname = MANIFESTS / (county.replace(" ", "_") + ".yaml")
    if fname.exists():
        m = yaml.safe_load(fname.read_text(encoding="utf-8")) or {}
    else:
        m = {"county": f"{county}, MI", "source": {"url": url}, "layers": [{"name":"parcels","file":"","parcel_id_field":""}]}
    m.setdefault("source", {})
    m["source"]["url"] = url or m["source"].get("url","")
    m.setdefault("layers", [{"name":"parcels","file":"","parcel_id_field":""}])
    if layer:
        m["layers"][0]["file"] = layer
        m["layers"][0]["format"] = "arcgis-rest"
    if field:
        m["layers"][0]["parcel_id_field"] = field
    fname.write_text(yaml.safe_dump(m, sort_keys=False, allow_unicode=True), encoding="utf-8")

def main(limit=0, pause=1.5):
    manifests = sorted(MANIFESTS.glob("*.yaml"))
    if limit and limit>0:
        manifests = manifests[:limit]
    results = []
    for i, m in enumerate(manifests, start=1):
        county = m.stem.replace("_"," ")
        print(f"[{i}/{len(manifests)}] {county}")
        data = yaml.safe_load(m.read_text(encoding="utf-8")) or {}
        src = (data.get("source") or {}).get("url","") or ""
        if not src:
            results.append({"county":county,"resolved_url":"","status":"no_source"})
            continue
        try:
            r = requests.get(src, headers=HEADERS, timeout=20)
            r.raise_for_status()
            html = r.text
        except Exception as e:
            html = ""
        itemids, restlinks = find_itemid_and_rest(html, src)
        layer_candidate = ""
        parcel_field = ""
        notes = []
        # try itemids first
        for itemid in itemids:
            item = query_arcgis_item(itemid)
            if item:
                notes.append("item_json_ok")
                services = extract_service_urls_from_item(item)
                for s in services:
                    cand_layer, cand_field = probe_mapserver_for_parcel(s)
                    if cand_layer:
                        layer_candidate = cand_layer
                        parcel_field = cand_field
                        break
            if layer_candidate:
                break
        # if not found, try restlinks found in page
        if not layer_candidate:
            for rl in restlinks:
                cand_layer, cand_field = probe_mapserver_for_parcel(rl)
                if cand_layer:
                    layer_candidate = cand_layer
                    parcel_field = cand_field
                    break
        # update manifest if found
        update_manifest(county, src, layer_candidate, parcel_field)
        status = "found" if layer_candidate else "not_found"
        results.append({"county":county,"resolved_url":src,"status":status,"layer_candidate":layer_candidate,"parcel_id_field":parcel_field,"notes":";".join(notes)})
        time.sleep(pause)
    # write CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    import csv
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["county","resolved_url","status","layer_candidate","parcel_id_field","notes"])
        w.writeheader()
        w.writerows(results)
    print("Wrote", OUT_CSV)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--pause", type=float, default=1.5)
    args = p.parse_args()
    main(limit=args.limit, pause=args.pause)
