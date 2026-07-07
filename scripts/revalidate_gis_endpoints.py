#!/usr/bin/env python3
"""
Revalidate GIS endpoints from pipeline/config/counties.json
Outputs pipeline/config/counties_validated.json with diagnostics and recommendations.
"""
import json
import socket
import requests
from urllib.parse import urljoin, urlparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

ROOT = Path("pipeline/config/counties.json")
OUT = Path("pipeline/config/counties_validated.json")
TIMEOUT = 10
MAX_WORKERS = 6

def host_from_url(url):
    return urlparse(url).netloc

def dns_lookup(host):
    try:
        ips = socket.gethostbyname_ex(host)[2]
        return {"ok": True, "ips": ips}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def http_get_json(url, params=None):
    try:
        r = requests.get(url, params=params or {"f":"json"}, timeout=TIMEOUT)
        r.raise_for_status()
        return {"ok": True, "status_code": r.status_code, "json": r.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def enumerate_layers(base_url):
    """
    Try MapServer and FeatureServer roots to list layers.
    Returns list of layers with id and name.
    """
    candidates = []
    for suffix in ["/MapServer", "/FeatureServer"]:
        root = urljoin(base_url, suffix)
        res = http_get_json(root, params={"f":"json"})
        if res["ok"]:
            info = res["json"]
            layers = info.get("layers") or info.get("services") or info.get("layers", [])
            # MapServer returns 'layers' list; FeatureServer may return 'layers' too
            if isinstance(layers, list) and layers:
                for layer in layers:
                    # layer may be dict with id/name or nested
                    lid = layer.get("id") if isinstance(layer, dict) else None
                    name = layer.get("name") if isinstance(layer, dict) else str(layer)
                    candidates.append({"root": root, "id": lid, "name": name})
    return candidates

def test_layer_query(root, layer_id):
    """
    Query a layer for features count using f=json and return feature count or error.
    """
    if layer_id is None:
        return {"ok": False, "error": "no layer id"}
    query_url = f"{root}/{layer_id}/query"
    params = {"where":"1=1", "outFields":"*", "f":"json", "resultRecordCount":1}
    res = http_get_json(query_url, params=params)
    if not res["ok"]:
        return {"ok": False, "error": res.get("error")}
    data = res["json"]
    features = data.get("features", [])
    return {"ok": True, "features_sample": len(features), "has_features": len(features) > 0}

def detect_parcel_layer(candidates):
    """
    Heuristic: prefer layers whose name contains 'parcel' or fields like 'PIN','PARCEL','PARCELID'
    """
    scored = []
    for c in candidates:
        score = 0
        name = (c.get("name") or "").lower()
        if "parcel" in name or "pin" in name:
            score += 10
        # try a quick field probe if layer id exists
        if c.get("id") is not None:
            meta_url = f"{c['root']}/{c['id']}?f=json"
            meta = http_get_json(meta_url)
            if meta["ok"]:
                fields = [f.get("name","").lower() for f in meta["json"].get("fields",[])]
                if any(k in " ".join(fields) for k in ("pin","parcel","parcelid","parcel_id")):
                    score += 5
        scored.append((score, c))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [c for s,c in scored if s>0] + [c for s,c in scored if s==0]

def validate_county(key, county):
    gis_url = county.get("gis_url")
    host = host_from_url(gis_url)
    result = {"name": county.get("name"), "gis_url": gis_url, "host": host}
    dns = dns_lookup(host)
    result["dns"] = dns
    if not dns["ok"]:
        result["status"] = "dns_failed"
        return key, result

    # enumerate layers
    candidates = enumerate_layers(gis_url)
    result["candidates_count"] = len(candidates)
    result["candidates"] = candidates

    # detect likely parcel layers
    prioritized = detect_parcel_layer(candidates)
    result["prioritized_candidates"] = prioritized

    # test top candidates
    tested = []
    for c in prioritized[:4]:
        test = test_layer_query(c["root"], c.get("id"))
        tested.append({"candidate": c, "test": test})
    result["tested"] = tested

    # pick best candidate that returns features
    for t in tested:
        if t["test"].get("ok") and t["test"].get("has_features"):
            result["recommended"] = {
                "gis_url": t["candidate"]["root"],
                "layer_id": t["candidate"]["id"],
                "reason": "returns features"
            }
            result["status"] = "ok"
            return key, result

    # fallback: if root query returns features (MapServer root with features)
    # otherwise mark as no_features
    result["status"] = "no_features_found"
    return key, result

def main():
    cfg = json.loads(ROOT.read_text())
    results = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(validate_county, k, v): k for k,v in cfg.items()}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Validating"):
            k, res = fut.result()
            results[k] = res
    OUT.write_text(json.dumps(results, indent=2))
    print("Validation complete. Results written to", OUT)

if __name__ == "__main__":
    main()
