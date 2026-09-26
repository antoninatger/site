@echo off
cd /d "%~dp0"
echo Telechargement des visuels du site (couvertures, logos, photos) depuis antoninatger.com
python rapatrier_medias.py
pause
