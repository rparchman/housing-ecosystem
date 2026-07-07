def normalize_parcel(feature):
    """
    Converts raw GIS parcel data into your unified schema.
    """
    attrs = feature.get("attributes", {})

    return {
        "parcel_id": attrs.get("PARCELID") or attrs.get("parcel_id"),
        "county": attrs.get("COUNTY") or attrs.get("county"),
        "address": attrs.get("SITUS") or attrs.get("address"),
        "city": attrs.get("CITY"),
        "state": "MI",
        "zip": attrs.get("ZIP"),
        "acreage": attrs.get("ACREAGE"),
        "land_value": attrs.get("LANDVALUE"),
        "building_value": attrs.get("BUILDVALUE"),
        "total_value": attrs.get("TOTALVALUE"),
        "geometry": feature.get("geometry")
    }
