param(
  [Parameter(Mandatory=$true)][string]$InputFile,
  [Parameter(Mandatory=$true)][string]$OutputFile
)

# Config
$UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GISFinder/1.0"
$keywords = @("parcel","gis","property","maps","parcelviewer","parcel viewer","parcel map","parcel data","property search")
$duckBase = "https://html.duckduckgo.com/html/"

function Do-DuckSearch {
  param($query, $num=5)
  $q = [System.Web.HttpUtility]::UrlEncode($query)
  $url = "$duckBase?q=$q"
  try {
    $r = Invoke-WebRequest -Uri $url -Headers @{ "User-Agent" = $UserAgent } -UseBasicParsing -TimeoutSec 15
  } catch {
    Write-Warning "DuckDuckGo search failed for: $query"
    return @()
  }
  # DuckDuckGo HTML returns results in <a class="result__a" href="...">
  $links = @()
  foreach ($a in $r.AllElements | Where-Object { $_.tagName -eq "a" -and $_.className -match "result__a" }) {
    $href = $a.href
    if ($href) { $links += $href }
    if ($links.Count -ge $num) { break }
  }
  return $links
}

function Get-CandidateLinks {
  param($url)
  try {
    $r = Invoke-WebRequest -Uri $url -Headers @{ "User-Agent" = $UserAgent } -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
  } catch {
    return @()
  }
  $base = $r.BaseResponse.ResponseUri.AbsoluteUri
  $links = @()
  foreach ($a in $r.Links) {
    $href = $a.href
    if (-not $href) { continue }
    try {
      $full = [System.Uri]::new([System.Uri]::new($base), $href).AbsoluteUri
    } catch {
      continue
    }
    $text = ($a.innerText -join " ").ToLower()
    $fullLower = $full.ToLower()
    foreach ($k in $keywords) {
      if ($text.Contains($k) -or $fullLower.Contains($k)) {
        $links += [PSCustomObject]@{ Url = $full; Text = $text }
        break
      }
    }
  }
  $links = $links | Sort-Object Url -Unique
  return $links
}

# Prepare output CSV
if (Test-Path $OutputFile) { Remove-Item $OutputFile -Force }
"county,state,confirmed_url,source_page,note" | Out-File -FilePath $OutputFile -Encoding utf8

# Load counties
$counties = Get-Content -Path $InputFile | Where-Object { $_.Trim() -ne "" } | ForEach-Object {
  $parts = $_ -split ","
  if ($parts.Count -ge 2) { [PSCustomObject]@{ County = $parts[0].Trim(); State = $parts[1].Trim() } }
  else { [PSCustomObject]@{ County = $_.Trim(); State = "" } }
}

foreach ($c in $counties) {
  $query = "$($c.County) $($c.State) county GIS parcel site site:.gov"
  Write-Host "`nSearching for: $query" -ForegroundColor Cyan
  $results = Do-DuckSearch -query $query -num 8
  if (-not $results -or $results.Count -eq 0) {
    # fallback without site:.gov
    $results = Do-DuckSearch -query "$($c.County) $($c.State) county GIS parcel site" -num 8
  }

  if (-not $results -or $results.Count -eq 0) {
    "$($c.County),$($c.State),, ,No search results" | Out-File -FilePath $OutputFile -Append -Encoding utf8
    continue
  }

  $candidates = @()
  foreach ($link in $results) {
    Write-Host " Probing: $link" -ForegroundColor Yellow
    $found = Get-CandidateLinks -url $link
    $candidates += [PSCustomObject]@{ Source = $link; FoundLinks = $found }
    Start-Sleep -Seconds 1
  }

  # Present candidates
  Write-Host "`nCandidates for $($c.County), $($c.State):" -ForegroundColor Green
  for ($i=0; $i -lt $candidates.Count; $i++) {
    $idx = $i + 1
    $cand = $candidates[$i]
    Write-Host "[$idx] Source: $($cand.Source)"
    if ($cand.FoundLinks.Count -gt 0) {
      Write-Host "    Found links:"
      $j = 1
      foreach ($f in $cand.FoundLinks) {
        Write-Host "      ($j) $($f.Url) -- $($f.Text.Substring(0,[Math]::Min(80,$f.Text.Length)))"
        $j++
      }
    } else {
      Write-Host "    (no direct parcel links found on source page)"
    }
    Write-Host ""
  }

  # Interactive confirmation
  while ($true) {
    $sel = Read-Host "Select candidate number to confirm, 'n' to enter manual URL, 's' to skip"
    if ($sel -eq 's') {
      "$($c.County),$($c.State),, ,Skipped" | Out-File -FilePath $OutputFile -Append -Encoding utf8
      break
    } elseif ($sel -eq 'n') {
      $manual = Read-Host "Enter the confirmed GIS/parcel URL"
      "$($c.County),$($c.State),$manual,Manual,Manual" | Out-File -FilePath $OutputFile -Append -Encoding utf8
      break
    } elseif ($sel -match '^\d+$') {
      $idx = [int]$sel - 1
      if ($idx -ge 0 -and $idx -lt $candidates.Count) {
        $cand = $candidates[$idx]
        if ($cand.FoundLinks.Count -gt 0) {
          Write-Host "Found links for this source:"
          for ($k=0; $k -lt $cand.FoundLinks.Count; $k++) {
            $num = $k + 1
            Write-Host " ($num) $($cand.FoundLinks[$k].Url)"
          }
          $linkSel = Read-Host "Select link number to confirm or 'b' to go back"
          if ($linkSel -eq 'b') { continue }
          if ($linkSel -match '^\d+$') {
            $lidx = [int]$linkSel - 1
            if ($lidx -ge 0 -and $lidx -lt $cand.FoundLinks.Count) {
              $confirmed = $cand.FoundLinks[$lidx].Url
              $confirm = Read-Host "Confirm saving '$confirmed' for $($c.County), $($c.State)? (y/n)"
              if ($confirm -eq 'y') {
                "$($c.County),$($c.State),$confirmed,$($cand.Source),Auto" | Out-File -FilePath $OutputFile -Append -Encoding utf8
                break
              } else { continue }
            } else { Write-Host "Invalid link number"; continue }
          } else { Write-Host "Invalid input"; continue }
        } else {
          $confirmed = $cand.Source
          $confirm = Read-Host "Confirm saving source page '$confirmed' for $($c.County), $($c.State)? (y/n)"
          if ($confirm -eq 'y') {
            "$($c.County),$($c.State),$confirmed,$($cand.Source),AutoSource" | Out-File -FilePath $OutputFile -Append -Encoding utf8
            break
          } else { continue }
        }
      } else {
        Write-Host "Invalid candidate number"
      }
    } else {
      Write-Host "Invalid input"
    }
  } # end interactive loop
}

Write-Host "`nDone. Confirmed paths saved to $OutputFile" -ForegroundColor Cyan
