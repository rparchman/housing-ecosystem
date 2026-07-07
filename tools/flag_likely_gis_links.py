# tools/flag_likely_gis_links.py
"""
Flag likely GIS/open-data links from data/county_gis_links.resolved.csv.
Usage:
  .venv\\Scripts\\python.exe tools\\flag_likely_gis_links.py
Output:
  - data/county_gis_links.flagged.csv (county,resolved_url,title,likely_gis,reason)
"""
import csv
from pathlib import Path
import urllib.parse

IN = Path("data/county_gis_links.resolved.csv")
OUT = Path("data/county_gis_links.flagged.csv")
KEYWORDS = ["arcgis", "beacon", "qpublic", "parcel", "gis", "maps", "open-data", "opendata", "data", "viewer", "tax", "assessor"]

def score_url(url):
    if not url:
        return False, "empty"
    u = url.lower()
    # strip common wrappers
    try:
        parsed = urllib.parse.urlparse(u)
        net = parsed.netloc
    except Exception:
        net = u
    reasons = []
    for k in KEYWORDS:
        if k in u or k in net:
            reasons.append(k)
    return (len(reasons) > 0), ";".join(reasons) if reasons else "no_keyword"

def main():
    if not IN.exists():
        print("Input CSV not found:", IN); return
    rows = []
    with IN.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            url = (r.get("resolved_url") or "").strip()
            likely, reason = score_url(url)
            r_out = {
                "county": r.get("county",""),
                "resolved_url": url,
                "title": r.get("title",""),
                "likely_gis": "yes" if likely else "no",
                "reason": reason
            }
            rows.append(r_out)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["county","resolved_url","title","likely_gis","reason"])
        w.writeheader()
        w.writerows(rows)
    print("Wrote flagged CSV:", OUT)
    # summary
    yes = sum(1 for r in rows if r["likely_gis"]=="yes")
    print(f"Flagged {yes} of {len(rows)} as likely GIS/open-data links.")

if __name__ == "__main__":
    main()
