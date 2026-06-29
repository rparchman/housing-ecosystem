import httpx
from bs4 import BeautifulSoup

def run_scraper_sample():
    url = "https://example-county-records.gov/sample-listings"
    resp = httpx.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for el in soup.select(".listing"):
        results.append({
            "source_id": el.get("data-id"),
            "address": el.select_one(".address").get_text(strip=True),
            "raw": str(el)
        })
    return results
