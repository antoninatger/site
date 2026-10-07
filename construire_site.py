# -*- coding: utf-8 -*-
"""
construire_site.py — Construit le site antoninatger.com dans `_site/`.

Entrées (tout est du texte, versionné) :
  · site.yaml                     réglages, menu, pied de page, formulaires
  · contenu/pages/*.md            les pages (accueil, contact, formations, jeux, livres…)
  · contenu/interventions/*.md    une fiche par intervention
  · contenu/blog/*.md             les billets (importés depuis WordPress par importer_blog.py)
  · contenu/categories.yaml       correspondance anciennes → nouvelles catégories
  · contenu/references.yaml       « Ils m'ont fait confiance », témoignages, références
  · contenu/redirections.yaml     anciennes adresses WordPress → nouvelles
  · contenu/themes.yaml           thèmes des chroniques (page /chroniques/)
  · contenu/ecrits.yaml           page « Nouvelles et poèmes » (/ecrits/)
  · contenu/retours.yaml          retours d'intervention choisis dans Retours.xlsx (extraire_retours.py)
  · gabarits/*.html               les gabarits Jinja2
  · static/, images/              copiés tels quels

Sortie : `_site/` — à servir tel quel (GitHub Pages, ou `python -m http.server` en local).

    python construire_site.py
    python construire_site.py --verifier     # + contrôle des liens internes

Dépendances : pip install -r requirements.txt  (markdown, jinja2, pyyaml)
"""
import argparse, datetime, html, json, math, re, shutil, sys, unicodedata
from pathlib import Path

import markdown, yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ICI = Path(__file__).resolve().parent
SORTIE = ICI / "_site"
CONF = yaml.safe_load((ICI / "site.yaml").read_text(encoding="utf-8"))
MD_EXT = ["extra", "sane_lists", "smarty", "toc"]
MD_CFG = {"smarty": {"smart_dashes": False, "substitutions": {"left-double-quote": "«&nbsp;", "right-double-quote": "&nbsp;»"}}}
RE_FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
RE_YT = re.compile(r"\{youtube:\s*([A-Za-z0-9_-]{6,})(?:\s*\|\s*([^}]*))?\}")
RE_YT_MD = re.compile(r"\[Vidéo / contenu intégré\]\(https?://(?:www\.)?youtube(?:-nocookie)?\.com/embed/([A-Za-z0-9_-]{6,})[^)]*\)")
RE_EMBED_MD = re.compile(r"\[Vidéo / contenu intégré\]\(([^)]+)\)")
RE_PLEIN_ECRAN = re.compile(r"^\s*⛶\s*(Plein écran|Full screen)\s*$", re.M)
# iframes de l'ancien site qui pointaient vers des pages désormais intégrées au site
EMBED_VERS_PAGE = {
    "Bibliographie/interventions.html": "/interventions/", "Bibliographie/publication.html": "/livres/",
    "Bibliographie/collaborations.html": "/presse-et-medias/", "Bibliographie/couverture-mediatique.html": "/presse-et-medias/",
    "Bibliographie/cv.html": "/a-propos/", "antoninatger.com/jeux-pedagogiques": "/jeux/",
}
EMBED_CADRE = ("antoninatger.github.io/", "jeux.antoninatger.com/", "dailymotion.com/", "videopress.com/")


# ---------------------------------------------------------------- utilitaires

def slugifier(s):
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "sans-titre"


def lire_md(chemin):
    """→ (métadonnées, corps markdown)."""
    txt = chemin.read_text(encoding="utf-8")
    m = RE_FRONT.match(txt)
    meta = yaml.safe_load(m.group(1)) if m else {}
    corps = txt[m.end():] if m else txt
    return (meta or {}), corps


def youtube_html(vid, titre=""):
    titre = html.escape(titre or "Vidéo")
    return (f'<div class="video" data-id="{vid}"><a class="video-lien" href="https://www.youtube.com/watch?v={vid}" '
            f'target="_blank" rel="noopener" aria-label="Lire la vidéo : {titre}">'
            f'<img loading="lazy" src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="{titre}">'
            f'<span class="video-play" aria-hidden="true"></span></a></div>')


