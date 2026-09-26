@echo off
cd /d "%~dp0"
if not exist _site (python construire_site.py)
start "" http://localhost:8791/
cd _site
python -m http.server 8791
