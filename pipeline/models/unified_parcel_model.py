"""
Unified Parcel Model
--------------------
Normalizes parcel attributes from any Michigan county into a single,
consistent statewide schema.

This model handles:
    - parcel ID normalization
    - situs address normalization
    - owner name normalization
    - zoning normalization
    - tax/assessment fields
    - building attributes
    - land bank enrichment attachment

It uses county-specific field maps from county_field_maps.json.
"""

import re


class UnifiedParcelModel:

    @staticmethod
    def normalize(parcel: dict, field_map: dict) -> dict:
        """
        Normalize a raw GIS parcel record into the unified statewide schema.

        parcel: raw GIS parcel attributes
        field_map: mapping of county-specific fields → unified fields
        """

        def get(field):
            """
            Helper to fetch a field using the county's field map.
            """
            source = field_map.get(field)
            if not source:
                return None
            return parcel.get(source)

        unified = {
            # -----------------------------
            # Core identifiers
            # -----------------------------
            "parcel_id": UnifiedParcelModel.clean_pid(get("parcel_id")),
            "county": get("county") or parcel.get("county"),

            # -----------------------------
            # Location / address
            # -----------------------------
            "address": UnifiedParcelModel.clean_address(get("address")),
            "city": get("city"),
            "zip": get("zip"),

            # -----------------------------
            # Ownership
            # -----------------------------
            "owner": UnifiedParcelModel.clean_owner(get("owner")),
            "owner_address": UnifiedParcelModel.clean_address(get("owner_address")),

            # -----------------------------
            # Tax / assessment
            # -----------------------------
            "tax_year": UnifiedParcelModel.to_int(get("tax_year")),
            "assessed_value": UnifiedParcelModel.to_int(get("assessed_value")),
            "taxable_value": UnifiedParcelModel.to_int(get("taxable_value")),
            "land_value": UnifiedParcelModel.to_int(get("land_value")),
            "improvement_value": UnifiedParcelModel.to_int(get("improvement_value")),

            # -----------------------------
            # Zoning / land use
            # -----------------------------
            "zoning": UnifiedParcelModel.clean_zoning(get("zoning")),
            "land_use": get("land_use"),

            # -----------------------------
            # Building attributes
            # -----------------------------
            "year_built": UnifiedParcelModel.to_int(get("year_built")),
            "sqft": UnifiedParcelModel.to_int(get("sqft")),
            "bedrooms": UnifiedParcelModel.to_int(get("bedrooms")),
            "bathrooms": UnifiedParcelModel.to_int(get("bathrooms")),

            # -----------------------------
            # Geometry (optional)
            # -----------------------------
            "geometry": parcel.get("geometry"),

            # -----------------------------
            # Land bank enrichment (added later)
            # -----------------------------
            "landbank": None,
        }

        return unified

    # ---------------------------------------------------------
    # Normalization helpers
    # ---------------------------------------------------------

    @staticmethod
    def clean_pid(pid: str):
        """
        Normalize parcel IDs:
            - uppercase
            - remove spaces/dashes
            - strip leading zeros
        """
        if not pid:
            return None
        pid = pid.strip().replace("-", "").replace(" ", "").upper()
        pid = re.sub(r"^0+", "", pid)
        return pid

    @staticmethod
    def clean_address(addr: str):
        """
        Normalize addresses:
            - uppercase
            - remove punctuation
            - collapse whitespace
        """
        if not addr:
            return None
        addr = addr.upper()
        addr = re.sub(r"[^\w\s]", "", addr)
        addr = re.sub(r"\s+", " ", addr).strip()
        return addr

    @staticmethod
    def clean_owner(owner: str):
        """
        Normalize owner names:
            - uppercase
            - remove punctuation
            - collapse whitespace
        """
        if not owner:
            return None
        owner = owner.upper()
        owner = re.sub(r"[^\w\s]", "", owner)
        owner = re.sub(r"\s+", " ", owner).strip()
        return owner

    @staticmethod
    def clean_zoning(z: str):
        """
        Normalize zoning codes:
            - uppercase
            - remove spaces
        """
        if not z:
            return None
        z = z.upper().strip().replace(" ", "")
        return z

    @staticmethod
    def to_int(value):
        """
        Convert numeric fields safely.
        """
        try:
            return int(value)
        except:
            return None
