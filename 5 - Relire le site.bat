@echo off
cd /d "%~dp0"
echo Construction du site puis ouverture de la relecture (http://localhost:8792/)
python construire_site.py
start "" http://localhost:8792/
python relecture\serveur_relecture.py
pause
