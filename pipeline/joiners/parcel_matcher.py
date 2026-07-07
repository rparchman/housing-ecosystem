"""
Exact Parcel ID Matcher
Matches land bank parcel IDs to GIS parcel attributes.
"""

import re
from pipeline.utils.arcgis import query_layer


def clean_pid(pid: str):
    """
    Normalize parcel IDs:
        - remove spaces
        - remove dashes
        - uppercase
        - strip leading zeros
    """
    if not pid:
        return None

    pid = pid.strip().replace("-", "").replace(" ", "").upper()
    pid = re.sub(r"^0+", "", pid)
    return pid


def match_by_parcel_id(parcel_id, gis_info):
    """
    Attempts direct parcel ID match using GIS FeatureServer query.
    """
    if not parcel_id:
        return None

    cleaned = clean_pid(parcel_id)
    if not cleaned:
        return None

    gis_url = gis_info.get("gis_url")
    layer_id = gis_info.get("layer_id", 0)

    # Query GIS layer for matching parcel ID
    fields = ["parcel", "parcelid", "sidwell", "pin", "taxid", "parcel_number"]

    for field in fields:
        where = f"{field} LIKE '%{cleaned}%'"
        result = query_layer(gis_url, layer_id, where)

        if result:
            return result

    return None
