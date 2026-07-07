#!/usr/bin/env python3
"""
tools/find_parcel_services.py

Open viewer pages headful, check public accessibility, capture ArcGIS requests,
probe service/layer metadata, test a minimal query, and output verified parcel URLs.

Outputs:
  - data/verified_parcels.csv   (county, viewer_url, candidate_url, probe_note, parcel_field_candidates)
  - data/verified_parcels_debug.json  (detailed per-candidate info)
  - manifests/<County>.yaml for each verified candidate (layers[0].file set)

Usage:
  .venv\Scripts\python.exe tools/find_parcel_services.py --input manifests_list.txt --limit 20 --pause 4.0
"""
import time
import re
import csv
import json
import socket
import argparse
import urllib.parse
from pathlib import Path

import requests
import yaml
from playwright.sync_api import sync_playwright

ROOT = Path.cwd()
OUT_DIR = ROOT / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)
MANIFESTS_DIR = ROOT / "manifests"
OUT_CSV = OUT_DIR / "verified_parcels.csv"
OUT_DEBUG = OUT_DIR / "verified_parcels_debug.json"

# Patterns and filters
SERVICE_PATTERNS = ("/rest/services", "/MapServer", "/FeatureServer")
REJECT_PATTERNS = re.compile(
    r"\.(?:png|jpg|jpeg|svg|gif|ico|css|js|woff2?|ttf)$|/widgets/|/images/|/tile/|/tiles/|/tilemap/|/static/|/icons/|/resources/",
    flags=re.IGNORECASE,
)
PARCEL_FIELD_KEYWORDS = ("APN", "PARCEL", "PIN", "PARID", "PARCEL_NO", "PARCEL_NUM", "PARID")

# Helpers
def is_resolvable(hostname: str) -> bool:
    try:
        socket.gethostbyname(hostname)
        return True
    except Exception:
        return False

def looks_like_arcgis(u: str) -> bool:
    u0 = u.split("?")[0].lower()
    if REJECT_PATTERNS.search(u0):
        return False
    return any(p.lower() in u0 for p in SERVICE_PATTERNS)

def derive_service_root_from_query(url: str) -> str:
    u = url.split("?")[0]
    if u.endswith("/query"):
        return u.rsplit("/query", 1)[0]
    parts = u.split("/")
    for i, p in enumerate(parts):
        if p.lower() in ("featureserver", "mapserver"):
            if i + 1 < len(parts) and parts[i+1].isdigit():
                return "/".join(parts[: i + 2])
            return "/".join(parts[: i + 1])
    return u

