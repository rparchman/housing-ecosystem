@echo off
REM find_gis.bat - wrapper to run the PowerShell probe script from cmd

if "%~1"=="" (
  echo Usage: find_gis.bat counties.txt
  exit /b 1
)

set INPUT=%~1
set OUTPUT=confirmed_gis_paths.csv

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "& { $in = '%INPUT%'; $out = '%OUTPUT%'; . '%~dp0\probe_counties.ps1' -InputFile $in -OutputFile $out }"

pause
