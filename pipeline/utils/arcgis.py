# pipeline/utils/arcgis.py — replace sample_features with this
import requests
from typing import Optional, List, Dict, Any

DEFAULT_TIMEOUT = 10

def sample_features(url: str, layer_id: int, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
    try:
        query_url = f"{url.rstrip('/')}/{layer_id}/query"
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "json",
            "resultRecordCount": limit,
            "orderByFields": "OBJECTID ASC",
            "returnGeometry": False
        }
        resp = requests.get(query_url, params=params, timeout=DEFAULT_TIMEOUT)
        if resp.status_code != 200:
            print(f"[arcgis.sample_features] non-200 status {resp.status_code} for {query_url}")
            print(resp.text[:1000])
            return []
        data = resp.json()
        features = data.get("features")
        if features is None:
            print(f"[arcgis.sample_features] no 'features' key in response for {query_url}")
            print("response keys:", list(data.keys()))
            return []
        return features
    except Exception as exc:
        print(f"[arcgis.sample_features] exception: {exc}")
        return []
