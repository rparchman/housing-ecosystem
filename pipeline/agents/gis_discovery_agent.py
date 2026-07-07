# pipeline/agents/gis_discovery_agent.py
from __future__ import annotations
import json
import socket
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests

# Configuration
TIMEOUT = 10
RETRIES = 2
BACKOFF_FACTOR = 1.5
USER_AGENT = "housing-ecosystem-discovery/1.0"

HERE = Path(__file__).resolve().parent
CONFIG_DIR = HERE.parent / "config"
COUNTIES_PATH = CONFIG_DIR / "counties.json"
VALIDATED_PATH = CONFIG_DIR / "counties_validated.json"


class GISDiscoveryAgent:
    def __init__(self, config_path: Path = COUNTIES_PATH):
        self.config_path = config_path
        self.validated: Dict[str, Any] = {}

    def run(self) -> Dict[str, Any]:
        cfg = self.load_config()
        results = {}
        for key, info in cfg.items():
            results[key] = self.inspect_county(key, info)
        self.validated = results
        self.write_validated()
        return results

    def load_config(self) -> Dict:
        """
        Load counties.json safely. If file is empty or invalid JSON, raise a clear error.
        """
        if not self.config_path.exists():
            raise RuntimeError(f"{self.config_path} does not exist. Create it before running discovery.")
        text = self.config_path.read_text(encoding="utf-8").strip()
        if not text:
            raise RuntimeError(f"{self.config_path} is empty. Restore or recreate the file before running discovery.")
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in {self.config_path}: {e}") from e

    # --- network helpers ---
    def dns_check(self, host: str) -> Dict[str, Any]:
        try:
            # prefer getaddrinfo to support IPv4/IPv6
            infos = socket.getaddrinfo(host, None)
            ips = sorted({info[4][0] for info in infos})
            return {"ok": True, "ips": ips}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def http_get_json(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        headers = {"User-Agent": USER_AGENT}
        params = params or {"f": "json"}
        attempt = 0
        while attempt <= RETRIES:
            try:
                r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
                # ArcGIS often returns JSON error objects with 200 status; attempt to parse
                content_type = r.headers.get("content-type", "")
                text = r.text
                try:
                    j = r.json()
                except Exception:
                    j = None
                return {"ok": True, "status_code": r.status_code, "json": j, "text": text, "content_type": content_type}
            except requests.RequestException as e:
                attempt += 1
                if attempt > RETRIES:
                    return {"ok": False, "error": str(e)}
                time.sleep(BACKOFF_FACTOR ** attempt)
        return {"ok": False, "error": "unknown"}

    # --- discovery logic ---
    def inspect_county(self, key: str, info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inspect a single county entry and return diagnostics and recommended candidate(s).
        """
        out: Dict[str, Any] = {"name": info.get("name"), "status": "unknown"}
        gis_url = info.get("gis_url") or ""
        if not gis_url:
            out["status"] = "no_gis_url"
            return out

        # host and dns
        host = self.extract_host(gis_url)
        out["host"] = host
        dns = self.dns_check(host) if host else {"ok": False, "error": "no host"}
        out["dns"] = dns
        if not dns.get("ok"):
            out["status"] = "dns_failed"
            return out

        # try variants and collect candidates
        candidates = []
        tested = []

        # canonicalize base
        base = gis_url.rstrip("/")
        # candidate roots to try
        tries = self.build_candidate_roots(base)

        for root in tries:
            res = self.http_get_json(root, params={"f": "json"})
            tested.append({"root": root, "result": self.summarize_http_result(res)})
            if res.get("ok") and isinstance(res.get("json"), dict):
                j = res["json"]
                # if this is a service root with 'layers' or 'services'
                if "layers" in j and isinstance(j["layers"], list) and j["layers"]:
                    for layer in j["layers"]:
                        candidates.append(self.candidate_from_layer(root, layer))
                elif "services" in j and isinstance(j["services"], list) and j["services"]:
                    # org listing: each service has name and url
                    for svc in j["services"]:
                        svc_url = svc.get("url")
                        if svc_url:
                            # probe service's layer 0
                            cand = self.probe_service_for_candidate(svc_url)
                            if cand:
                                candidates.append(cand)
                elif "error" in j:
                    # record error details
                    pass
                else:
                    # sometimes a FeatureServer root returns fields or other metadata
                    # try to interpret as a layer root if it has 'fields' or 'name'
                    if "fields" in j or "name" in j:
                        # treat as single-layer root
                        candidates.append({"root": root, "id": None, "name": j.get("name"), "meta": j})
        # If no candidates found but base looks like an ArcGIS Online org, enumerate org services
        if not candidates and "/arcgis/rest/services" in base:
            org_root = self.derive_org_root(base)
            if org_root:
                svc_list = self.http_get_json(org_root, params={"f": "json"})
                tested.append({"root": org_root, "result": self.summarize_http_result(svc_list)})
                if svc_list.get("ok") and isinstance(svc_list.get("json"), dict):
                    for svc in svc_list["json"].get("services", []):
                        svc_url = svc.get("url")
                        if svc_url:
                            cand = self.probe_service_for_candidate(svc_url)
                            if cand:
                                candidates.append(cand)

        # score candidates
        prioritized = []
        for c in candidates:
            score = self.score_candidate(c)
            c["score"] = score
            prioritized.append(c)
        prioritized.sort(key=lambda x: x.get("score", 0), reverse=True)

        out["candidates_count"] = len(candidates)
        out["candidates"] = candidates
        out["prioritized_candidates"] = prioritized
        out["tested"] = tested

        # choose recommended if any candidate has features or parcel-like fields
        recommended = None
        for p in prioritized:
            if p.get("sample_features", 0) > 0 or p.get("has_parcel_fields"):
                recommended = p
                break
        if recommended:
            out["recommended"] = recommended
            out["status"] = "ok"
            # normalize recommended gis_url and layer_id
            out["gis_url"] = recommended.get("svc_root") or recommended.get("root")
            if recommended.get("id") is not None:
                out["layer_id"] = recommended.get("id")
        else:
            out["status"] = "no_features_found"
        return out

    # --- helpers for candidate discovery ---
    def build_candidate_roots(self, base: str) -> List[str]:
        tries = []
        tries.append(base)
        # strip trailing numeric id if present
        m = re.match(r"(.*/)(\d+)$", base)
        if m:
            tries.append(m.group(1).rstrip("/"))
        # try MapServer/FeatureServer variants
        if not base.endswith("/MapServer") and not base.endswith("/FeatureServer"):
            tries.append(base + "/MapServer")
            tries.append(base + "/FeatureServer")
        # try without trailing layer id if present
        tries = list(dict.fromkeys([t.rstrip("/") for t in tries]))
        # ensure full REST services root if possible
        if "/arcgis/rest/services" in base:
            prefix = base.split("/arcgis/rest/services")[0] + "/arcgis/rest/services"
            tries.append(prefix)
        return tries

    def candidate_from_layer(self, root: str, layer: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "root": root,
            "id": layer.get("id"),
            "name": layer.get("name"),
            "meta": layer
        }

    def probe_service_for_candidate(self, svc_url: str) -> Optional[Dict[str, Any]]:
        """
        Probe a service URL (FeatureServer/MapServer) and try layer 0 metadata and a tiny query.
        """
        svc_root = svc_url.rstrip("/")
        # try layer 0 metadata
        layer0_meta = self.http_get_json(f"{svc_root}/0", params={"f": "json"})
        meta = layer0_meta.get("json") if layer0_meta.get("ok") else None
        fields = []
        if isinstance(meta, dict):
            fields = [f.get("name", "").lower() for f in meta.get("fields", []) if isinstance(f, dict)]
        has_parcel_fields = any(k in " ".join(fields) for k in ("pin", "parcel", "parcelid", "assessor", "tax"))
        # try a tiny query to see if features are returned
        sample_features = 0
        try:
            q = self.http_get_json(f"{svc_root}/0/query", params={"where": "1=1", "outFields": "*", "resultRecordCount": 1, "f": "json"})
            if q.get("ok") and isinstance(q.get("json"), dict):
                sample_features = len(q["json"].get("features", []) or [])
        except Exception:
            sample_features = 0
        # if token required or 401/403, mark requires_token
        requires_token = False
        if isinstance(layer0_meta.get("json"), dict) and layer0_meta["json"].get("error", {}).get("code") in (499, 401, 403):
            requires_token = True

        # build candidate
        cand = {
            "svc_root": svc_root,
            "id": 0,
            "name": meta.get("name") if isinstance(meta, dict) else None,
            "fields": fields,
            "has_parcel_fields": has_parcel_fields,
            "sample_features": sample_features,
            "requires_token": requires_token,
            "meta": meta
        }
        # return candidate if it looks promising or public
        if has_parcel_fields or sample_features > 0:
            return cand
        # otherwise return None (not promising)
        return None

    def score_candidate(self, c: Dict[str, Any]) -> float:
        score = 0.0
        if c.get("has_parcel_fields"):
            score += 5.0
        score += float(c.get("sample_features", 0))
        # name heuristics
        name = (c.get("name") or "").lower()
        if any(k in name for k in ("parcel", "assessor", "tax", "property", "pin")):
            score += 2.0
        # penalize token-protected
        if c.get("requires_token"):
            score -= 10.0
        return score

    def derive_org_root(self, base: str) -> Optional[str]:
        """
        Given a URL containing /arcgis/rest/services, return the org services root.
        """
        if "/arcgis/rest/services" not in base:
            return None
        prefix = base.split("/arcgis/rest/services")[0] + "/arcgis/rest/services"
        return prefix + "?f=json"

    def extract_host(self, url: str) -> str:
        m = re.match(r"https?://([^/]+)", url)
        return m.group(1) if m else ""

    def summarize_http_result(self, res: Dict[str, Any]) -> Dict[str, Any]:
        if not res.get("ok"):
            return {"ok": False, "error": res.get("error")}
        j = res.get("json")
        if isinstance(j, dict) and "error" in j:
            return {"ok": True, "status_code": res.get("status_code"), "error": j.get("error")}
        return {"ok": True, "status_code": res.get("status_code"), "keys": list(j.keys()) if isinstance(j, dict) else None}

    def write_validated(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        VALIDATED_PATH.write_text(json.dumps(self.validated, indent=2), encoding="utf-8")

    # Optional: apply recommendations to counties.json (create backup)
    def apply_recommendations(self) -> None:
        """
        Merge recommended entries into counties.json and create a backup.
        This method should be called only after human review or --apply flag.
        """
        cfg = self.load_config()
        backup = self.config_path.with_suffix(".json.bak")
        backup.write_text(self.config_path.read_text(encoding="utf-8"), encoding="utf-8")
        for key, val in self.validated.items():
            rec = val.get("recommended")
            if rec:
                # set gis_url and layer_id
                cfg_entry = cfg.get(key, {})
                cfg_entry["gis_url"] = val.get("gis_url") or rec.get("svc_root") or rec.get("root")
                if rec.get("id") is not None:
                    cfg_entry["layer_id"] = rec.get("id")
                cfg[key] = cfg_entry
        self.config_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


# If run as a script for quick testing
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GIS Discovery Agent")
    parser.add_argument("--apply", action="store_true", help="Apply recommended changes to counties.json (creates backup)")
    args = parser.parse_args()

    agent = GISDiscoveryAgent()
    results = agent.run()
    print("Discovery complete. Results written to", VALIDATED_PATH)
    if args.apply:
        agent.apply_recommendations()
        print("Applied recommendations to", COUNTIES_PATH)

