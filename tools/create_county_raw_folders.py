# tools/create_county_raw_folders.py
"""
Create data/raw/<county> folders.

Behavior:
- If manifests/ exists and contains YAML files, create one folder per manifest using the
  manifest 'county' field (fallback: filename).
- Otherwise, if data/counties.txt exists, create one folder per non-empty line.
- Prints created and existing folder counts.

Usage:
  .venv\\Scripts\\python.exe tools\\create_county_raw_folders.py
"""
import sys
import yaml
from pathlib import Path
import re

ROOT = Path.cwd()
MANIFESTS_DIR = ROOT / "manifests"
RAW_ROOT = ROOT / "data" / "raw"
COUNTIES_TXT = ROOT / "data" / "counties.txt"

def safe_name(name: str) -> str:
    # Replace problematic characters with underscore and collapse spaces
    s = name.strip()
    s = re.sub(r"[\\/:\*\?\"<>\|]+", "_", s)
    s = re.sub(r"\s+", " ", s)
    s = s.replace(" ", "_")
    return s

def create_folder(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def from_manifests():
    created = []
    if not MANIFESTS_DIR.exists():
        return created
    for p in sorted(MANIFESTS_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
            county = data.get("county") if isinstance(data, dict) else None
        except Exception:
            county = None
        if not county:
            county = p.stem
        folder = RAW_ROOT / safe_name(county)
        create_folder(folder)
        created.append(str(folder))
    return created

def from_counties_txt():
    created = []
    if not COUNTIES_TXT.exists():
        return created
    for line in COUNTIES_TXT.read_text(encoding="utf-8").splitlines():
        name = line.strip()
        if not name:
            continue
        folder = RAW_ROOT / safe_name(name)
        create_folder(folder)
        created.append(str(folder))
    return created

def main():
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    created = from_manifests()
    source = "manifests"
    if not created:
        created = from_counties_txt()
        source = "data/counties.txt" if created else None
    if not created:
        print("No manifests or counties.txt found. Nothing created.")
        print("Create manifests/*.yaml or data/counties.txt and re-run.")
        return
    print(f"Created or ensured {len(created)} folders from {source}:")
    for c in created[:50]:
        print(" ", c)
    if len(created) > 50:
        print(" ...", len(created) - 50, "more")

if __name__ == '__main__':
    main()
