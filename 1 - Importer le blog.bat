@echo off
cd /d "%~dp0"
echo Import des billets et des images depuis ..\blog\export (quelques minutes la premiere fois)
python importer_blog.py
pause
