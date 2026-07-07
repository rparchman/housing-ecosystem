# tools/probe_epp_api.py
import re
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup

ROOT = "https://public-wclb.epropertyplus.com/"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; probe/1.0)"}
TIMEOUT = 20.0

def fetch_text(url):
    with httpx.Client(timeout=TIMEOUT, follow_redirects=True, headers=HEADERS) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.text, str(r.url)

def find_script_urls(html, base):
    soup = BeautifulSoup(html, "html.parser")
    scripts = []
    for s in soup.select("script[src]"):
        scripts.append(urljoin(base, s["src"]))
    return scripts

def scan_js_for_endpoints(js_text):
    patterns = [
        r'["\'](/[^"\']*api[^"\']*)["\']',
        r'["\'](/[^"\']*search[^"\']*)["\']',
        r'["\'](/[^"\']*parcel[^"\']*)["\']',
        r'fetch\(["\']([^"\']+)["\']',
        r'axios\.get\(["\']([^"\']+)["\']'
    ]
    found = set()
    for p in patterns:
        for m in re.findall(p, js_text, flags=re.IGNORECASE):
            found.add(m)
    return sorted(found)

def main():
    print("Fetching portal root:", ROOT)
    html, final_url = fetch_text(ROOT)
    print("final_url:", final_url)
    scripts = find_script_urls(html, final_url)
    print("Found script URLs:", len(scripts))
    candidates = set()
    for s in scripts:
        try:
            print("Downloading", s)
            js, _ = fetch_text(s)
            for ep in scan_js_for_endpoints(js):
                if ep.startswith("/"):
                    candidates.add(urljoin(final_url, ep))
                else:
                    candidates.add(ep)
        except Exception as e:
            print("Failed to fetch", s, ":", e)
    print("\nCandidate endpoints / fetch calls found:")
    for c in sorted(candidates):
        print(c)
    if not candidates:
        print("\nNo obvious endpoints found. If that happens, copy one listing's OuterHTML from the browser and paste it here.")

if __name__ == "__main__":
    main()
