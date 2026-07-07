"""
Michigan Parcel GIS Discovery Script
Counties: Wayne, Monroe, Washtenaw, Oakland, Macomb
Generated: 2026-07-01
"""

import json
import urllib.request
import urllib.error
import urllib.parse

# ─────────────────────────────────────────────
# COUNTY GIS ENDPOINT REGISTRY
# ─────────────────────────────────────────────

COUNTIES = {

    # ══════════════════════════════════════════
    # WAYNE COUNTY
    # ══════════════════════════════════════════
    "Wayne": {
        "official_domain": "https://www.waynecountymi.gov",
        "gis_portal": "https://waynecounty.maps.arcgis.com",
        "open_data": "https://waynecounty.opendata.arcgis.com",
        "property_search": "https://www.waynecountymi.gov/government/elected-officials/treasurer/property-search",
        "arcgis_org_id": "GE9NT2GkM4r2CTMB",
        "rest_root": "https://services1.arcgis.com/GE9NT2GkM4r2CTMB/arcgis/rest/services",
        "parcel_layers": {
            "Tax_Parcels_FeatureServer": {
                "type": "FeatureServer",
                "url": "https://services1.arcgis.com/GE9NT2GkM4r2CTMB/arcgis/rest/services/Wayne_County_Parcels/FeatureServer",
                "layer_0": "https://services1.arcgis.com/GE9NT2GkM4r2CTMB/arcgis/rest/services/Wayne_County_Parcels/FeatureServer/0",
                "query_url": "https://services1.arcgis.com/GE9NT2GkM4r2CTMB/arcgis/rest/services/Wayne_County_Parcels/FeatureServer/0/query",
                "notes": "Tax parcel polygons; WKID 2898 (NAD83 Michigan South ft)"
            },
        },
        "downloads": {
            "open_data_hub": "https://waynecounty.opendata.arcgis.com/search?q=parcel",
            "formats": ["Shapefile", "GeoJSON", "CSV", "KML"],
        },
        "wkid": 2898,
    },

    # ══════════════════════════════════════════
    # OAKLAND COUNTY
    # ══════════════════════════════════════════
    "Oakland": {
        "official_domain": "https://www.oakgov.com",
        "gis_portal": "https://gisservices.oakgov.com/arcgis/rest/services",
        "open_data": "https://gisservices.oakgov.com/arcgis/rest/services",
        "property_search": "https://www.oakgov.com/equalization/Pages/PropertySearch.aspx",
        "arcgis_org_id": None,
        "rest_root": "https://gisservices.oakgov.com/arcgis/rest/services",
        "parcel_layers": {
            "Tax_Parcel_Plus_MapServer": {
                "type": "MapServer",
                "url": "https://gisservices.oakgov.com/arcgis/rest/services/Enterprise/EnterpriseOpenParcelDataMapService/MapServer",
                "layer_1": "https://gisservices.oakgov.com/arcgis/rest/services/Enterprise/EnterpriseOpenParcelDataMapService/MapServer/1",
                "query_url": "https://gisservices.oakgov.com/arcgis/rest/services/Enterprise/EnterpriseOpenParcelDataMapService/MapServer/1/query",
                "record_count": "332000+",
                "notes": "Tax Parcel Plus; owner names redacted per county policy; public access"
            },
            "Parcel_MapServer_Identify": {
                "type": "MapServer",
                "url": "https://gisservices.oakgov.com/arcgis/rest/services/Enterprise/EnterpriseOpenParcelDataMapService/MapServer",
                "identify_url": "https://gisservices.oakgov.com/arcgis/rest/services/Enterprise/EnterpriseOpenParcelDataMapService/MapServer/identify",
                "notes": "Point-in-polygon parcel lookup via Identify"
            },
        },
        "downloads": {
            "geojson_direct": "https://gisservices.oakgov.com/arcgis/rest/services/Enterprise/EnterpriseOpenParcelDataMapService/MapServer/1/query?where=1%3D1&outFields=*&f=geojson",
            "formats": ["GeoJSON (via REST query)", "Shapefile (Open Data Hub)"],
        },
        "wkid": 2898,
    },

    # ══════════════════════════════════════════
    # WASHTENAW COUNTY
    # ══════════════════════════════════════════
    "Washtenaw": {
        "official_domain": "https://www.washtenaw.org",
        "gis_portal": "https://washtenaw.maps.arcgis.com",
        "open_data": "https://washtenaw.opendata.arcgis.com",
        "property_search": "https://www.ewashtenaw.org/government/departments/equalization",
        "arcgis_org_id": "0MSEUqKaxRlEPj5g",
        "rest_root": "https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services",
        "parcel_layers": {
            "Parcels_FeatureServer_Primary": {
                "type": "FeatureServer",
                "item_id": "e2841fdffb9c44ea88553a24dcb9a942",
                "url": "https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services/WashtenawCountyParcels/FeatureServer",
                "layer_0": "https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services/WashtenawCountyParcels/FeatureServer/0",
                "query_url": "https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services/WashtenawCountyParcels/FeatureServer/0/query",
                "notes": "Primary tax parcel FeatureServer; JSON/GeoJSON output supported"
            },
            "Parcels_FeatureServer_Extended": {
                "type": "FeatureServer",
                "item_id": "55bdd176b8d54c90ab8ecb2daeb55c20",
                "url": "https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services/WashtenawParcels_Extended/FeatureServer",
                "layer_0": "https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services/WashtenawParcels_Extended/FeatureServer/0",
                "query_url": "https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services/WashtenawParcels_Extended/FeatureServer/0/query",
                "notes": "Extended attributes: assessment data, land use fields"
            },
        },
        "downloads": {
            "open_data_hub": "https://washtenaw.opendata.arcgis.com/search?q=parcel",
            "bsa_property_search": "https://bsasoftware.com/solutions/BS-A-Online",
            "formats": ["Shapefile", "GeoJSON", "CSV"],
        },
        "wkid": 4326,
    },

    # ══════════════════════════════════════════
    # MONROE COUNTY
    # ══════════════════════════════════════════
    "Monroe": {
        "official_domain": "https://www.co.monroe.mi.us",
        "gis_portal": "https://monroe.maps.arcgis.com",
        "open_data": "https://monroe.opendata.arcgis.com",
        "property_search": "https://www.co.monroe.mi.us/government/departments/equalization/property-search",
        "arcgis_org_id": "hEBFaQ6MiiYe2Rq1",  # verify at monroe.maps.arcgis.com
        "rest_root": "https://services6.arcgis.com/hEBFaQ6MiiYe2Rq1/arcgis/rest/services",
        "parcel_layers": {
            "Property_Data_Exchange_FeatureServer": {
                "type": "FeatureServer",
                "item_id": "953463c144fc4d1abc29f188f433aefb",
                "url": "https://services6.arcgis.com/hEBFaQ6MiiYe2Rq1/arcgis/rest/services/Monroe_County_Parcels/FeatureServer",
                "layer_0": "https://services6.arcgis.com/hEBFaQ6MiiYe2Rq1/arcgis/rest/services/Monroe_County_Parcels/FeatureServer/0",
                "query_url": "https://services6.arcgis.com/hEBFaQ6MiiYe2Rq1/arcgis/rest/services/Monroe_County_Parcels/FeatureServer/0/query",
                "last_updated": "2026-05-11",
                "notes": "Property Data Exchange; verify org ID at monroe.maps.arcgis.com before use"
            },
        },
        "downloads": {
            "open_data_hub": "https://monroe.opendata.arcgis.com/search?q=parcel",
            "state_fallback": "https://gis-michigan.opendata.arcgis.com/search?q=monroe+parcel",
            "formats": ["Shapefile", "GeoJSON"],
        },
        "wkid": 2898,
    },

    # ══════════════════════════════════════════
    # MACOMB COUNTY
    # ══════════════════════════════════════════
    "Macomb": {
        "official_domain": "https://www.macombgov.org",
        "gis_portal": "https://macombcounty.maps.arcgis.com",
        "open_data": "https://macombcounty.opendata.arcgis.com",
        "property_search": "https://www.macombgov.org/GIS",
        "arcgis_org_id": "JmQXFSCuFhD97Wqb",
        "rest_root": "https://services6.arcgis.com/JmQXFSCuFhD97Wqb/arcgis/rest/services",
        "parcel_layers": {
            "Parcel_FeatureServer": {
                "type": "FeatureServer",
                "item_id": "e073e8402b3544628d684719c5cd79d1",
                "url": "https://services6.arcgis.com/JmQXFSCuFhD97Wqb/arcgis/rest/services/Macomb_County_Parcels/FeatureServer",
                "layer_10": "https://services6.arcgis.com/JmQXFSCuFhD97Wqb/arcgis/rest/services/Macomb_County_Parcels/FeatureServer/10",
                "query_url": "https://services6.arcgis.com/JmQXFSCuFhD97Wqb/arcgis/rest/services/Macomb_County_Parcels/FeatureServer/10/query",
                "wkid": 2898,
                "supports_create_replica": True,
                "notes": "24 township sub-layers (0-23); primary polygons at layer 10; Create Replica for bulk export"
            },
        },
        "downloads": {
            "open_data_hub": "https://macombcounty.opendata.arcgis.com/search?q=parcel",
            "bulk_replica": "https://services6.arcgis.com/JmQXFSCuFhD97Wqb/arcgis/rest/services/Macomb_County_Parcels/FeatureServer/createReplica",
            "formats": ["Shapefile (Create Replica)", "GeoJSON", "File Geodatabase"],
        },
        "wkid": 2898,
    },
}


