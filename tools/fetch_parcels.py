#!/usr/bin/env python3
import os, sys, json, math, argparse, time
import requests
from urllib.parse import urljoin, urlparse, urlencode

SESSION = requests.Session()
SESSION.headers.update({"User-Agent":"parcel-fetcher/1.0"})

def download_file(url, outpath):
    r = SESSION.get(url, stream=True, timeout=30)
    r.raise_for_status()
    with open(outpath, "wb") as f:
        for chunk in r.iter_content(32768):
            if chunk:
                f.write(chunk)
    return outpath

def download_from_hub(item_url, outdir="."):
    # naive: fetch page, look for .zip/.geojson links; for robust use Hub API
    r = SESSION.get(item_url, timeout=20)
    r.raise_for_status()
    text = r.text
    for ext in (".geojson", ".zip", ".shp.zip"):
        idx = text.find(ext)
        if idx != -1:
            # find href before ext
            start = text.rfind('href="', 0, idx)
            if start != -1:
                start += 6
                end = text.find('"', start)
                link = text[start:end]
                link = urljoin(item_url, link)
                fname = os.path.join(outdir, os.path.basename(urlparse(link).path))
                print("Downloading", link, "->", fname)
                return download_file(link, fname)
    raise RuntimeError("No direct download found on hub page")

def query_layer_metadata(layer_url):
    meta_url = layer_url.rstrip("/") + "?f=json"
    r = SESSION.get(meta_url, timeout=20)
    r.raise_for_status()
    return r.json()

def download_feature_service(layer_query_url, out_geojson):
    # layer_query_url should be like .../MapServer/0/query
    meta = query_layer_metadata(layer_query_url.replace("/query",""))
    max_rec = meta.get("maxRecordCount", 1000)
    supports_geojson = True  # try f=geojson; servers 10.4+ support it
    # get object id field and range
    oid_field = meta.get("objectIdField", "OBJECTID")
    # get min/max OID via statistics
    stats_url = layer_query_url + "?where=1=1&returnIdsOnly=true&f=json"
    r = SESSION.get(stats_url, timeout=30)
    r.raise_for_status()
    ids = r.json().get("objectIds")
    if not ids:
        # fallback to offset/limit approach
        offset = 0
        features = []
        while True:
            params = {"where":"1=1","outFields":"*","f":"geojson","resultOffset":offset,"resultRecordCount":max_rec}
            r = SESSION.get(layer_query_url, params=params, timeout=60)
            r.raise_for_status()
            data = r.json()
            feats = data.get("features", [])
            features.extend(feats)
            print("Fetched", len(feats), "features (offset", offset, ")")
            if len(feats) < max_rec:
                break
            offset += max_rec
            time.sleep(0.2)
    else:
        ids = sorted(ids)
        features = []
        chunk = max_rec
        for i in range(0, len(ids), chunk):
            group = ids[i:i+chunk]
            params = {"objectIds":",".join(map(str,group)),"outFields":"*","f":"geojson"}
            r = SESSION.get(layer_query_url, params=params, timeout=60)
            r.raise_for_status()
            data = r.json()
            feats = data.get("features", [])
            features.extend(feats)
            print("Fetched", len(feats), "features (oids", group[0], "-", group[-1], ")")
            time.sleep(0.2)
    # write combined GeoJSON
    fc = {"type":"FeatureCollection","features":features}
    with open(out_geojson,"w",encoding="utf-8") as f:
        json.dump(fc, f)
    return out_geojson

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--hub", help="ArcGIS Hub/Open Data item URL to download")
    p.add_argument("--layer", help="ArcGIS Feature Service layer query URL (…/query)")
    p.add_argument("--out", default="out.geojson")
    args = p.parse_args()
    if args.hub:
        print("Downloading from hub...")
        print(download_from_hub(args.hub, outdir=os.path.dirname(args.out) or "."))
    elif args.layer:
        print("Downloading from feature service...")
        print(download_feature_service(args.layer, args.out))
    else:
        p.print_help()
