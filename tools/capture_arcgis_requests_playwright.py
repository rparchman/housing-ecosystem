# tools/capture_arcgis_requests_playwright.py
"""
Capture ArcGIS service requests from a headful browser session,
reconstruct cURL for JSON responses, probe layer metadata, and test a minimal query.

Usage:
  .venv\Scripts\python.exe tools\capture_arcgis_requests_playwright.py "https://viewer-url" --pause 4.0

Outputs:
  - data/captured_arcgis_requests.csv  (columns: url, status, content_type, curl, probe_ok, probe_note, metadata_sample)
  - data/captured_arcgis_debug.json    (detailed per-request info)
"""
import sys
import time
import json
import argparse
import urllib.parse
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright

OUT_DIR = Path("data")
OUT_DIR.mkdir(parents=True, exist_ok=True)
CSV_OUT = OUT_DIR / "captured_arcgis_requests.csv"
JSON_OUT = OUT_DIR / "captured_arcgis_debug.json"

# Patterns to look for in URLs
SERVICE_PATTERNS = ("/rest/services", "/MapServer", "/FeatureServer")
REJECT_PATTERNS = ("/widgets/", "/images/", "/tile", "/tiles", "/tilemap", ".png", ".jpg", ".svg", ".css", ".js")

def looks_like_arcgis(u: str) -> bool:
    u0 = u.split("?")[0].lower()
    if any(p in u0 for p in REJECT_PATTERNS):
        return False
    return any(p.lower() in u0 for p in SERVICE_PATTERNS)

def build_curl_from_request(req):
    """Reconstruct a cURL command from a Playwright Request object (best-effort)."""
    method = req.method
    url = req.url
    headers = req.headers.copy()
    # remove headers that curl will add automatically or that are large
    headers.pop("content-length", None)
    headers.pop("accept-encoding", None)
    header_parts = []
    for k, v in headers.items():
        # escape quotes
        header_parts.append(f"-H '{k}: {v}'")
    data = None
    try:
        post = req.post_data
        if post:
            data = post
    except Exception:
        data = None
    curl = f"curl -X {method} " + " ".join(header_parts) + f" '{url}'"
    if data:
        # escape single quotes in data
        safe = data.replace("'", "'\"'\"'")
        curl += f" --data '{safe}'"
    return curl

def derive_service_root_from_query(url: str) -> str:
    """
    If url ends with /query or /query?..., return the base service/layer URL without /query.
    If url already looks like a MapServer/FeatureServer root or layer, return that.
    """
    u = url.split("?")[0]
    if u.endswith("/query"):
        return u.rsplit("/query", 1)[0]
    # if it ends with /FeatureServer/<id>/something, try to reduce to /FeatureServer/<id>
    parts = u.split("/")
    # find FeatureServer or MapServer in parts
    for i, p in enumerate(parts):
        if p.lower() in ("featureserver", "mapserver"):
            # keep up to the id if present
            if i + 1 < len(parts) and parts[i+1].isdigit():
                return "/".join(parts[: i + 2])
            return "/".join(parts[: i + 1])
    return u

