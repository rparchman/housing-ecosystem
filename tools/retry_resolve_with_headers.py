# tools/retry_resolve_with_headers.py
import csv, time, urllib.parse
from pathlib import Path
import requests

IN = Path("data/county_gis_candidates.csv")
OUT = Path("data/county_gis_candidates_retry.csv")
HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
  "Accept-Language": "en-US,en;q=0.9",
  "Referer": "https://www.bing.com/",
  "Connection": "keep-alive"
}
TIMEOUT = 20
PAUSE = 1.5

def decode_wrapper(url):
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        if "uddg" in qs:
            return urllib.parse.unquote(qs["uddg"][0])
        if "u" in qs:
            return urllib.parse.unquote(qs["u"][0])
    except Exception:
        pass
    return url

def follow(url):
    if not url:
        return ""
    if url.startswith("//"):
        url = "https:" + url
    if not urllib.parse.urlparse(url).scheme:
        url = "https://" + url
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        return r.status_code, r.url
    except Exception as e:
        return None, str(e)

def main():
    if not IN.exists():
        print("Input not found:", IN); return
    rows = []
    with IN.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            county = r["county"]
            cand = (r.get("candidate_url") or "").strip()
            decoded = decode_wrapper(cand)
            status, final = follow(decoded)
            print(county, "->", status, final)
            rows.append({"county": county, "original": cand, "decoded": decoded, "status": status or "", "final": final})
            time.sleep(PAUSE)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["county","original","decoded","status","final"])
        w.writeheader()
        w.writerows(rows)
    print("Wrote", OUT)

if __name__ == "__main__":
    main()
