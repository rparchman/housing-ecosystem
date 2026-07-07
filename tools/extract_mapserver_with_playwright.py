# tools/extract_mapserver_with_playwright.py
from pathlib import Path
import re, time, csv, yaml
from playwright.sync_api import sync_playwright

MANIFESTS = Path("manifests")
OUT_CSV = Path("data/county_mapserver_playwright.csv")
KEY_PATTERNS = [r"/rest/services", r"/MapServer", r"arcgis.com"]

def find_candidates(request_urls):
    seen = []
    for u in request_urls:
        for p in KEY_PATTERNS:
            if re.search(p, u, flags=re.IGNORECASE):
                u_norm = u.split("?")[0]
                if u_norm not in seen:
                    seen.append(u_norm)
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
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        for i, m in enumerate(manifests, start=1):
            county = m.stem.replace("_"," ")
            data = yaml.safe_load(m.read_text(encoding="utf-8")) or {}
            src = (data.get("source") or {}).get("url","") or ""
            print(f"[{i}/{len(manifests)}] {county} -> {src}")
            if not src:
                results.append({"county":county,"source_url":"","candidate":"","notes":"no_source"})
                continue
            context = browser.new_context()
            page = context.new_page()
            urls = []
            def on_request(req):
                try:
                    urls.append(req.url)
                except Exception:
                    pass
            page.on("request", on_request)
            try:
                if src.startswith("//"):
                    src = "https:" + src
                if not src.startswith("http"):
                    src = "https://" + src
                page.goto(src, timeout=60000)
                time.sleep(pause)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.0)
                candidates = find_candidates(urls)
                candidate = candidates[0] if candidates else ""
                print("  found candidate:", candidate)
                update_manifest(county, src, candidate)
                notes = "found" if candidate else "none"
                results.append({"county":county,"source_url":src,"candidate":candidate,"notes":notes})
            except Exception as e:
                print("  error:", e)
                results.append({"county":county,"source_url":src,"candidate":"","notes":f"error:{e}"})
            finally:
                page.close()
                context.close()
        browser.close()
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["county","source_url","candidate","notes"])
        w.writeheader()
        w.writerows(results)
    print("Wrote", OUT_CSV)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--pause", type=float, default=2.0)
    p.add_argument("--headless", action="store_true")
    args = p.parse_args()
    main(limit=args.limit, pause=args.pause, headless=args.headless)