# ─────────────────────────────────────────────
# MICHIGAN STATE GIS RESOURCES
# ─────────────────────────────────────────────

STATE_RESOURCES = {
    "Michigan_GIS_Open_Data":          "https://gis-michigan.opendata.arcgis.com",
    "MI_Center_for_Shared_Solutions":  "https://www.michigan.gov/dtmb/government/css",
    "SIGMA_Viewer":                    "https://sigma.michigan.gov/msp/",
    "MI_Parcel_Viewer":                "https://www.arcgis.com/apps/webappviewer/index.html?id=96af488b79584d63bede25aab0a29f7e",
    "State_FeatureServer_All_Counties":"https://services3.arcgis.com/GpSGtjQSfMDicZmH/arcgis/rest/services/Michigan_Parcels/FeatureServer/0",
}


# ─────────────────────────────────────────────
# PROBE ENDPOINT
# ─────────────────────────────────────────────

def probe_endpoint(name, url, timeout=10):
    """Check if an ArcGIS REST endpoint is reachable and returns valid JSON."""
    probe_url = url.rstrip("/") + "?f=json"
    try:
        req = urllib.request.Request(probe_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "error" in data:
                return f"ERROR — {data['error'].get('message', 'unknown')}"
            label = (
                data.get("serviceDescription") or data.get("name")
                or data.get("layerName") or data.get("type") or "OK"
            )
            return f"LIVE — {str(label)[:80]}"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except Exception as e:
        return f"UNREACHABLE — {type(e).__name__}"


# ─────────────────────────────────────────────
# QUERY PARCEL BY APN / PIN
# ─────────────────────────────────────────────

def query_parcel_by_apn(county_name, apn):
    """Query a county's primary parcel layer for a specific APN/PIN."""
    county = COUNTIES.get(county_name)
    if not county:
        raise ValueError(f"County '{county_name}' not in registry.")
    query_url = None
    for layer in county["parcel_layers"].values():
        if "query_url" in layer:
            query_url = layer["query_url"]
            break
    if not query_url:
        raise ValueError(f"No query URL found for {county_name}.")
    params = urllib.parse.urlencode({
        "where": f"PARCELNO='{apn}' OR APN='{apn}' OR PIN='{apn}'",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "json",
    })
    req = urllib.request.Request(
        f"{query_url}?{params}", headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ─────────────────────────────────────────────
# DOWNLOAD SAMPLE FEATURES AS GEOJSON
# ─────────────────────────────────────────────

def download_sample_geojson(county_name, max_records=10, out_file=None):
    """Download a sample of parcel features as GeoJSON."""
    county = COUNTIES.get(county_name)
    if not county:
        raise ValueError(f"County '{county_name}' not in registry.")
    query_url = None
    for layer in county["parcel_layers"].values():
        if "query_url" in layer:
            query_url = layer["query_url"]
            break
    if not query_url:
        raise ValueError(f"No query URL for {county_name}.")
    params = urllib.parse.urlencode({
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "resultRecordCount": max_records,
        "f": "geojson",
    })
    req = urllib.request.Request(
        f"{query_url}?{params}", headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode("utf-8")
    if out_file:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Saved {county_name} sample → {out_file}")
    return content


# ─────────────────────────────────────────────
# PROBE ALL ENDPOINTS
# ─────────────────────────────────────────────

def probe_all(verbose=True):
    """Probe every registered ArcGIS endpoint and print a live status report."""
    results = {}
    for county_name, county in COUNTIES.items():
        results[county_name] = {}
        if verbose:
            print(f"\n{'='*55}\n  {county_name.upper()} COUNTY\n{'='*55}")
        for layer_name, layer in county["parcel_layers"].items():
            url = layer.get("url") or layer.get("layer_0") or layer.get("layer_10")
            if not url:
                continue
            status = probe_endpoint(layer_name, url)
            results[county_name][layer_name] = status
            if verbose:
                sym = "✓" if "LIVE" in status else "✗"
                print(f"  {sym} {layer_name}\n    {url}\n    → {status}")
    return results


# ─────────────────────────────────────────────
# PRINT REGISTRY
# ─────────────────────────────────────────────

def print_registry():
    print("\n" + "="*65)
    print("  MICHIGAN PARCEL GIS REGISTRY")
    print("  Wayne · Monroe · Washtenaw · Oakland · Macomb")
    print("="*65)
    for cname, county in COUNTIES.items():
        print(f"\n{'─'*65}\n  {cname.upper()} COUNTY\n{'─'*65}")
        print(f"  Official Domain   : {county['official_domain']}")
        print(f"  GIS Portal        : {county['gis_portal']}")
        print(f"  Open Data         : {county['open_data']}")
        print(f"  Property Search   : {county['property_search']}")
        print(f"  ArcGIS REST Root  : {county['rest_root']