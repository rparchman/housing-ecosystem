# tools/resolve_bing_redirects.py
"""
Resolve Bing redirect URLs in data/county_gis_links.csv and update manifests/*.yaml.
Usage:
  .venv\\Scripts\\python.exe tools\\resolve_bing_redirects.py
Requires:
  pip install requests pyyaml
"""
import csv, base64, urllib.parse, time
from pathlib import Path
import requests, yaml

ROOT = Path.cwd()
CSV = ROOT / "data" / "county_gis_links.csv"
MANIFESTS = ROOT / "manifests"
HEADERS = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
SLEEP = 0.5

def decode_u_param(url):
    q = urllib.parse.urlparse(url).query
    qs = urllib.parse.parse_qs(q)
    if "u" in qs:
        val = qs["u"][0]
        # try base64 decode (some values are base64-like)
        try:
            # some values have extra prefix; strip non-base64 prefix
            # find first 'aHR0' which is base64 for 'http'
            idx = val.find("aHR0")
            candidate = val[idx:] if idx != -1 else val
            decoded = base64.b64decode(candidate + "===").decode("utf-8", errors="ignore")
            if decoded.startswith("http"):
                return decoded
        except Exception:
            pass
        # fallback: URL-decode
        try:
            return urllib.parse.unquote(val)
        except Exception:
            return None
    return None

def follow_redirect(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        return r.url
    except Exception:
        return None

def main():
    if not CSV.exists():
        print("CSV not found:", CSV); return
    rows = []
    with CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    updated = []
    for r in rows:
        county = r["county"]
        candidate = r.get("candidate_url","").strip()
        resolved = ""
        if candidate:
            resolved = decode_u_param(candidate) or ""
            if not resolved:
                resolved = follow_redirect(candidate) or ""
            print(county, "->", resolved or "(unresolved)")
            # update manifest if exists
            mf = MANIFESTS / (county.replace(" ", "_") + ".yaml")
            if mf.exists():
                try:
                    m = yaml.safe_load(mf.read_text(encoding="utf-8")) or {}
                    if "source" not in m:
                        m["source"] = {}
                    m["source"]["url"] = resolved
                    mf.write_text(yaml.safe_dump(m, sort_keys=False, allow_unicode=True), encoding="utf-8")
                except Exception as e:
                    print("  manifest update failed for", county, e)
            time.sleep(SLEEP)
        updated.append((county, resolved, r.get("title","")))
    # write resolved CSV
    out = CSV.with_suffix(".resolved.csv")
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["county","resolved_url","title"])
        w.writerows(updated)
    print("Wrote resolved CSV:", out)

if __name__ == "__main__":
    main()
