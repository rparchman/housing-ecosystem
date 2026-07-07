#!/usr/bin/env python3
"""
tools/discover_and_confirm_parcels.py

Usage:
  .venv\Scripts\python.exe tools/discover_and_confirm_parcels.py --input manifests_list.txt --pause 8 --limit 50

Outputs:
  - data/discovered_parcels.csv
  - data/discovered_parcels_debug.json

Optional AI confirmation:
  - Set AI_PROVIDER to "openai" or "azure"
  - For OpenAI: set OPENAI_API_KEY
  - For Azure: set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY and AZURE_DEPLOYMENT_NAME

Notes:
  - Run headful (no --headless) for interactive viewers that lazy-load layers.
  - Increase --pause for slow pages or Experience Builder apps.
"""
import os
import re
import csv
import json
import time
import socket
import zipfile
import io
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any

import requests
from playwright.sync_api import sync_playwright

ROOT = Path.cwd()
OUT_DIR = ROOT / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CSV_OUT = OUT_DIR / "discovered_parcels.csv"
DEBUG_OUT = OUT_DIR / "discovered_parcels_debug.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ParcelScanner/1.0)"}

# Regexes to detect candidate endpoints
ARC_RE = re.compile(r"/(?:rest/services|MapServer|FeatureServer)", re.IGNORECASE)
WFS_RE = re.compile(r"\bservice=wfs\b|\bWFS\b", re.IGNORECASE)
GEOJSON_RE = re.compile(r"\.geojson$|/geojson\b", re.IGNORECASE)
KML_RE = re.compile(r"\.kml$|/kml\b", re.IGNORECASE)
ZIP_RE = re.compile(r"\.zip$", re.IGNORECASE)
PARCEL_FIELD_KEYWORDS = ("APN", "PARCEL", "PIN", "PARID", "PARCEL_NO", "PARCELID", "PARCEL_NUM")

# AI configuration (optional)
AI_PROVIDER = os.environ.get("AI_PROVIDER", "").lower()  # "openai" or "azure" or ""
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
AZURE_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_KEY = os.environ.get("AZURE_OPENAI_KEY")
AZURE_DEPLOYMENT = os.environ.get("AZURE_DEPLOYMENT_NAME", "gpt-deploy")

def is_resolvable(hostname: str) -> bool:
    try:
        socket.gethostbyname(hostname)
        return True
    except Exception:
        return False

def normalize_url(u: str) -> str:
    if not u:
        return u
    u = u.strip()
    if u.startswith("//"):
        u = "https:" + u
    if not urllib.parse.urlparse(u).scheme:
        u = "https://" + u
    return u

def derive_service_root(url: str) -> str:
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

def probe_arcgis_json(url: str, timeout=8):
    probe = url.rstrip("/") + "?f=json"
    try:
        r = requests.get(probe, headers=HEADERS, timeout=timeout)
    except Exception as e:
        return False, f"request_exception:{e}", None
    if r.status_code != 200:
        return False, f"status:{r.status_code}", None
    try:
        j = r.json()
    except Exception as e:
        return False, f"json_parse_error:{e}", None
    if isinstance(j, dict) and "error" in j:
        return False, "arcgis_error_payload", j
    meta = {}
    if isinstance(j, dict):
        if "fields" in j and isinstance(j["fields"], list):
            meta["fields"] = [f.get("name", "") for f in j["fields"]]
            meta["parcel_field_candidates"] = [n for n in meta["fields"] if any(k in n.upper() for k in PARCEL_FIELD_KEYWORDS)]
        if "geometryType" in j:
            meta["geometryType"] = j["geometryType"]
        if "layers" in j:
            meta["layers"] = [l.get("name") for l in j.get("layers", [])]
    ok = bool(meta.get("fields") or meta.get("geometryType") or meta.get("layers"))
    return ok, "ok" if ok else "unexpected_json_shape", meta