def probe_metadata(candidate_root: str, timeout=8):
    """
    Probe candidate_root?f=json for metadata. Return (ok, note, metadata_sample)
    metadata_sample is a small dict with keys found (fields_count, geometryType, layers_count)
    """
    probe_url = candidate_root.rstrip("/") + "?f=json"
    try:
        r = requests.get(probe_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
    except Exception as e:
        return False, f"request_exception:{e}", None
    if r.status_code != 200:
        return False, f"status:{r.status_code}", None
    ctype = r.headers.get("Content-Type", "")
    if "application/json" not in ctype and "text/javascript" not in ctype:
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
            # try to find parcel-like field names
            names = [f.get("name","").upper() for f in j["fields"]]
            parcel_candidates = [n for n in names if any(k in n for k in ("APN","PARCEL","PIN","PARID","PARID","PARCEL_NO","PARCEL_NUM"))]
            sample["parcel_field_candidates"] = parcel_candidates[:3]
        if "geometryType" in j:
            sample["geometryType"] = j["geometryType"]
        if "layers" in j and isinstance(j["layers"], list):
            sample["layers_count"] = len(j["layers"])
    # Accept if fields or layers or geometryType present
    ok = bool(sample.get("fields_count") or sample.get("layers_count") or sample.get("geometryType"))
    note = "ok" if ok else "unexpected_json_shape"
    return ok, note, sample

def test_minimal_query(service_or_layer_url: str, timeout=10):
    """
    Test a minimal query that returns one feature. Try ArcGIS JSON then GeoJSON.
    Return (ok, note, sample_status_code)
    """
    base = service_or_layer_url.rstrip("/")
    # if the URL ends with /MapServer or /FeatureServer (service root), prefer a concrete layer id if possible
    if base.lower().endswith("/mapserver") or base.lower().endswith("/featureserver"):
        # try to probe and pick first layer id
        ok, note, meta = probe_metadata(base)
        if ok and meta and meta.get("layers_count"):
            # try first layer id by probing the service root JSON
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
    # try ArcGIS JSON
    q1 = base + "/query?where=1=1&outFields=*&resultRecordCount=1&f=json"
    try:
        r1 = requests.get(q1, headers={"User-Agent":"Mozilla/5.0"}, timeout=timeout)
        if r1.status_code == 200:
            # if response is JSON and not an error payload, accept
            try:
                j1 = r1.json()
                if isinstance(j1, dict) and "error" not in j1:
                    return True, "arcgis_json_ok", r1.status_code
            except Exception:
                pass
    except Exception:
        pass
    # try GeoJSON
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

def main(viewer_url: str, pause: float = 4.0):
    out = []
    debug = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-features=IsolateOrigins,site-per-process"])
        context = browser.new_context()
        page = context.new_page()
        captured_requests = []

        def on_request(req):
            # store minimal request info for later cURL reconstruction
            try:
                captured_requests.append(req)
            except Exception:
                pass

        def on_response(resp):
            # no-op here; we'll inspect requests later via captured_requests and fetch response details via Playwright API
            pass

        page.on("request", on_request)
        page.on("response", on_response)

        # normalize viewer_url
        if viewer_url.startswith("//"):
            viewer_url = "https:" + viewer_url
        if not urllib.parse.urlparse(viewer_url).scheme:
            viewer_url = "https://" + viewer_url

        print("Opening viewer:", viewer_url)
        page.goto(viewer_url, timeout=60000)
        time.sleep(pause)
        # try to trigger lazy loads
        try:
            page.mouse.wheel(0, 1000)
        except Exception:
            pass
        time.sleep(1.0)

        # iterate captured requests and inspect responses where possible
        seen = set()
        for req in captured_requests:
            try:
                url = req.url
                u0 = url.split("?")[0]
                if u0 in seen:
                    continue
                seen.add(u0)
                if not looks_like_arcgis(u0):
                    continue
                # attempt to get the response object for this request
                try:
                    resp = req.response()
                except Exception:
                    resp = None
                status = None
                ctype = ""
                body_sample = None
                if resp:
                    try:
                        status = resp.status
                    except Exception:
                        status = None
                    try:
                        ctype = resp.headers.get("content-type", "")
                    except Exception:
                        ctype = ""
                    # avoid reading large binary bodies; only attempt JSON if content-type indicates JSON
                    if "json" in ctype or "javascript" in ctype:
                        try:
                            body_sample = resp.text()[:2000]
                        except Exception:
                            body_sample = None
                curl = build_curl_from_request(req)
                # derive a candidate root (strip /query if present)
                candidate_root = derive_service_root_from_query(url)
                # probe metadata on the candidate root
                probe_ok, probe_note, metadata_sample = probe_metadata(candidate_root)
                # if probe failed and candidate_root ends with /FeatureServer/<id> or /MapServer/<id>, try the root without id
                if not probe_ok and ("/featureserver/" in candidate_root.lower() or "/mapserver/" in candidate_root.lower()):
                    # try the service root (strip trailing id)
                    parts = candidate_root.split("/")
                    if parts and parts[-1].isdigit():
                        service_root = "/".join(parts[:-1])
                        probe_ok2, probe_note2, metadata_sample2 = probe_metadata(service_root)
                        if probe_ok2:
                            probe_ok, probe_note, metadata_sample = probe_ok2, probe_note2, metadata_sample2
                # test minimal query on the candidate root or expanded layer
                query_ok, query_note, query_status = test_minimal_query(candidate_root)
                row = {
                    "url": url,
                    "status": status,
                    "content_type": ctype,
                    "curl": curl,
                    "candidate_root": candidate_root,
                    "probe_ok": probe_ok,
                    "probe_note": probe_note,
                    "metadata_sample": metadata_sample,
                    "query_ok": query_ok,
                    "query_note": query_note,
                    "query_status": query_status,
                    "body_sample": (body_sample[:500] if isinstance(body_sample, str) else None),
                }
                out.append(row)
                debug.append(row)
                print("Captured candidate:", candidate_root, "probe:", probe_note, "query:", query_note)
            except Exception as e:
                # continue on errors
                debug.append({"error": str(e), "request_url": getattr(req, "url", None)})
                continue

        # write outputs
        # CSV
        import csv
        with CSV_OUT.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "url", "status", "content_type", "candidate_root", "probe_ok", "probe_note",
                "query_ok", "query_note", "query_status", "curl"
            ])
            writer.writeheader()
            for r in out:
                writer.writerow({
                    "url": r.get("url"),
                    "status": r.get("status"),
                    "content_type": r.get("content_type"),
                    "candidate_root": r.get("candidate_root"),
                    "probe_ok": r.get("probe_ok"),
                    "probe_note": r.get("probe_note"),
                    "query_ok": r.get("query_ok"),
                    "query_note": r.get("query_note"),
                    "query_status": r.get("query_status"),
                    "curl": r.get("curl"),
                })
        with JSON_OUT.open("w", encoding="utf-8") as f:
            json.dump(debug, f, indent=2, ensure_ascii=False)

        print("Wrote", CSV_OUT, "and", JSON_OUT)
        try:
            page.close()
            context.close()
        except Exception:
            pass
        browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("viewer_url", help="Viewer URL to open (headful)")
    parser.add_argument("--pause", type=float, default=4.0, help="Seconds to wait after page load")
    args = parser.parse_args()
    main(args.viewer_url, pause=args.pause)
