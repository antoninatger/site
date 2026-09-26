@echo off
cd /d "%~dp0"
echo.
echo  MISE EN LIGNE, PREMIERE FOIS
echo  Avant de continuer : sur github.com, cree un depot VIDE nomme  site  (Public, sans README).
echo.
pause
python construire_site.py --verifier || goto erreur
if not exist .git git init
rem noms de fichiers tres longs (certaines images du blog) et fins de ligne Windows sans avertissements
git config core.longpaths true
git config core.safecrlf false
git add -A || goto erreur
git commit -q -m "Site v1" || goto erreur
git branch -M main
git remote get-url origin >nul 2>&1 || git remote add origin https://github.com/antoninatger/site.git
git push -u origin main || goto erreur
echo.
echo  Envoye. Sur GitHub : depot site, Settings, Pages, Source = GitHub Actions.
echo  Ensuite, pour chaque modification : 4 - Publier.bat
pause
exit /b 0
:erreur
echo.
echo  ** Ca n a pas marche : rien n a ete publie. Envoie la fenetre a Claude. **
pause
exit /b 1
