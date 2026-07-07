import requests
from bs4 import BeautifulSoup
import json
import re
import time

# Free search engines
DUCKDUCKGO_SEARCH = "https://duckduckgo.com/html/"
BRAVE_SEARCH = "https://api.search.brave.com/res/v1/web/search"

# Optional Brave API key (free tier available)
BRAVE_API_KEY = None  # "your_key_here"

COUNTIES = [
    "Wayne County Michigan",
    "Monroe County Michigan",
    "Washtenaw County Michigan",
    "Oakland County Michigan",
    "Macomb County Michigan"
]

GIS_KEYWORDS = [
    "parcel viewer",
    "GIS",
    "mapping",
    "property search",
    "ArcGIS",
    "REST services",
    "Beacon",
    "MapGeo",
    "BS&A",
    "Land Records"
]

def duckduckgo_search(query):
    """Free DuckDuckGo HTML search."""
    try:
        params = {"q": query}
        r = requests.get(DUCKDUCKGO_SEARCH, params=params, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        links = []

        for a in soup.find_all("a", class_="result__a"):
            href = a.get("href")
            if href:
                links.append(href)

        return links
    except Exception as e:
        print("DuckDuckGo error:", e)
        return []

def brave_search(query):
    """Optional Brave Search API (free tier)."""
    if not BRAVE_API_KEY:
        return []

    try:
        headers = {"X-Subscription-Token": BRAVE_API_KEY}
        params = {"q": query, "count": 20}
        r = requests.get(BRAVE_SEARCH, headers=headers, params=params, timeout=10)
        data = r.json()

        links = []
        for item in data.get("web", {}).get("results", []):
            links.append(item.get("url"))

        return links
    except Exception as e:
        print("Brave error:", e)
        return []

def is_gis_like(url):
    """Heuristic filter for GIS/parcel viewer URLs."""
    patterns = [
        r"arcgis",
        r"mapserver",
        r"featureserver",
        r"parcel",
        r"gis",
        r"property",
        r"landrecords",
        r"beacon",
        r"mapgeo",
        r"bsaonline"
    ]
    return any(re.search(p, url.lower()) for p in patterns)

def probe_arcgis(url):
    """Check if URL is an ArcGIS REST endpoint."""
    try:
        r = requests.get(url, timeout=5)
        if "ArcGIS" in r.text or "MapServer" in r.text or "FeatureServer" in r.text:
            return True
    except:
        pass
    return False

def search_gis_for_county(county):
    query = f"{county} " + " ".join(GIS_KEYWORDS)
    print(f"\n=== Searching GIS for {county} ===")
    print("Query:", query)

    # 1. DuckDuckGo (free)
    ddg_results = duckduckgo_search(query)

    # 2. Brave (optional)
    brave_results = brave_search(query)

    all_results = ddg_results + brave_results

    # 3. Filter GIS-like URLs
    gis_candidates = [u for u in all_results if is_gis_like(u)]

    print(f"Found {len(gis_candidates)} GIS-like URLs:")
    for u in gis_candidates:
        print("  -", u)

    # 4. Probe ArcGIS REST endpoints
    arcgis_hits = []
    for u in gis_candidates:
        if probe_arcgis(u):
            arcgis_hits.append(u)

    if arcgis_hits:
        print("\nArcGIS REST endpoints detected:")
        for u in arcgis_hits:
            print("  -", u)

    return {
        "county": county,
        "results": gis_candidates,
        "arcgis": arcgis_hits
    }

def main():
    final = {}
    for county in COUNTIES:
        time.sleep(1)
        final[county] = search_gis_for_county(county)

    print("\n\n=== FINAL RESULTS ===")
    print(json.dumps(final, indent=2))

if __name__ == "__main__":
    main()
