@echo off
cd /d C:\Users\ricki\housing-ecosystem
call .venv\Scripts\activate.bat
python -c "from services.landbank.scraper_county_MI_primary import run_scraper_sample; print(run_scraper_sample())"
