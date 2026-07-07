import requests

def fetch_gis_parcels(gis_url):
    """
    Fetches parcel data from an ArcGIS REST endpoint.
    Handles DNS failures, 404s, and connection errors gracefully.
    """

    query = {
        "where": "1=1",
        "outFields": "*",
        "f": "json"
    }

    try:
        response = requests.get(f"{gis_url}/query", params=query, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("features", [])

    except Exception as e:
        return {
            "error": str(e),
            "features": []
        }
