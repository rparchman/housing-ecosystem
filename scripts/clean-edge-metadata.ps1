<#
  clean-edge-metadata.ps1
  - Usage:
      # Preview only (safe)
      .\scripts\clean-edge-metadata.ps1

      # Apply changes (creates .bak backups and edits files)
      .\scripts\clean-edge-metadata.ps1 -Apply
#>

param(
  [switch]$Apply
)

# Patterns to search for (add more patterns if needed)
$patterns = @(
  'edge_all_open_tabs',
  'edge_all_open_tabs\s*=',
  '<WebsiteContent_[^>]+>',
  'edge_all_open_tabs\s*=\s*

\['
)

# File globs to search (restrict to code and tests)
$paths = @('.\src', '.\tests', '.\tools', '.\scripts')

Write-Host "Starting metadata scan. Apply mode:" ($Apply.IsPresent) -ForegroundColor Cyan

$matches = @()

foreach ($p in $paths) {
  if (-not (Test-Path $p)) { continue }
  Get-ChildItem -Path $p -Recurse -File -Include *.py,*.js,*.ts,*.json,*.md,*.txt -ErrorAction SilentlyContinue |
    ForEach-Object {
      $file = $_.FullName
      try {
        $content = Get-Content -Raw -ErrorAction Stop -LiteralPath $file
      } catch {
        return
      }
      foreach ($pat in $patterns) {
        if ($content -match $pat) {
          $matches += [PSCustomObject]@{ File = $file; Pattern = $pat }
        }
      }
    }
}

if ($matches.Count -eq 0) {
  Write-Host "No candidate files found for the configured patterns." -ForegroundColor Green
  exit 0
}

Write-Host "Found candidate files:" -ForegroundColor Yellow
$matches | Select-Object -Unique File | ForEach-Object { Write-Host " - $_.File" }

if (-not $Apply) {
  Write-Host ""
  Write-Host "Preview mode only. To back up and remove matched blocks run with -Apply." -ForegroundColor Cyan
  exit 0
}

# Apply mode: back up and remove matched blocks
foreach ($entry in $matches | Select-Object -Unique File) {
  $file = $entry.File
  $bak = "$file.bak"
  Write-Host "Backing up $file -> $bak" -ForegroundColor Cyan
  Copy-Item -LiteralPath $file -Destination $bak -Force

  $lines = Get-Content -LiteralPath $file -ErrorAction Stop
  $outLines = @()
  $skip = $false

  for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]

    # Start skip when we see the metadata variable or WebsiteContent tag
    if ($line -match '^\s*edge_all_open_tabs\s*=' -or $line -match '<WebsiteContent_[^>]+>') {
      Write-Host "  Removing block starting at line $($i+1) in $file" -ForegroundColor Yellow
      $skip = $true
      continue
    }

    # If skipping, stop when we hit a closing bracket or closing tag
    if ($skip) {
      if ($line -match '^\s*\]

\s*;?\s*$' -or $line -match '</WebsiteContent_[^>]+>') {
        $skip = $false
        continue
      } else {
        continue
      }
    }

    $outLines += $line
  }

  # Write cleaned file
  Set-Content -LiteralPath $file -Value $outLines -Force
  Write-Host "Cleaned $file (backup at $bak)" -ForegroundColor Green
}

Write-Host "Done. Review backups (*.bak) before committing." -ForegroundColor Green
