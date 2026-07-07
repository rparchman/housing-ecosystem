#!/usr/bin/env python3
import argparse
from pipeline.agents.gis_discovery_agent import GISDiscoveryAgent

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true", help="Apply recommended endpoints to counties.json")
    p.add_argument("--dry-run", action="store_true", help="Show what would be applied without writing")
    p.add_argument("--workers", type=int, default=6)
    args = p.parse_args()

    # Construct agent without passing max_workers (agent handles max_workers internally if needed)
    agent = GISDiscoveryAgent()
    results = agent.run()
    print("Discovery complete. Results written to pipeline/config/counties_validated.json")

    if args.apply:
        # agent.apply_recommendations() writes changes and creates a backup.
        # For a dry-run, show the merged config without writing.
        if args.dry_run:
            # Show what would be applied: merge recommendations into a copy of the config and print it
            cfg = agent.load_config()
            for key, val in agent.validated.items():
                rec = val.get("recommended")
                if rec:
                    cfg_entry = cfg.get(key, {})
                    cfg_entry["gis_url"] = val.get("gis_url") or rec.get("svc_root") or rec.get("root")
                    if rec.get("id") is not None:
                        cfg_entry["layer_id"] = rec.get("id")
                    cfg[key] = cfg_entry
            import json
            print("Dry-run merged config (not written):")
            print(json.dumps(cfg, indent=2))
        else:
            agent.apply_recommendations()
            print("Applied recommendations and backed up original counties.json to counties.json.bak")