def embed_html(url):
    """Iframe de l'ancien site (hors YouTube) : cadre pour les jeux et vidéos, lien vers la page pour le reste."""
    for cle, page in EMBED_VERS_PAGE.items():
        if cle in url:
            return f'<p><a href="{page}">Voir la page {page}</a></p>'
    if any(h in url for h in EMBED_CADRE):
        u = html.escape(url)
        return (f'<div class="cadre-wrap"><iframe class="cadre" src="{u}" loading="lazy" allowfullscreen title="Contenu intégré"></iframe>'
                f'<p class="small"><a href="{u}" target="_blank" rel="noopener">Ouvrir en plein écran ↗</a></p></div>')
    return f'<p><a href="{html.escape(url)}" target="_blank" rel="noopener">Contenu intégré ↗</a></p>'


def rendre_md(corps):
    corps = RE_YT.sub(lambda m: youtube_html(m.group(1), (m.group(2) or "").strip()), corps)
    corps = RE_YT_MD.sub(lambda m: youtube_html(m.group(1)), corps)
    corps = RE_EMBED_MD.sub(lambda m: embed_html(m.group(1)), corps)
    corps = RE_PLEIN_ECRAN.sub("", corps)
    md = markdown.Markdown(extensions=MD_EXT, extension_configs=MD_CFG, output_format="html5")
    return md.convert(corps)


def extrait_de(html_txt, n=200):
    t = re.sub(r"<[^>]+>", " ", html_txt)
    t = html.unescape(re.sub(r"\s+", " ", t)).strip()
    return t if len(t) <= n else t[: n].rsplit(" ", 1)[0] + "…"


def date_fr(d):
    if isinstance(d, str):
        d = datetime.datetime.fromisoformat(d[:19])
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    return f"{d.day} {mois[d.month - 1]} {d.year}"


def ecrire(chemin_url, contenu):
    """/a/b/ → _site/a/b/index.html ; /x.xml → _site/x.xml"""
    if chemin_url.endswith("/"):
        dest = SORTIE / chemin_url.strip("/") / "index.html"
    else:
        dest = SORTIE / chemin_url.lstrip("/")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(contenu, encoding="utf-8")


# ---------------------------------------------------------------- chargement

def charger_pages():
    pages = {}
    for f in sorted((ICI / "contenu/pages").glob("*.md")):
        meta, corps = lire_md(f)
        meta.setdefault("slug", f.stem)
        meta.setdefault("url", "/" if f.stem == "accueil" else f"/{meta['slug']}/")
        meta["html"] = rendre_md(corps)
        meta.setdefault("gabarit", "page.html")
        meta.setdefault("description", extrait_de(meta["html"], 160))
        pages[f.stem] = meta
    return pages


# ── Filtres de la page Interventions (27 septembre 2026) ──────────────────────
# Âge, cadre, durée et mode sont DÉDUITS des champs déjà écrits dans chaque fiche
# (publics, duree, distance). Une fiche peut les imposer elle-même, en clair :
#   ages: [primaire, college, lycee, superieur, adultes]
#   cadre: [scolaire, hors-scolaire]
#   formats: [1h, 2h]
#   presentiel: false        (intervention uniquement à distance)
AGES = ["primaire", "college", "lycee", "superieur", "adultes"]
_ADULTES = ("adulte", "parent", "famille", "senior", "enseignant", "cpe", "documentaliste", "formateur",
            "entreprise", "collectivite", "professionnel", "encadrant", "grand public", "teacher", "professional")


