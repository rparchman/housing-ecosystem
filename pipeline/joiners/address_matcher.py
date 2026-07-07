"""
Address Matcher
Matches land bank addresses to GIS parcel situs addresses.
"""

import re
from pipeline.utils.arcgis import query_layer


def normalize_address(addr: str):
    """
    Normalize addresses:
        - uppercase
        - remove punctuation
        - collapse spaces
    """
    if not addr:
        return None

    addr = addr.upper()
    addr = re.sub(r"[^\w\s]", "", addr)
    addr = re.sub(r"\s+", " ", addr).strip()
    return addr


def match_by_address(address, gis_info):
    """
    Attempts address match using GIS FeatureServer query.
    """
    if not address:
        return None

    norm = normalize_address(address)
    if not norm:
        return None

    gis_url = gis_info.get("gis_url")
    layer_id = gis_info.get("layer_id", 0)

    fields = ["address", "situs", "situs_address", "location", "prop_addr"]

    for field in fields:
        where = f"UPPER({field}) LIKE '%{norm}%'"
        result = query_layer(gis_url, layer_id, where)

        if result:
            return result

    return None
