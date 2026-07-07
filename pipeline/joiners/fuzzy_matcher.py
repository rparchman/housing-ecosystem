"""
Fuzzy Matcher
Fallback matcher when parcel ID and address matching fail.
Uses partial string similarity and heuristic scoring.
"""

import difflib
from pipeline.utils.arcgis import query_layer


def fuzzy_score(a, b):
    """
    Returns similarity score between two strings.
    """
    if not a or not b:
        return 0
    return difflib.SequenceMatcher(None, a, b).ratio()


def fuzzy_match(record, gis_info):
    """
    Attempts fuzzy match using:
        - partial parcel ID similarity
        - partial address similarity
        - heuristic scoring
    """
    parcel_id = record.get("parcel_id")
    address = record.get("address")

    gis_url = gis_info.get("gis_url")
    layer_id = gis_info.get("layer_id", 0)

    # Pull a sample of parcels from GIS
    sample = query_layer(gis_url, layer_id, "1=1", limit=200)

    if not sample:
        return None

    best = None
    best_score = 0

    for parcel in sample:
        score = 0

        # Parcel ID similarity
        if parcel_id and parcel.get("parcel"):
            score += fuzzy_score(parcel_id, parcel.get("parcel"))

        # Address similarity
        if address and parcel.get("address"):
            score += fuzzy_score(address, parcel.get("address"))

        if score > best_score:
            best_score = score
            best = parcel

    # Require minimum confidence
    if best_score >= 0.55:
        return best

    return None
