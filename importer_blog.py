# -*- coding: utf-8 -*-
"""
importer_blog.py — Copie l'export WordPress (blog/export/) dans le site.

  · billets : blog/export/billets/*.md  →  contenu/blog/*.md   (chemins d'images réécrits vers /images/uploads/)
  · images  : blog/export/images/**     →  images/uploads/**   (photos réduites à 1600 px de large au plus, PDF copiés tels quels)

    python importer_blog.py                      # export attendu dans ../blog/export
    python importer_blog.py --export CHEMIN      # autre dossier d'export
    python importer_blog.py --sans-images        # billets seulement (rapide)
    python importer_blog.py --forcer             # refaire toutes les images même si déjà présentes

Relancer après un nouvel export : seuls les fichiers nouveaux ou modifiés sont retraités.
Les billets déjà présents dans contenu/blog sont remplacés ; pour retoucher un billet, modifier son .md
dans contenu/blog ET ne plus relancer l'import sans l'option --garder (qui ne remplace pas les billets existants).
"""
import argparse, re, shutil, sys, urllib.parse
from pathlib import Path

ICI = Path(__file__).resolve().parent
MAX_COTE = 1600
QUALITE_JPEG = 82
EXT_IMAGES = {".jpg", ".jpeg", ".png", ".webp"}


def reecrire_chemins(txt):
    txt = txt.replace("](../images/", "](/images/uploads/")
    txt = txt.replace('image_une: "../images/', 'image_une: "/images/uploads/')
    txt = re.sub(r'src="\.\./images/', 'src="/images/uploads/', txt)
    return txt


def importer_billets(export, garder=False):
    src = export / "billets"
    dest = ICI / "contenu" / "blog"
    dest.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(src.glob("*.md")):
        cible = dest / f.name
        if garder and cible.exists():
            continue
        cible.write_text(reecrire_chemins(f.read_text(encoding="utf-8")), encoding="utf-8")
        n += 1
    print(f"Billets : {n} copiés dans contenu/blog/")


def reduire_image(src, dest):
    from PIL import Image, ImageOps
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        fmt = (im.format or "").upper()
        if max(im.size) > MAX_COTE:
            im.thumbnail((MAX_COTE, MAX_COTE), Image.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix.lower() in (".jpg", ".jpeg") or fmt == "JPEG":
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            im.save(dest, "JPEG", quality=QUALITE_JPEG, optimize=True, progressive=True)
        elif src.suffix.lower() == ".png":
            im.save(dest, "PNG", optimize=True)
        elif src.suffix.lower() == ".webp":
            im.save(dest, "WEBP", quality=QUALITE_JPEG)
        else:
            shutil.copy2(src, dest)


def importer_images(export, forcer=False):
    src = export / "images"
    dest = ICI / "images" / "uploads"
    if not src.exists():
        print("Pas de dossier images dans l'export.")
        return
    try:
        import PIL  # noqa
    except ImportError:
        print("Pillow manque : pip install pillow   (les images sont copiées sans réduction)")
        PIL = None
    n = 0; ignores = 0; octets_avant = 0; octets_apres = 0
    for f in sorted(src.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(src)
        # noms encodés (%C3%A9…) : le navigateur demande le nom décodé → on enregistre décodé
        if "%" in f.name:
            decode = urllib.parse.unquote(f.name)
            if (f.parent / decode).exists():
                continue  # le même fichier existe déjà sous son vrai nom
            rel = rel.parent / decode
        cible = dest / rel
        if cible.exists() and not forcer and cible.stat().st_mtime >= f.stat().st_mtime:
            ignores += 1
            continue
        cible.parent.mkdir(parents=True, exist_ok=True)
        octets_avant += f.stat().st_size
        try:
            if f.suffix.lower() in EXT_IMAGES and PIL is not None:
                reduire_image(f, cible)
            else:
                shutil.copy2(f, cible)
        except Exception as e:  # image illisible : copie brute
            print(f"  ! {rel} : {e} → copie sans réduction")
            shutil.copy2(f, cible)
        octets_apres += cible.stat().st_size
        n += 1
        if n % 50 == 0:
            print(f"  … {n} fichiers")
    print(f"Images : {n} traitées ({octets_avant/1e6:.0f} Mo → {octets_apres/1e6:.0f} Mo), {ignores} déjà à jour, dans images/uploads/")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", default=str(ICI.parent / "blog" / "export"))
    ap.add_argument("--sans-images", action="store_true")
    ap.add_argument("--forcer", action="store_true")
    ap.add_argument("--garder", action="store_true", help="ne pas remplacer les billets déjà présents")
    a = ap.parse_args()
    export = Path(a.export)
    if not (export / "billets").exists():
        sys.exit(f"Export introuvable : {export}  (lancer d'abord blog/Exporter le blog.bat)")
    importer_billets(export, garder=a.garder)
    if not a.sans_images:
        importer_images(export, forcer=a.forcer)