def probe_metadata(candidate_root: str, timeout=8):
    probe_url = candidate_root.rstrip("/") + "?f=json"
    try:
        r = requests.get(probe_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
    except Exception as e:
        return False, f"request_exception:{e}", None
    if r.status_code != 200:
        return False, f"status:{r.status_code}", None
    ctype = r.headers.get("Content-Type", "")
    if "application/json" not in ctype and "text/javascript" not in ctype and "application/geo+json" not in ctype:
        return False, f"non_json_content_type:{ctype}", None
    try:
        j = r.json()
    except Exception as e:
        return False, f"json_parse_error:{e}", None
    if isinstance(j, dict) and "error" in j:
        return False, "arcgis_error_payload", None
    sample = {}
    if isinstance(j, dict):
        if "fields" in j and isinstance(j["fields"], list):
            sample["fields_count"] = len(j["fields"])
            names = [f.get("name","").upper() for f in j["fields"]]
            parcel_candidates = [n for n in names if any(k in n for k in PARCEL_FIELD_KEYWORDS)]
            sample["parcel_field_candidates"] = parcel_candidates[:3]
        if "geometryType" in j:
            sample["geometryType"] = j["geometryType"]
        if "layers" in j and isinstance(j["layers"], list):
            sample["layers_count"] = len(j["layers"])
    ok = bool(sample.get("fields_count") or sample.get("layers_count") or sample.get("geometryType"))
    note = "ok" if ok else "unexpected_json_shape"
    return ok, note, sample

def test_minimal_query(service_or_layer_url: str, timeout=10):
    base = service_or_layer_url.rstrip("/")
    if base.lower().endswith("/mapserver") or base.lower().endswith("/featureserver"):
        ok, note, meta = probe_metadata(base)
        if ok and meta and meta.get("layers_count"):
            try:
                r = requests.get(base + "?f=json", headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
                j = r.json()
                layers = j.get("layers") or []
                if layers:
                    lid = layers[0].get("id")
                    if lid is not None:
                        base = base + f"/{lid}"
            except Exception:
                pass
    q1 = base + "/query?where=1=1&outFields=*&resultRecordCount=1&f=json"
    try:
        r1 = requests.get(q1, headers={"User-Agent":"Mozilla/5.0"}, timeout=timeout)
        if r1.status_code == 200:
            try:
                j1 = r1.json()
                if isinstance(j1, dict) and "error" not in j1:
                    return True, "arcgis_json_ok", r1.status_code
            except Exception:
                pass
    except Exception:
        pass
    q2 = base + "/query?where=1=1&outFields=*&resultRecordCount=1&f=geojson"
    try:
        r2 = requests.get(q2, headers={"User-Agent":"Mozilla/5.0"}, timeout=timeout)
        if r2.status_code == 200:
            ctype = r2.headers.get("Content-Type","")
            if "json" in ctype:
                return True, "geojson_ok", r2.status_code
    except Exception:
        pass
    return False, "no_query_result", None

def safe_goto(page, url, timeout=120000, retries=1, screenshot_on_fail=None):
    for attempt in range(1, retries + 2):
        try:
            page.goto(url, timeout=timeout)
            return True
        except Exception as e:
            print(f"goto attempt {attempt} failed: {e}")
            if screenshot_on_fail:
                try:
                    page.screenshot(path=screenshot_on_fail, full_page=True)
                except Exception:
                    pass
            if attempt <= retries:
                time.sleep(2)
    return False

def write_manifest_snippet(county, viewer_url, candidate_url):
    fname = MANIFESTS_DIR / (county.replace(" ", "_") + ".yaml")
    if fname.exists():
        m = yaml.safe_load(fname.read_text(encoding="utf-8")) or {}
    else:
        m = {"county": f"{county}", "source": {"url": viewer_url}, "layers": [{"name":"parcels","file":"","parcel_id_field":""}]}
    m.setdefault("source", {})
    m["source"]["url"] = viewer_url or m["source"].get("url","")
    m.setdefault("layers", [{"name":"parcels","file":"","parcel_id_field":""}])
    if candidate_url:
        m["layers"][0]["file"] = candidate_url
        m["layers"][0]["format"] = "arcgis-rest"
    fname.write_text(yaml.safe_dump(m, sort_keys=False, allow_unicode=True), encoding="utf-8")

# Main runner
def main(input_file=None, limit=0, pause=4.0, headless=False):
    # Build list of viewer URLs to check
    viewers = []
    if input_file:
        p = Path(input_file)
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                s = line.strip()
                if s:
                    viewers.append(s)
    else:
        # fallback: scan manifests dir for source.url entries
        for f in sorted(MANIFESTS_DIR.glob("*.yaml")):
            try:
                m = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
                src = (m.get("source") or {}).get("url","")
                county = f.stem.replace("_"," ")
                if src:
                    viewers.append((county, src))
            except Exception:
                continue

    # normalize viewers list to tuples (county, url)
    normalized = []
    for item in viewers:
        if isinstance(item, tuple):
            normalized.append(item)
        else:
            # try to infer county from URL host
            parsed = urllib.parse.urlparse(item)
            host = parsed.hostname or item
            county_guess = host.split(".")[0]
            normalized.append((county_guess, item))
    if limit and limit > 0:
        normalized = normalized[:limit]

    results = []
    debug = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=["--disable-features=IsolateOrigins,site-per-process"])
        for i, (county, viewer_url) in enumerate(normalized, start=1):
            print(f"[{i}/{len(normalized)}] {county} -> {viewer_url}")
            # normalize URL
            if viewer_url.startswith("//"):
                viewer_url = "https:" + viewer_url
            if not urllib.parse.urlparse(viewer_url).scheme:
                viewer_url = "https://" + viewer_url
            parsed = urllib.parse.urlparse(viewer_url)
            host = parsed.hostname or ""
            if not host or not is_resolvable(host):
                print(f"  unresolved host: {host}; skipping")
                results.append({"county": county, "viewer_url": viewer_url, "candidate": "", "probe_note": "unresolved_host"})
                continue

            # per-page capture
            captured_requests = []
            responses_map = {}  # url_without_query -> (status, content_type)

            try:
                context = browser.new_context()
                page = context.new_page()

                def on_request(req):
                    try:
                        captured_requests.append(req)
                    except Exception:
                        pass

                def on_response(resp):
                    try:
                        u = resp.url.split("?")[0]
                        status = resp.status
                        ctype = ""
                        try:
                            ctype = resp.headers.get("content-type", "")
                        except Exception:
                            ctype = ""
                        responses_map[u] = (status, ctype)
                    except Exception:
                        pass

                page.on("request", on_request)
                page.on("response", on_response)

                nav_ok = safe_goto(page, viewer_url, timeout=120000, retries=1, screenshot_on_fail=str(OUT_DIR / "nav_error.png"))
                if not nav_ok:
                    print("  navigation failed; skipping")
                    results.append({"county": county, "viewer_url": viewer_url, "candidate": "", "probe_note": "navigation_failed"})
                    try:
                        page.close()
                        context.close()
                    except Exception:
                        pass
                    continue

                time.sleep(pause)
                try:
                    page.mouse.wheel(0, 1000)
                except Exception:
                    pass
                time.sleep(1.0)

                # inspect captured requests
                seen = set()
                raw_candidates = []
                for req in captured_requests:
                    try:
                        url = req.url
                        u0 = url.split("?")[0]
                        if u0 in seen:
                            continue
                        seen.add(u0)
                        if not looks_like_arcgis(u0):
                            continue
                        raw_candidates.append(url)
                    except Exception:
                        continue

                # filter and probe
                filtered = []
                for url in raw_candidates:
                    u0 = url.split("?")[0]
                    # skip tile endpoints explicitly
                    if re.search(r"/(?:/tile/|/tilemap/|/tiles/|/MapServer/tile)", u0, flags=re.IGNORECASE):
                        continue
                    filtered.append(u0)

                verified = []
                for c in filtered:
                    candidate_root = derive_service_root_from_query(c)
                    # if candidate_root is a service root, try to expand to a layer
                    expanded = None
                    if candidate_root.rstrip("/").lower().endswith("/mapserver") or candidate_root.rstrip("/").lower().endswith("/featureserver"):
                        expanded = None
                        try:
                            ok_e, note_e, meta_e = probe_metadata(candidate_root)
                            if ok_e and meta_e and meta_e.get("layers_count"):
                                # expand to first likely layer
                                try:
                                    r = requests.get(candidate_root.rstrip("/") + "?f=json", headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
                                    j = r.json()
                                    layers = j.get("layers") or []
                                    for layer in layers:
                                        name = (layer.get("name") or "").lower()
                                        lid = layer.get("id")
                                        if lid is None:
                                            continue
                                        if any(k.lower() in name for k in ("parcel","tax","property","apn","pin")):
                                            expanded = candidate_root.rstrip("/") + f"/{lid}"
                                            break
                                    if not expanded and layers:
                                        first = layers[0].get("id")
                                        if first is not None:
                                            expanded = candidate_root.rstrip("/") + f"/{first}"
                                except Exception:
                                    expanded = None
                        except Exception:
                            expanded = None
                    probe_target = expanded or candidate_root
                    ok, note, meta = probe_metadata(probe_target)
                    if not ok:
                        # if probe failed on layer, try service root without id
                        if probe_target.rstrip("/").split("/")[-1].isdigit():
                            service_root = "/".join(probe_target.rstrip("/").split("/")[:-1])
                            ok2, note2, meta2 = probe_metadata(service_root)
                            if ok2:
                                ok, note, meta = ok2, note2, meta2
                    if ok:
                        # test minimal query
                        q_ok, q_note, q_status = test_minimal_query(probe_target)
                        if q_ok:
                            verified.append({"candidate": probe_target, "probe_note": note, "metadata": meta, "query_note": q_note})
                        else:
                            # still accept if metadata looks good but query failed due to token; mark accordingly
                            verified.append({"candidate": probe_target, "probe_note": note + ";query_failed", "metadata": meta, "query_note": q_note})
                    else:
                        # record debug info
                        debug.append({"county": county, "viewer_url": viewer_url, "candidate_root": probe_target, "probe_note": note, "responses_map": responses_map.get(c)})
                # pick best verified candidate (prefer parcel-like metadata)
                chosen = ""
                chosen_meta = None
                chosen_note = ""
                for v in verified:
                    meta = v.get("metadata") or {}
                    candidates = meta.get("parcel_field_candidates") or []
                    if candidates:
                        chosen = v["candidate"]
                        chosen_meta = meta
                        chosen_note = v["probe_note"]
                        break
                if not chosen and verified:
                    chosen = verified[0]["candidate"]
                    chosen_meta = verified[0].get("metadata")
                    chosen_note = verified[0].get("probe_note","")
                if chosen:
                    parcel_fields = chosen_meta.get("parcel_field_candidates") if chosen_meta else []
                    results.append({"county": county, "viewer_url": viewer_url, "candidate": chosen, "probe_note": chosen_note, "parcel_field_candidates": parcel_fields})
                    write_manifest_snippet(county, viewer_url, chosen)
                else:
                    results.append({"county": county, "viewer_url": viewer_url, "candidate": "", "probe_note": "none_found"})
                # append debug entries for this viewer
                debug.append({"county": county, "viewer_url": viewer_url, "raw_candidates": raw_candidates, "filtered": filtered, "verified": verified, "responses_map_sample": dict(list(responses_map.items())[:5])})
            except Exception as e:
                print("  error:", e)
                results.append({"county": county, "viewer_url": viewer_url, "candidate": "", "probe_note": f"error:{e}"})
            finally:
                try:
                    page.close()
                    context.close()
                except Exception:
                    pass
                time.sleep(1.0)
        browser.close()

    # write outputs
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["county", "viewer_url", "candidate", "probe_note", "parcel_field_candidates"])
        w.writeheader()
        for r in results:
            w.writerow(r)
    with OUT_DEBUG.open("w", encoding="utf-8") as f:
        json.dump(debug, f, indent=2, ensure_ascii=False)
    print("Wrote", OUT_CSV, "and", OUT_DEBUG)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="Text file with one viewer URL per line (optional)", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--pause", type=float, default=4.0)
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args()
    main(input_file=args.input, limit=args.limit, pause=args.pause, headless=args.headless)