def test_arcgis_query(layer_url: str, timeout=10):
    q = layer_url.rstrip("/") + "/query?where=1=1&outFields=*&resultRecordCount=1&f=json"
    try:
        r = requests.get(q, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            try:
                j = r.json()
                if isinstance(j, dict) and "error" not in j:
                    return True, "arcgis_json_ok", j
            except Exception:
                pass
    except Exception:
        pass
    return False, "no_query_result", None

def try_download_sample(url: str, timeout=12):
    try:
        r = requests.get(url, headers=HEADERS, stream=True, timeout=timeout)
    except Exception as e:
        return False, f"download_error:{e}", None
    if r.status_code != 200:
        return False, f"status:{r.status_code}", None
    ctype = r.headers.get("Content-Type", "")
    if "zip" in ctype or ZIP_RE.search(url):
        try:
            data = r.content
            z = zipfile.ZipFile(io.BytesIO(data))
            names = z.namelist()
            return True, "zip_ok", {"files": names}
        except Exception as e:
            return False, f"zip_error:{e}", None
    if "json" in ctype or GEOJSON_RE.search(url):
        try:
            j = r.json()
            return True, "json_ok", {"sample": j if isinstance(j, dict) else str(j)[:2000]}
        except Exception as e:
            return False, f"json_parse_error:{e}", None
    try:
        txt = r.text[:2000]
        return True, "text_ok", {"sample": txt}
    except Exception:
        return False, "no_preview", None

def build_curl_from_req(req) -> str:
    try:
        method = req.method
        url = req.url
        headers = req.headers
        header_parts = []
        for k, v in headers.items():
            header_parts.append(f"-H '{k}: {v}'")
        body = ""
        try:
            post = req.post_data
            if post:
                body = f"--data '{post}'"
        except Exception:
            body = ""
        curl = f"curl -X {method} " + " ".join(header_parts) + f" '{url}' " + body
        return curl
    except Exception:
        return ""

def confirm_with_copilot(candidate_url: str, viewer_url: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Confirm and correct candidate_url using an AI assistant if configured.
    Returns a dict: {confirmed_url, confidence_note, suggestion}
    If AI not configured, returns empty dict.
    """
    if AI_PROVIDER not in ("openai", "azure"):
        return {}
    prompt = (
        "You are an assistant that helps confirm public GIS/parcel endpoints.\n"
        f"Viewer page: {viewer_url}\n"
        f"Candidate endpoint: {candidate_url}\n"
        "Tasks:\n"
        "1) Confirm whether the candidate endpoint looks like a valid public GIS endpoint (MapServer/FeatureServer/WFS/GeoJSON/KML/ZIP).\n"
        "2) If the path looks truncated or contains query tokens, suggest a corrected canonical URL (service root or layer URL) that is likely to be stable.\n"
        "3) If the endpoint likely requires a token or referrer, say so and explain what evidence indicates that.\n"
        "Answer in JSON with keys: confirmed_url, confidence_note, suggestion.\n"
    )
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperature": 0.0,
    }
    try:
        if AI_PROVIDER == "openai" and OPENAI_API_KEY:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
            r = requests.post(url, headers=headers, json=payload, timeout=15)
            r.raise_for_status()
            j = r.json()
            text = j["choices"][0]["message"]["content"]
        elif AI_PROVIDER == "azure" and AZURE_ENDPOINT and AZURE_KEY:
            url = AZURE_ENDPOINT.rstrip("/") + f"/openai/deployments/{AZURE_DEPLOYMENT}/chat/completions?api-version=2023-10-01"
            headers = {"api-key": AZURE_KEY, "Content-Type": "application/json"}
            r = requests.post(url, headers=headers, json=payload, timeout=15)
            r.raise_for_status()
            j = r.json()
            text = j["choices"][0]["message"]["content"]
        else:
            return {}
        # Try to parse JSON from assistant; fallback to raw text
        try:
            parsed = json.loads(text)
            return parsed
        except Exception:
            return {"confirmed_url": candidate_url, "confidence_note": "ai_response_text", "suggestion": text}
    except Exception as e:
        return {"error": f"ai_call_failed:{e}"}

def scan_viewer(viewer_url: str, pause: float = 8.0, headless: bool = False):
    viewer_url = normalize_url(viewer_url)
    parsed = urllib.parse.urlparse(viewer_url)
    host = parsed.hostname or ""
    if not host or not is_resolvable(host):
        return {"viewer_url": viewer_url, "status": "unresolved_host"}, []

    results = []
    debug_rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=["--disable-features=IsolateOrigins,site-per-process"])
        context = browser.new_context()
        page = context.new_page()
        captured = []

        def on_request(req):
            captured.append(req)

        page.on("request", on_request)

        try:
            page.goto(viewer_url, timeout=180000)
        except Exception as e:
            browser.close()
            return {"viewer_url": viewer_url, "status": f"navigation_failed:{e}"}, []

        time.sleep(pause)
        # try UI interactions to trigger lazy loads
        selectors = [
            "button[title*='Layers']",
            "button[title*='Contents']",
            "button[title*='Legend']",
            "button[aria-label*='Layers']",
            "a:has-text('Layers')",
            ".esri-layer-list__toggle",
            ".toc-toggle",
            ".layers-toggle",
        ]
        for sel in selectors:
            try:
                els = page.query_selector_all(sel)
                for el in els[:3]:
                    try:
                        el.click(timeout=2000)
                        time.sleep(0.6)
                    except Exception:
                        pass
            except Exception:
                pass
        page.mouse.wheel(0, 800)
        time.sleep(2.0)

        seen = set()
        for req in captured:
            try:
                url = req.url
                base = url.split("?")[0]
                if base in seen:
                    continue
                seen.add(base)
                # quick candidate filter
                if not (ARC_RE.search(url) or WFS_RE.search(url) or GEOJSON_RE.search(url) or KML_RE.search(url) or ZIP_RE.search(url)):
                    continue
                curl = build_curl_from_req(req)
                candidate_root = derive_service_root(url)
                row = {"url": url, "candidate_root": candidate_root, "curl": curl}
                # probe types
                if ARC_RE.search(candidate_root):
                    ok, note, meta = probe_arcgis_json(candidate_root)
                    q_ok, q_note, q_meta = test_arcgis_query(candidate_root)
                    row.update({"type": "arcgis", "probe_ok": ok, "probe_note": note, "meta": meta, "query_ok": q_ok, "query_note": q_note})
                elif WFS_RE.search(url):
                    # simple WFS probe
                    caps = candidate_root + "?service=WFS&request=GetCapabilities"
                    try:
                        r = requests.get(caps, headers=HEADERS, timeout=8)
                        ok = r.status_code == 200 and ("WFS_Capabilities" in r.text or "wfs:WFS_Capabilities" in r.text)
                        row.update({"type": "wfs", "probe_ok": ok, "probe_note": "wfs_caps_ok" if ok else "no_wfs_caps", "meta": {"sample": r.text[:1000] if r.status_code==200 else ""}})
                    except Exception as e:
                        row.update({"type": "wfs", "probe_ok": False, "probe_note": f"request_exception:{e}"})
                else:
                    ok, note, meta = try_download_sample(url)
                    row.update({"type": "direct", "probe_ok": ok, "probe_note": note, "meta": meta})
                # AI confirmation step (optional)
                ai_result = confirm_with_copilot(candidate_root, viewer_url)
                if ai_result:
                    row["ai_confirmation"] = ai_result
                results.append(row)
                debug_rows.append(row)
            except Exception as e:
                debug_rows.append({"error": str(e), "request_url": getattr(req, "url", None)})
                continue

        try:
            page.close()
            context.close()
        except Exception:
            pass
        browser.close()

    return {"viewer_url": viewer_url, "status": "scanned", "candidates": len(results)}, debug_rows

def main(input_file: str, pause: float, limit: int, headless: bool):
    p = Path(input_file)
    if not p.exists():
        print("Input file not found:", input_file)
        return
    lines = [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and not l.strip().startswith("#")]
    to_scan = lines[:limit] if limit and limit > 0 else lines

    out_rows = []
    debug_all = []

    for url in to_scan:
        summary, debug_rows = scan_viewer(url, pause=pause, headless=headless)
        debug_all.extend(debug_rows)
        # choose best candidate heuristically
        chosen = {"viewer_url": url, "candidate": "", "type": "", "probe_note": "none_found", "parcel_fields": []}
        for r in debug_rows:
            if r.get("probe_ok"):
                meta = r.get("meta") or {}
                pf = meta.get("parcel_field_candidates") or []
                if pf:
                    chosen = {"viewer_url": url, "candidate": r.get("candidate_root"), "type": r.get("type"), "probe_note": r.get("probe_note"), "parcel_fields": pf}
                    break
        if chosen["candidate"] == "" and debug_rows:
            for r in debug_rows:
                if r.get("probe_ok"):
                    chosen = {"viewer_url": url, "candidate": r.get("candidate_root"), "type": r.get("type"), "probe_note": r.get("probe_note"), "parcel_fields": (r.get("meta") or {}).get("parcel_field_candidates", [])}
                    break
        out_rows.append(chosen)

    # write CSV and debug JSON
    with CSV_OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["viewer_url", "candidate", "type", "probe_note", "parcel_fields"])
        w.writeheader()
        for r in out_rows:
            w.writerow(r)
    with DEBUG_OUT.open("w", encoding="utf-8") as f:
        json.dump(debug_all, f, indent=2, ensure_ascii=False)

    print("Wrote", CSV_OUT, "and", DEBUG_OUT)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Text file with one viewer URL per line")
    ap.add_argument("--pause", type=float, default=8.0, help="Seconds to wait after page load")
    ap.add_argument("--limit", type=int, default=0, help="Limit number of viewers (0 = all)")
    ap.add_argument("--headless", action="store_true", help="Run headless (not recommended for interactive viewers)")
    args = ap.parse_args()
    main(args.input, pause=args.pause, limit=args.limit, headless=args.headless)
