# tools/test_endpoint.py
import sys, json
import httpx

def main():
    if len(sys.argv) < 2:
        print("Usage: python tools\\test_endpoint.py <URL> [GET|POST] [json_body_as_string]")
        return
    url = sys.argv[1]
    method = (sys.argv[2].upper() if len(sys.argv) >= 3 else "GET")
    body = None
    if len(sys.argv) >= 4:
        try:
            body = json.loads(sys.argv[3])
        except Exception:
            body = sys.argv[3]

    headers = {"User-Agent":"Mozilla/5.0 (compatible; probe/1.0)"}
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=headers) as c:
            if method == "POST":
                if isinstance(body, dict):
                    r = c.post(url, json=body)
                else:
                    r = c.post(url, data=body)
            else:
                r = c.get(url, params=body if isinstance(body, dict) else None)
            print("URL:", r.url)
            print("Status:", r.status_code)
            print("Content-Type:", r.headers.get("content-type"))
            text = r.text
            print("\n--- Response start (first 4000 chars) ---\n")
            print(text[:4000])
            print("\n--- Response end ---\n")
    except Exception as e:
        print("Request failed:", repr(e))

if __name__ == "__main__":
    main()
