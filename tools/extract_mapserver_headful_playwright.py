# tools/extract_mapserver_headful_playwright.py
"""
Headful Playwright extractor with blocked/forbidden filtering

Usage:
  .venv\Scripts\python.exe tools/extract_mapserver_headful_playwright.py --limit 20 --pause 3.0 --csv data/county_mapserver_playwright_headful.csv
"""
import time
import re
import csv
import argparse
import urllib.parse
from pathlib import Path
import requests
import yaml
from playwright.sync_api import sync_playwright

ROOT = Path.cwd()
MANIFESTS = ROOT / "manifests"
OUT_CSV = ROOT / "data" / "county_mapserver_playwright_headful.csv"
KEY_PATTERNS = [r"/rest/services", r"/MapServer", r"arcgis.com"]

# patterns to accept/reject candidates
SERVICE_LIKE = re.compile(r"/(?:rest/services|MapServer)(?:/|$)", flags=re.IGNORECASE)
REJECT_PATTERNS = re.compile(
    r"\.(?:png|jpg|jpeg|svg|gif|ico|css|js|woff2?|ttf)$|/widgets/|/images/|/tile/|/tiles/|/tilemap/|/static/|/icons/|/resources/",
    flags=re.IGNORECASE,
)

def find_candidates(urls):
    """Return unique candidate URLs matching KEY_PATTERNS (strip query string)."""
    seen = []
    for u in urls:
        try:
            u0 = u.split("?")[0]
        except Exception:
            continue
        for p in KEY_PATTERNS:
            if re.search(p, u0, flags=re.IGNORECASE):
                if u0 not in seen:
                    seen.append(u0)
    return seen

def filter_candidates(raw_urls):
    """Keep only service-like URLs and reject static assets and tiles."""
    seen = []
    for u in raw_urls:
        u0 = u.split("?")[0]
        if REJECT_PATTERNS.search(u0):
            continue
        if SERVICE_LIKE.search(u0):
            if u0 not in seen:
                seen.append(u0)
    return seen

def probe_candidate(candidate, timeout=8):
    """
    Probe candidate by requesting candidate?f=json.
    Return (True, reason) if probe looks usable.
    """
    try:
        probe_url = candidate if candidate.lower().endswith("?f=json") else candidate.rstrip("/") + "?f=json"
        r = requests.get(probe_url, headers={"User-Agent":"Mozilla/5.0"}, timeout=timeout, stream=True)
        ctype = r.headers.get("Content-Type", "")
        if r.status_code != 200:
            return False, f"probe_status:{r.status_code}"
        if "application/json" not in ctype and "text/javascript" not in ctype and "application/geo+json" not in ctype:
            return False, f"non_json_content_type:{ctype}"
        j = r.json()
        if isinstance(j, dict) and "error" in j:
            return False, "probe_error_payload"
        lower = candidate.lower()
        if any(x in lower for x in ("imageserver", "wmsserver", "wmts")):
            return False, "unsupported_service_type"
        if isinstance(j, dict) and ("fields" in j or "layers" in j or "geometryType" in j or "capabilities" in j):
            return True, "ok"
        return False, "unexpected_json"
    except ValueError as ve:
        return False, f"json_parse_error:{ve}"
    except Exception as e:
        return False, f"probe_exception:{e}"

def expand_service_root(root_url, timeout=6):
    """
    If root_url is a service root (MapServer), try to pick a concrete layer id.
    Prefer layers whose name contains parcel/property/tax/apn/pin.
    """
    try:
        probe_url = root_url.rstrip("/") + "?f=json"
        r = requests.get(probe_url, headers={"User-Agent":"Mozilla/5.0"}, timeout=timeout)
        if r.status_code != 200:
            return None
        j = r.json()
        layers = j.get("layers") or []
        if not layers:
            return None
        for layer in layers:
            name = (layer.get("name") or "").lower()
            lid = layer.get("id")
            if lid is None:
                continue
            if any(k in name for k in ("parcel", "tax", "property", "apn", "pin")):
                return root_url.rstrip("/") + f"/{lid}"
        first = layers[0].get("id")
        if first is not None:
            return root_url.rstrip("/") + f"/{first}"
    except Exception:
        return None
    return None

