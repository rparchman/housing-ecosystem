@echo off
cd /d C:\Users\ricki\housing-ecosystem
call .venv\Scripts\activate.bat
python -m uvicorn api.routes.contractor.router:router --reload --port 8000
