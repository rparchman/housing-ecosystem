# tools/extract_mapserver_with_seleniumwire.py
"""
Load each manifest source.url in a real browser, capture XHRs, extract ArcGIS REST/MapServer endpoints,
and update manifests/<County>.yaml layers[0].file when found.

Usage:
  .venv\Scripts\python.exe tools/extract_mapserver_with_seleniumwire.py --limit 20 --pause 2.0

Notes:
  - Runs a visible Chrome instance to avoid some bot blocks.
  - Writes data/county_mapserver_extracted.csv and updates manifests/*.yaml.
"""
import time, argparse, re, csv, urllib.parse
from pathlib import Path
import yaml
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

ROOT = Path.cwd()
MANIFESTS = ROOT / "manifests"
OUT_CSV = ROOT / "data" / "county_mapserver_extracted.csv"
KEY_PATTERNS = [r"/rest/services", r"/MapServer", r"arcgis.com"]

def find_candidate_from_requests(requests_list):
    seen = []
    for req in requests_list:
        try:
            url = req.url
        except Exception:
            continue
        for p in KEY_PATTERNS:
            if re.search(p, url, flags=re.IGNORECASE):
                # normalize
                u = url.split("?")[0]
                if u not in seen:
                    seen.append(u)
    return seen

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

def main(limit=0, pause=2.0, headless=False):
    manifests = sorted(MANIFESTS.glob("*.yaml"))
    if limit and limit>0:
        manifests = manifests[:limit]
    # Chrome options
    chrome_opts = Options()
    if headless:
        chrome_opts.add_argument("--headless=new")
    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")
    chrome_opts.add_argument("--window-size=1600,1000")
    # start webdriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_opts)
    results = []
    for i, m in enumerate(manifests, start=1):
        county = m.stem.replace("_"," ")
        data = yaml.safe_load(m.read_text(encoding="utf-8")) or {}
        src = (data.get("source") or {}).get("url","") or ""
        print(f"[{i}/{len(manifests)}] {county} -> {src}")
        if not src:
            results.append({"county":county,"source_url":"","candidate":"","notes":"no_source"})
            continue
        try:
            # clear previous requests
            driver.requests.clear()
            # ensure scheme
            if src.startswith("//"):
                src = "https:" + src
            if not urllib.parse.urlparse(src).scheme:
                src = "https://" + src
            driver.get(src)
            # wait for XHRs to load
            time.sleep(pause)
            # optionally scroll to trigger lazy loads
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.0)
            reqs = driver.requests
            candidates = find_candidate_from_requests(reqs)
            candidate = candidates[0] if candidates else ""
            print("  found candidate:", candidate)
            update_manifest(county, src, candidate)
            notes = "found" if candidate else "none"
            results.append({"county":county,"source_url":src,"candidate":candidate,"notes":notes})
        except Exception as e:
            print("  error:", e)
            results.append({"county":county,"source_url":src,"candidate":"","notes":f"error:{e}"})
        time.sleep(1.0)
    driver.quit()
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["county","source_url","candidate","notes"])
        w.writeheader()
        w.writerows(results)
    print("Wrote", OUT_CSV)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--pause", type=float, default=2.0)
    p.add_argument("--headless", action="store_true")
    args = p.parse_args()
    main(limit=args.limit, pause=args.pause, headless=args.headless)
