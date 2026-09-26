@echo off
cd /d "%~dp0"
python construire_site.py --verifier || (pause & exit /b 1)
git add contenu gabarits static images site.yaml construire_site.py extraire_retours.py importer_blog.py requirements.txt CNAME .github .gitignore LISEZ-MOI.md *.bat
git commit -m "Mise a jour du site"
git push
pause