def update_manifest(county, src, candidate):
    fname = MANIFESTS / (county.replace(" ", "_") + ".yaml")
    if fname.exists():
        m = yaml.safe_load(fname.read_text(encoding="utf-8")) or {}
    else:
        m = {"county": f"{county}, MI", "source": {"url": src}, "layers": [{"name":"parcels","file":"","parcel_id_field":""}]}
    m.setdefault("source", {})
    m["source"]["url"] = src or m["source"].get("url","")
    m.setdefault("layers", [{"name":"parcels","file":"","parcel_id_field":""}])
    if candidate:
        m["layers"][0]["file"] = candidate
        m["layers"][0]["format"] = "arcgis-rest"
    fname.write_text(yaml.safe_dump(m, sort_keys=False, allow_unicode=True), encoding="utf-8")

def main(limit=0, pause=3.0, headless=False, csv_out=str(OUT_CSV)):
    manifests = sorted(MANIFESTS.glob("*.yaml"))
    if limit and limit > 0:
        manifests = manifests[:limit]
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=["--disable-features=IsolateOrigins,site-per-process"])
        for i, m in enumerate(manifests, start=1):
            county = m.stem.replace("_", " ")
            data = yaml.safe_load(m.read_text(encoding="utf-8")) or {}
            src = (data.get("source") or {}).get("url", "") or ""
            print(f"[{i}/{len(manifests)}] {county} -> {src}")
            if not src:
                results.append({"county": county, "source_url": "", "candidate": "", "notes": "no_source"})
                continue

            if src.startswith("//"):
                src = "https:" + src
            if not urllib.parse.urlparse(src).scheme:
                src = "https://" + src

            captured_urls = []
            responses = {}       # url_without_query -> (status, content_type)
            blocked_hosts = set()

            try:
                context = browser.new_context()
                page = context.new_page()

                def _on_request(req):
                    try:
                        captured_urls.append(req.url)
                    except Exception:
                        pass

                def _on_response(resp):
                    try:
                        u = resp.url.split("?")[0]
                        status = resp.status
                        ctype = ""
                        try:
                            ctype = resp.headers.get("content-type", "")
                        except Exception:
                            ctype = ""
                        responses[u] = (status, ctype)
                        if status in (401, 403, 404, 410, 451) or (500 <= status < 600):
                            blocked_hosts.add(u)
                    except Exception:
                        pass

                page.on("request", _on_request)
                page.on("response", _on_response)

                page.goto(src, timeout=60000)
                time.sleep(pause)

                # try to trigger lazy loads / interactions
                try:
                    page.mouse.wheel(0, 1000)
                except Exception:
                    pass
                time.sleep(1.0)

                raw_candidates = find_candidates(captured_urls)
                filtered_candidates = [c for c in filter_candidates(raw_candidates) if c not in blocked_hosts]

                verified = []
                for c in filtered_candidates:
                    # skip obvious tile endpoints
                    if re.search(r"/(?:/tile/|/tilemap/|/tiles/|/MapServer/tile)", c, flags=re.IGNORECASE):
                        print(f"    skipping tile endpoint {c}")
                        continue

                    # if candidate is a service root, try to expand to a concrete layer
                    c_probe = c
                    if c.rstrip("/").lower().endswith("/mapserver"):
                        expanded = expand_service_root(c)
                        if expanded:
                            c_probe = expanded

                    ok, reason = probe_candidate(c_probe)
                    if ok:
                        verified.append(c_probe)
                    else:
                        print(f"    probe rejected {c_probe} ({reason})")

                candidate = verified[0] if verified else ""
                print("  found candidate:", candidate or "(none)")

                update_manifest(county, src, candidate)
                notes = "found" if candidate else ("blocked" if blocked_hosts else "none")
                results.append({"county": county, "source_url": src, "candidate": candidate, "notes": notes})

            except Exception as e:
                print("  error:", e)
                results.append({"county": county, "source_url": src, "candidate": "", "notes": f"error:{e}"})
            finally:
                try:
                    page.close()
                    context.close()
                except Exception:
                    pass
                time.sleep(1.0)

        browser.close()

    outp = Path(csv_out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["county", "source_url", "candidate", "notes"])
        w.writeheader()
        w.writerows(results)
    print("Wrote", outp)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--pause", type=float, default=3.0)
    p.add_argument("--headless", action="store_true")
    p.add_argument("--csv", type=str, default=str(OUT_CSV))
    args = p.parse_args()
    main(limit=args.limit, pause=args.pause, headless=args.headless, csv_out=args.csv)
