# scripts/init_and_run_discovery.ps1
Set-StrictMode -Version Latest

$repoRoot = (Get-Location).Path
$configDir = Join-Path $repoRoot "pipeline\config"
$configFile = Join-Path $configDir "counties.json"
$backupFile = Join-Path $configDir "counties.json.bak"
$validatedFile = Join-Path $configDir "counties_validated.json"

# Ensure config directory exists
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

# Backup existing config if present
if (Test-Path $configFile) {
    Copy-Item -Path $configFile -Destination $backupFile -Force
    Write-Host "Backed up existing counties.json to counties.json.bak"
}

# Full Michigan counties list JSON
$contents = @'
{
  "alcona": {"name": "Alcona County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "alger": {"name": "Alger County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "allegan": {"name": "Allegan County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "alpena": {"name": "Alpena County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "antrim": {"name": "Antrim County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "arenac": {"name": "Arenac County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "baraga": {"name": "Baraga County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "barry": {"name": "Barry County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "bay": {"name": "Bay County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "benzie": {"name": "Benzie County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "berrien": {"name": "Berrien County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "branch": {"name": "Branch County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "calhoun": {"name": "Calhoun County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "cass": {"name": "Cass County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "charlevoix": {"name": "Charlevoix County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "cheboygan": {"name": "Cheboygan County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "chippewa": {"name": "Chippewa County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "clare": {"name": "Clare County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "clinton": {"name": "Clinton County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "crawford": {"name": "Crawford County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "delta": {"name": "Delta County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "dickinson": {"name": "Dickinson County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "eaton": {"name": "Eaton County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "emmet": {"name": "Emmet County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "genesee": {"name": "Genesee County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "gladwin": {"name": "Gladwin County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "gogebic": {"name": "Gogebic County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "grand_traverse": {"name": "Grand Traverse County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "gratiot": {"name": "Gratiot County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "hillsdale": {"name": "Hillsdale County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "houghton": {"name": "Houghton County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "huron": {"name": "Huron County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "ingham": {"name": "Ingham County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "ionia": {"name": "Ionia County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "iosco": {"name": "Iosco County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "iron": {"name": "Iron County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "isabella": {"name": "Isabella County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "jackson": {"name": "Jackson County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "kalamazoo": {"name": "Kalamazoo County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "kalkaska": {"name": "Kalkaska County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "kent": {"name": "Kent County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "keweenaw": {"name": "Keweenaw County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "lake": {"name": "Lake County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "lapeer": {"name": "Lapeer County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "leelanau": {"name": "Leelanau County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "lenawee": {"name": "Lenawee County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "livingston": {"name": "Livingston County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "luce": {"name": "Luce County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "mackinac": {"name": "Mackinac County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "macomb": {"name": "Macomb County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "manistee": {"name": "Manistee County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "marquette": {"name": "Marquette County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "mason": {"name": "Mason County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "mecosta": {"name": "Mecosta County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "menominee": {"name": "Menominee County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "midland": {"name": "Midland County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "missaukee": {"name": "Missaukee County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "monroe": {"name": "Monroe County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "montcalm": {"name": "Montcalm County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "montmorency": {"name": "Montmorency County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "muskegon": {"name": "Muskegon County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "newaygo": {"name": "Newaygo County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "oakland": {"name": "Oakland County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "oceana": {"name": "Oceana County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "ogemaw": {"name": "Ogemaw County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "ontonagon": {"name": "Ontonagon County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "osceola": {"name": "Osceola County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "oscoda": {"name": "Oscoda County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "ottawa": {"name": "Ottawa County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "presque_isle": {"name": "Presque Isle County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "roscommon": {"name": "Roscommon County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "saginaw": {"name": "Saginaw County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "sanilac": {"name": "Sanilac County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "schoolcraft": {"name": "Schoolcraft County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "shiawassee": {"name": "Shiawassee County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "st_clair": {"name": "St. Clair County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "st_joesph": {"name": "St. Joseph County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "tuscola": {"name": "Tuscola County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "van_buren": {"name": "Van Buren County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "washtenaw": {"name": "Washtenaw County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "wayne": {"name": "Wayne County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""},
  "wexford": {"name": "Wexford County", "gis_url": "", "layer_id": null, "disabled": false, "notes": ""}
}
'@

# Write the file
Set-Content -Path $configFile -Value $contents -Encoding UTF8
Write-Host "Wrote counties.json to $configFile"

# Ensure pipeline package is importable for the run
$env:PYTHONPATH = $repoRoot

# Run discovery runner
Write-Host "Running discovery runner..."
python scripts\discovery_runner.py

# Show result summary if present
if (Test-Path $validatedFile) {
    Write-Host "Discovery complete. Validated file written to pipeline/config/counties_validated.json"
    Get-Content $validatedFile -Raw | Out-Host
} else {
    Write-Host "Discovery runner did not produce counties_validated.json. Check logs."
}