def _sans_accents(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", str(s).lower()) if unicodedata.category(c) != "Mn")


def _ages_de(public):
    p = _sans_accents(public)
    trouves = []
    if re.search(r"\bcm[12]\b|primaire|\becole\b", p): trouves.append("primaire")
    if "college" in p: trouves.append("college")
    if re.search(r"lycee|\b2de\b|\bbts\b", p): trouves.append("lycee")
    if re.search(r"superieur|student|etudiant|\bbts\b", p): trouves.append("superieur")
    if any(m in p for m in _ADULTES): trouves.append("adultes")
    if "etablissements scolaires" in p or "schools" in p: trouves += ["college", "lycee"]
    # « CM1 → lycée » : tout ce qu'il y a entre les deux bouts.
    if "→" in p and len(trouves) >= 2:
        rangs = sorted(AGES.index(a) for a in trouves)
        trouves = AGES[rangs[0]:rangs[-1] + 1]
    return trouves


def facettes(meta):
    publics = meta.get("publics") or []
    ages = meta.get("ages")
    if not ages:
        ages = []
        for pub in publics:
            ages += [a for a in _ages_de(pub) if a not in ages]
    ages = [a for a in AGES if a in ages]
    cadre = meta.get("cadre")
    if not cadre:
        texte = _sans_accents(" ".join(map(str, publics)))
        cadre = []
        if any(a in ages for a in ("primaire", "college", "lycee")) or "scolaire" in texte or "enseignant" in texte:
            cadre.append("scolaire")
        if "adultes" in ages or "superieur" in ages or re.search(r"mediath|entreprise|collectivit|parent|famille|senior|grand public", texte):
            cadre.append("hors-scolaire")
    formats = meta.get("formats")
    if not formats:
        d = _sans_accents(meta.get("duree", ""))
        minutes = []
        for h, m in re.findall(r"(\d+)\s*h(?:\s*(\d+))?", d):
            minutes.append(int(h) * 60 + int(m or 0))
        minutes += [int(m) for m in re.findall(r"(\d+)\s*min", d)]
        formats = []
        if any(x <= 75 for x in minutes): formats.append("1h")
        if any(x >= 90 for x in minutes) or "demi-journee" in d: formats.append("2h")
    modes = []
    if meta.get("presentiel", True) is not False: modes.append("presentiel")
    if meta.get("distance"): modes.append("distanciel")
    return {"ages": ages, "cadre": cadre, "formats": formats, "modes": modes}


def charger_interventions():
    fiches = []
    for f in sorted((ICI / "contenu/interventions").glob("*.md")):
        meta, corps = lire_md(f)
        meta.setdefault("slug", f.stem)
        meta["url"] = f"/interventions/{meta['slug']}/"
        meta["html"] = rendre_md(corps)
        meta.setdefault("ordre", 99)
        meta.setdefault("description", meta.get("sous_titre") or extrait_de(meta["html"], 160))
        meta["facettes"] = facettes(meta)
        fiches.append(meta)
    fiches.sort(key=lambda m: (m["ordre"], m["titre"]))
    return fiches


def charger_categories():
    p = ICI / CONF["blog"]["categories_fichier"]
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {"correspondance": {}, "surcharges": {}, "categories": {}}


def _maintenant_paris():
    """Heure de Paris, sans fuseau (les dates des billets sont écrites ainsi)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("Europe/Paris")).replace(tzinfo=None)
    except Exception:
        return datetime.datetime.now()


def charger_billets(cats):
    corr = cats.get("correspondance", {})
    surch = cats.get("surcharges", {}) or {}
    defaut = cats.get("par_defaut", "Esprit critique")
    billets = []
    for f in sorted((ICI / "contenu/blog").glob("*.md")):
        meta, corps = lire_md(f)
        if meta.get("brouillon"):
            continue
        d = meta.get("date")
        if isinstance(d, (datetime.date, datetime.datetime)):
            dt = d if isinstance(d, datetime.datetime) else datetime.datetime(d.year, d.month, d.day)
        else:
            dt = datetime.datetime.fromisoformat(str(d)[:19])
        if dt > _maintenant_paris():    # billet programmé (Séquenceur) : il attend sa date
            continue
        meta["dt"] = dt
        meta["date_fr"] = date_fr(dt)
        if not meta.get("slug"):   # absent ou vide (article créé dans le back-office) : on le tire du nom du fichier
            meta["slug"] = f.stem[11:] if re.match(r"\d{4}-\d{2}-\d{2}-", f.stem) else f.stem
        meta["url"] = f"/{dt:%Y/%m/%d}/{meta['slug']}/"
        # catégories : surcharge par slug, sinon correspondance, sinon défaut
        if meta["slug"] in surch:
            nouvelles = surch[meta["slug"]]
        else:
            nouvelles = []
            for c in meta.get("categories") or []:
                n = corr.get(c, c)
                if n and n not in nouvelles:
                    nouvelles.append(n)
            nouvelles = [c for c in nouvelles if c]
        meta["categories"] = nouvelles or [defaut]
        meta["html"] = rendre_md(corps)
        meta.setdefault("extrait", "")
        if not meta["extrait"]:
            meta["extrait"] = extrait_de(meta["html"], 220)
        meta["image_une"] = normaliser_image(meta.get("image_une") or "")
        # vignette (accueil) : l'image à la une, sinon la première image du billet
        m_img = re.search(r'<img[^>]+src="([^"]+)"', meta["html"])
        meta["vignette"] = meta["image_une"] or (normaliser_image(m_img.group(1)) if m_img else "")
        billets.append(meta)
    billets.sort(key=lambda m: m["dt"], reverse=True)
    return billets


def texte_en_html(t):
    """Texte brut d'un commentaire → paragraphes HTML (échappés : aucun balisage des visiteurs ne passe)."""
    blocs = [b.strip() for b in re.split(r"\n\s*\n|\n", str(t or "").strip()) if b.strip()]
    return "".join("<p>" + html.escape(b) + "</p>" for b in blocs)


def attacher_commentaires(billets):
    """Commentaires sous chaque billet : ceux de l'ancien WordPress (par id_wordpress) puis ceux
    validés dans contenu/commentaires.yaml (par slug), dans l'ordre chronologique."""
    ancien = ICI / "contenu/commentaires_wordpress.json"
    nouveaux = ICI / "contenu/commentaires.yaml"
    wp = json.loads(ancien.read_text(encoding="utf-8")) if ancien.exists() else {}
    conf = (yaml.safe_load(nouveaux.read_text(encoding="utf-8")) or {}) if nouveaux.exists() else {}
    serveur = ICI / "contenu/commentaires.json"          # écrit par le serveur (bouton « Publier » du mail, page de modération)
    publies = json.loads(serveur.read_text(encoding="utf-8")) if serveur.exists() else {}
    masques = {str(m) for m in (conf.get("masques") or [])} | {str(m.get("cle")) for m in (publies.get("masques") or [])}
    par_slug = {}
    for c in (conf.get("commentaires") or []) + [dict(c, id=c.get("id")) for c in (publies.get("publies") or [])]:
        par_slug.setdefault(str(c.get("billet", "")).strip("/"), []).append(c)
    for b in billets:
        liste = []
        for c in wp.get(str(b.get("id_wordpress", "")), []):
            cle = "wp-" + str(c.get("date", ""))
            if c.get("type", "comment") != "comment" or str(c.get("date")) in masques or cle in masques:
                continue
            liste.append({"cle": cle, "texte": str(c.get("contenu") or ""), "nom": c.get("auteur") or "Anonyme", "dt": str(c.get("date", "")), "html": texte_en_html(c.get("contenu")),
                          "reponse": bool(c.get("en_reponse_a")), "auteur_site": (c.get("auteur") or "").strip() == "Antonin Atger"})
        for c in par_slug.get(b["slug"], []):
            d = str(c.get("date", ""))
            cle = str(c.get("id") or ("site-" + d + "-" + str(c.get("nom", ""))))
            if cle in masques:
                continue
            liste.append({"cle": cle, "texte": str(c.get("texte") or ""), "nom": c.get("nom") or "Anonyme", "dt": d, "html": texte_en_html(c.get("texte")), "reponse": False, "auteur_site": False})
            if c.get("reponse"):
                liste.append({"cle": cle + "-reponse", "texte": str(c.get("reponse") or ""), "nom": "Antonin Atger", "dt": d + "~", "html": texte_en_html(c.get("reponse")), "reponse": True, "auteur_site": True})
        liste.sort(key=lambda c: c["dt"])
        for c in liste:
            try:
                c["date_fr"] = date_fr(c["dt"].rstrip("~")[:10])
            except ValueError:
                c["date_fr"] = ""
        b["commentaires"] = liste


def copier_dossier(src, dst):
    """Copie `src` dans `dst` en sautant les fichiers déjà présents et identiques
    (même taille, pas plus anciens) : une reconstruction ne recopie que le neuf."""
    import os
    for racine, _, fichiers in os.walk(src):
        cible = Path(dst) / Path(racine).relative_to(src)
        cible.mkdir(parents=True, exist_ok=True)
        for nom in fichiers:
            a, b = Path(racine) / nom, cible / nom
            try:
                sa, sb = a.stat(), b.stat()
                if sa.st_size == sb.st_size and sb.st_mtime >= sa.st_mtime - 1:
                    continue
            except FileNotFoundError:
                pass
            shutil.copy2(a, b)


GALERIE_DEPOT = ICI / "galerie-a-ajouter"
GALERIE_IMG = ICI / "images" / "galerie"
GALERIE_YAML = ICI / "contenu" / "galerie.yaml"


def preparer_galerie():
    """Photos déposées dans galerie-a-ajouter/ : réduites dans images/galerie/ (grande + vignette)
    et inscrites en tête de contenu/galerie.yaml avec une légende vide (donc pas encore affichées)."""
    if not GALERIE_DEPOT.is_dir():
        return
    photos = sorted(p for p in GALERIE_DEPOT.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
    a_faire = [p for p in photos if not (GALERIE_IMG / f"{slugifier(p.stem) or 'photo'}.jpg").exists()]
    if not a_faire:
        return
    try:
        from PIL import Image, ImageOps
    except ImportError:
        print("Galerie : Pillow n'est pas installé, lancez « 0 - Installer » puis reconstruisez.")
        return
    GALERIE_IMG.mkdir(parents=True, exist_ok=True)
    nouvelles = []
    for p in a_faire:
        nom = slugifier(p.stem) or "photo"
        try:
            im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
        except Exception as e:
            print(f"Galerie : {p.name} illisible ({e}).")
            continue
        for suffixe, larg in (("", 1600), ("-vignette", 720)):
            c = im.copy()
            c.thumbnail((larg, larg * 2), Image.LANCZOS)
            c.save(GALERIE_IMG / f"{nom}{suffixe}.jpg", quality=80, optimize=True, progressive=True)
        nouvelles.append(nom)
    if not nouvelles:
        return
    texte = GALERIE_YAML.read_text(encoding="utf-8") if GALERIE_YAML.exists() else "photos:\n"
    bloc = "".join(f'  - fichier: {n}\n    legende: ""\n    credit: ""\n' for n in nouvelles)
    if re.search(r"^photos:[ \t]*(\[\])?[ \t]*$", texte, re.M):
        texte = re.sub(r"^photos:[ \t]*(\[\])?[ \t]*\n?", "photos:\n" + bloc, texte, count=1, flags=re.M)
    else:
        texte += "\nphotos:\n" + bloc
    GALERIE_YAML.write_text(texte, encoding="utf-8", newline="")
    print(f"Galerie : {len(nouvelles)} photo(s) ajoutée(s). Écrivez leur légende dans contenu/galerie.yaml ; "
          "elles restent cachées en attendant.")


def charger_galerie():
    if not GALERIE_YAML.exists():
        return []
    photos = (yaml.safe_load(GALERIE_YAML.read_text(encoding="utf-8")) or {}).get("photos") or []
    ok, sans = [], 0
    for p in photos:
        if not p or not p.get("fichier"):
            continue
        if not str(p.get("legende") or "").strip():
            sans += 1
            continue
        if not (GALERIE_IMG / f"{p['fichier']}.jpg").exists():
            print(f"Galerie : image introuvable pour « {p['fichier']} ».")
            continue
        ok.append(p)
    if sans:
        print(f"Galerie : {sans} photo(s) sans légende, non affichée(s) (contenu/galerie.yaml).")
    return ok


def normaliser_image(src):
    if not src:
        return ""
    src = src.replace("../images/", "/images/uploads/")
    return src


# ---------------------------------------------------------------- construction

def construire(verifier=False):
    if SORTIE.exists():
        try:
            shutil.rmtree(SORTIE)
        except PermissionError:
            print("(_site/ ne peut pas être vidé ici : les fichiers sont réécrits par-dessus)")
    SORTIE.mkdir(exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(ICI / "gabarits")), autoescape=select_autoescape(["html", "xml"]), trim_blocks=True, lstrip_blocks=True)
    env.filters["date_fr"] = date_fr
    env.filters["slug"] = slugifier
    env.globals["site"] = CONF
    env.globals["annee"] = datetime.date.today().year
    env.globals["youtube"] = lambda vid, titre="": youtube_html(vid, titre)

    preparer_galerie()
    pages = charger_pages()
    fiches = charger_interventions()
    cats = charger_categories()
    billets = charger_billets(cats)
    refs = yaml.safe_load((ICI / "contenu/references.yaml").read_text(encoding="utf-8"))
    redirs = yaml.safe_load((ICI / "contenu/redirections.yaml").read_text(encoding="utf-8")) or {}
    # Retours d'intervention : relus dans Retours.xlsx quand il est là (sur le PC),
    # sinon on garde le retours.yaml déjà publié (sur GitHub).
    try:
        import extraire_retours
        extraire_retours.mettre_a_jour()
    except Exception as e:
        print(f"Retours : non mis à jour ({e}).")
    f_retours = ICI / "contenu/retours.yaml"
    retours = (yaml.safe_load(f_retours.read_text(encoding="utf-8")) or {}).get("retours", []) if f_retours.exists() else []

    # catégories du blog : nom → {slug, description, billets}
    categories = {}
    for nom, info in (cats.get("categories") or {}).items():
        categories[nom] = {"nom": nom, "slug": info.get("slug") or slugifier(nom), "description": info.get("description", ""), "billets": [], "ordre": info.get("ordre", 99), "pilier": info.get("pilier", "")}
    for b in billets:
        for c in b["categories"]:
            categories.setdefault(c, {"nom": c, "slug": slugifier(c), "description": "", "billets": [], "ordre": 99})
            categories[c]["billets"].append(b)
    for c in categories.values():
        c["url"] = f"/blog/{c['slug']}/"
    cats_ordonnees = sorted(categories.values(), key=lambda c: (c["ordre"], c["nom"]))
    env.globals["categories"] = cats_ordonnees
    env.globals["interventions"] = fiches
    env.globals["pages"] = pages
    env.globals["refs"] = refs
    env.globals["retours"] = retours
    # vrai si le fichier existe dans le site (ex. image pas encore rapatriée → on ne l'affiche pas)
    env.tests["existe"] = lambda chemin: bool(chemin) and ((ICI / chemin.lstrip("/")).exists() or (ICI / "static" / chemin.lstrip("/")).exists())
    env.globals["existe"] = lambda chemin: bool(chemin) and ((ICI / chemin.lstrip("/")).exists() or (ICI / "static" / chemin.lstrip("/")).exists())
    env.globals["derniers_billets"] = billets[:4]

    # chroniques : thèmes (contenu/themes.yaml + « themes: » dans l'en-tête d'un billet)
    f_themes = ICI / "contenu/themes.yaml"
    th = yaml.safe_load(f_themes.read_text(encoding="utf-8")) if f_themes.exists() else {}
    defs, classement = th.get("themes") or {}, th.get("billets") or {}
    for b in billets:
        cles = list(b.get("themes") or []) + list(classement.get(b["slug"], []))
        vus = []
        for k in cles:
            if k in defs and k not in vus: vus.append(k)
        b["themes"] = [{"cle": k, "nom": defs[k]["nom"], "description": defs[k].get("description", "")} for k in vus]
        b["annee"] = b["dt"].year
    chroniques = [b for b in billets if b["themes"]]
    themes_liste = [{"cle": k, "nom": d["nom"], "description": d.get("description", ""),
                     "nombre": sum(1 for b in chroniques if any(t["cle"] == k for t in b["themes"]))} for k, d in defs.items()]
    env.globals["themes_liste"] = themes_liste

    # page « Nouvelles et poèmes »
    f_ecrits = ICI / "contenu/ecrits.yaml"
    par_slug = {b["slug"]: b for b in billets}
    ecrits = []
    for g in (yaml.safe_load(f_ecrits.read_text(encoding="utf-8")) or {}).get("groupes", []) if f_ecrits.exists() else []:
        elements = []
        for nom in g.get("pages") or []:
            p = pages.get(nom)
            if p: elements.append({"titre": p.get("titre", nom), "url": p["url"], "date": "", "extrait": p.get("description", "")})
        for s in g.get("billets") or []:
            b = par_slug.get(s)
            if b: elements.append({"titre": b["titre"], "url": b["url"], "date": b["date_fr"], "extrait": b["extrait"]})
            else: print(f"Nouvelles et poèmes : billet introuvable « {s} » (contenu/ecrits.yaml)")
        ecrits.append({**g, "elements": elements})

    def rendre(gabarit, url, **ctx):
        ctx.setdefault("url", url)
        ctx.setdefault("canonique", CONF["url"].rstrip("/") + url)
        ecrire(url, env.get_template(gabarit).render(**ctx))

    # pages
    for nom, p in pages.items():
        rendre(p["gabarit"], p["url"], page=p, titre=p.get("titre", ""), description=p.get("description", ""), image=p.get("image"))
    # interventions
    rendre("interventions.html", "/interventions/", titre="Interventions", description="Conférences et ateliers d'esprit critique, du CM1 au lycée, en médiathèque, en centre social et en entreprise.", fiches=fiches, galerie=charger_galerie())
    for i, f in enumerate(fiches):
        autres = [x for x in fiches if x is not f and not x.get("hors_catalogue")][:3]
        rendre("intervention.html", f["url"], page=f, titre=f["titre"], description=f["description"], image=f.get("image") or f.get("visuel"), autres=autres)
    # blog : liste paginée, catégories, billets
    par_page = int(CONF["blog"].get("par_page", 12))
    def paginer(liste, base, gabarit, **ctx):
        n = max(1, math.ceil(len(liste) / par_page))
        for p in range(1, n + 1):
            url = base if p == 1 else f"{base}page/{p}/"
            rendre(gabarit, url, billets=liste[(p - 1) * par_page: p * par_page], page_num=p, pages_total=n, base=base, **ctx)
    paginer(billets, "/blog/", "blog.html", titre="Blog", description="Analyses, actualités des interventions, conseils d'écriture et textes d'Antonin Atger.")
    for c in cats_ordonnees:
        paginer(c["billets"], c["url"], "blog.html", titre=c["nom"], description=c["description"] or f"Les billets de la catégorie {c['nom']}.", categorie=c)
    rendre("chroniques.html", "/chroniques/", titre="Chroniques de l'actualité",
           description="Complotisme, rhétorique, désinformation, réseaux sociaux : les chroniques d'Antonin Atger, classées par thème.",
           chroniques=chroniques)
    rendre("ecrits.html", "/ecrits/", titre="Nouvelles et poèmes",
           description="Les nouvelles, poèmes et textes d'Antonin Atger publiés depuis 2012, dont les Nouvelles du confinement.",
           ecrits=ecrits)
    attacher_commentaires(billets)
    for i, b in enumerate(billets):
        precedent = billets[i + 1] if i + 1 < len(billets) else None
        suivant = billets[i - 1] if i > 0 else None
        cats_b = [categories[c] for c in b["categories"] if c in categories]
        rendre("billet.html", b["url"], page=b, titre=b["titre"], description=b["extrait"][:160], image=b["image_une"], precedent=precedent, suivant=suivant, cats=cats_b)
    # flux, plan, robots, 404, redirections, CNAME
    ecrire("/feed.xml", env.get_template("feed.xml").render(billets=billets[:20], maj=datetime.datetime.now()))
    urls = ["/", "/interventions/", "/blog/", "/chroniques/", "/ecrits/"] + [p["url"] for p in pages.values() if p["url"] != "/"] + [f["url"] for f in fiches] + [c["url"] for c in cats_ordonnees] + [b["url"] for b in billets]
    ecrire("/sitemap.xml", env.get_template("sitemap.xml").render(urls=urls))
    ecrire("/robots.txt", f"User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: {CONF['url']}/sitemap.xml\n")
    # index des commentaires affichés (pour la page de modération du serveur), les plus récents d'abord
    index = [{"cle": c["cle"], "titre": b["titre"], "url": b["url"], "nom": c["nom"], "date_fr": c.get("date_fr", ""), "dt": c["dt"],
              "extrait": (c["texte"][:140] + "…") if len(c["texte"]) > 140 else c["texte"]} for b in billets for c in b.get("commentaires", [])]
    index.sort(key=lambda c: c["dt"], reverse=True)
    ecrire("/commentaires-index.json", json.dumps(index, ensure_ascii=False))
    # back-office : /admin/ (Decap CMS), réglé par site.yaml → admin → serveur
    themes_bo = (yaml.safe_load((ICI / "contenu/themes.yaml").read_text(encoding="utf-8")) or {}).get("themes", {})
    simples = [{"nom": n, "titre": p.get("titre", n)} for n, p in sorted((p["slug"], p) for p in pages.values())
               if n not in ("accueil", "livres")]
    ecrire("/admin/config.yml", env.get_template("admin-config.yml").render(site=CONF, themes=themes_bo, pages_simples=simples))
    ecrire("/admin/", env.get_template("admin.html").render(site=CONF))
    (SORTIE / "404.html").write_text(env.get_template("404.html").render(titre="Page introuvable", url="/404.html", canonique=CONF["url"] + "/404.html"), encoding="utf-8")
    for ancienne, nouvelle in redirs.items():
        ecrire(ancienne if ancienne.endswith("/") else ancienne + "/", env.get_template("redirection.html").render(vers=nouvelle))
    if (ICI / "CNAME").exists():
        shutil.copy(ICI / "CNAME", SORTIE / "CNAME")
    (SORTIE / ".nojekyll").write_text("")
    # fichiers statiques
    copier_dossier(ICI / "static", SORTIE / "static")
    if (ICI / "images").exists():
        copier_dossier(ICI / "images", SORTIE / "images")

    n_html = sum(1 for _ in SORTIE.rglob("*.html"))
    print(f"Site construit : {n_html} pages HTML, {len(billets)} billets, {len(fiches)} interventions, {len(cats_ordonnees)} catégories → {SORTIE}")
    if verifier:
        verifier_liens()


def verifier_liens():
    """Chaque lien interne doit mener à un fichier de _site/."""
    import urllib.parse
    casses, images = {}, {}
    for f in SORTIE.rglob("*.html"):
        s = f.read_text(encoding="utf-8")
        for h in re.findall(r'(?:href|src)="(/[^"#?]*)', s):
            if h.startswith("//"):
                continue
            chemin = urllib.parse.unquote(h)
            cible = SORTIE / chemin.lstrip("/")
            if chemin.endswith("/"):
                cible = cible / "index.html"
            if not cible.exists() and not (cible.with_suffix("") / "index.html").exists():
                (images if chemin.startswith("/images/") else casses).setdefault(h, []).append(str(f.relative_to(SORTIE)))
    if images:
        print(f"\n{len(images)} image(s) manquante(s) sous /images/ (lancer « 1 - Importer le blog.bat » ; sinon, fichier absent de l'export) :")
        for h, pages in sorted(images.items())[:15]:
            print(f"  {h}   ← {pages[0]}")
        if len(images) > 15:
            print(f"  … et {len(images) - 15} autres")
    if casses:
        print(f"\n{len(casses)} lien(s) interne(s) cassé(s) :")
        for h, pages in sorted(casses.items()):
            print(f"  {h}   ← {pages[0]}" + (f" (+{len(pages) - 1})" if len(pages) > 1 else ""))
    else:
        print("Liens internes (hors images) : tous valides.")
    return casses


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verifier", action="store_true")
    a = ap.parse_args()
    construire(verifier=a.verifier)
