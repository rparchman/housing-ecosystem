import os

BASE = "housing-ecosystem"

STRUCTURE = {
    "pipeline": {
        "agents": [
            "gis_discovery_agent.py",
            "landbank_scraper_agent.py",
            "parcel_join_agent.py",
            "county_normalization_agent.py",
            "statewide_aggregation_agent.py",
            "fusion_pipeline_agent.py",
        ],
        "scrapers": [
            "base_scraper.py",
            "wayne_lb.py",
            "detroit_lb.py",
            "genesee_lb.py",
            "monroe_lb.py",
            "washtenaw_lb.py",
            "statewide_lb_runner.py",
        ],
        "joiners": [
            "parcel_matcher.py",
            "fuzzy_matcher.py",
            "address_matcher.py",
        ],
        "models": [
            "unified_parcel_model.py",
            "unified_landbank_model.py",
            "county_field_maps.json",
        ],
        "fusion": {
            "fusion_orchestrator.py": None,
            "fusion_steps": [
                "step_gis.py",
                "step_landbank.py",
                "step_join.py",
                "step_normalize.py",
                "step_aggregate.py",
                "step_index.py",
            ],
        },
        "config": [
            "counties.json",
            "counties_validated.json",
            "landbank_inventory.json",
            "landbank_parcel_join.json",
            "unified_county_data.json",
            "statewide_landbank_dataset.json",
        ],
        "utils": [
            "http.py",
            "arcgis.py",
            "parsing.py",
            "logging.py",
            "normalization.py",
        ],
        "scripts": [
            "discovery_runner.py",
            "scrape_runner.py",
            "join_runner.py",
            "normalize_runner.py",
            "aggregate_runner.py",
            "fusion_runner.py",
        ],
    },
    "api": {
        "server.py": None,
        "routes": [
            "parcels.py",
            "landbank.py",
            "search.py",
            "analytics.py",
        ],
        "models": [
            "parcel.py",
            "landbank.py",
            "search_index.py",
        ],
    },
    "frontend": {
        "web": [],
        "mobile": [],
        "components": [],
    },
    "docs": [
        "architecture.md",
        "agents.md",
        "data_model.md",
        "fusion_pipeline.md",
    ],
}


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"[DIR]  {path}")


def ensure_file(path):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("# placeholder\n")
        print(f"[FILE] {path}")


def build_structure(base, structure):
    ensure_dir(base)

    for key, value in structure.items():
        subpath = os.path.join(base, key)

        # If value is a dict → nested folders
        if isinstance(value, dict):
            ensure_dir(subpath)
            build_structure(subpath, value)

        # If value is a list → files inside folder
        elif isinstance(value, list):
            ensure_dir(subpath)
            for filename in value:
                ensure_file(os.path.join(subpath, filename))

        # If value is None → single file
        elif value is None:
            ensure_file(subpath)


if __name__ == "__main__":
    build_structure(BASE, STRUCTURE)
    print("\nStructure generation complete.")
