# Save this into C:\Users\ricki\housing-ecosystem\pipeline\utils\arcgis.py

# pipeline/utils/arcgis.py
import requests
from typing import Optional, List, Dict, Any

DEFAULT_TIMEOUT = 10

def validate_service(url: str) -> bool:
    try:
        resp = requests.get(url, params={"f": "json"}, timeout=DEFAULT_TIMEOUT)
        if resp.status_code != 200:
            return False
        data = resp.json()
        return any(k in data for k in ("layers", "services", "currentVersion", "type"))
    except Exception:
        return False

def validate_layer(url: str, layer_id: int) -> Optional[Dict[str, Any]]:
    try:
        layer_url = f"{url.rstrip('/')}/{layer_id}"
        resp = requests.get(layer_url, params={"f": "json"}, timeout=DEFAULT_TIMEOUT)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if isinstance(data, dict) and ("fields" in data or "geometryType" in data or "type" in data):
            return data
        return None
    except Exception:
        return None

def sample_features(url: str, layer_id: int, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
    try:
        query_url = f"{url.rstrip('/')}/{layer_id}/query"
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "json",
            "resultRecordCount": limit,
            "orderByFields": "OBJECTID ASC"
        }
        resp = requests.get(query_url, params=params, timeout=DEFAULT_TIMEOUT)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data.get("features", [])
    except Exception:
        return None
