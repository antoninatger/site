# -*- coding: utf-8 -*-
"""
synchroniser_confiance.py — Ajoute au site les nouvelles interventions du Hub.

Le Hub reste privé : il écrit seulement Interventions-site.json (dossier « Web apps »,
à côté de Retours.xlsx), qui ne contient que ce que le site a le droit de montrer :

    {"interventions": [
        {"id": "2026-10-28-lycee-x", "etablissement": "Lycée X",
         "type": "etablissement", "seances": 2, "date": "2026-10-28"},
        ...
    ]}

  · id        identifiant stable de l'intervention dans le Hub (sinon date + établissement)
  · type      etablissement (école, collège, lycée…), mediatheque (bibliothèque comprise)
              ou autre (collectivité, entreprise, événement) ; deviné d'après le nom s'il manque
  · seances   nombre de séances données ce jour-là (1 par défaut)
  · date      AAAA-MM-JJ ; une intervention n'est comptée qu'une fois sa date passée

Ce script met à jour contenu/confiance.yaml : le nom de l'établissement entre dans la
liste « Ils m'ont fait confiance » (s'il n'y est pas déjà) et le compteur d'interventions
augmente du nombre de séances. Chaque intervention n'est comptée qu'une fois : son
empreinte (un code illisible) est gardée dans `deja_comptees`.

Premier passage (deja_comptees vide) : les interventions déjà passées sont seulement
notées, sans toucher au compteur, qui les inclut déjà. Les noms manquants sont ajoutés.

Lancé automatiquement à chaque construction du site, quand le fichier est accessible
(donc sur le PC ; sur GitHub, c'est le confiance.yaml déjà publié qui sert).

    python synchroniser_confiance.py      # met à jour contenu/confiance.yaml et dit ce qui a changé
"""
import datetime, hashlib, json, re, sys, unicodedata
from pathlib import Path

ICI = Path(__file__).resolve().parent
SOURCE = ICI.parent.parent / "Interventions-site.json"     # Web apps/Interventions-site.json
FICHIER = ICI / "contenu" / "confiance.yaml"


def _cle(nom):
    """Compare deux noms sans tenir compte des accents, majuscules, tirets ni apostrophes."""
    s = unicodedata.normalize("NFD", str(nom or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _type(nom, donne):
    t = _cle(donne)
    if t.startswith("media") or t.startswith("biblio"):
        return "mediatheques"
    if t.startswith("etab") or t in ("ecole", "college", "lycee", "scolaire"):
        return "etablissements"
    if t:
        return "autres"
    n = _cle(nom)
    if re.search(r"\b(mediatheque|bibliotheque|ludotheque)\b", n):
        return "mediatheques"
    if re.search(r"\b(ecole|college|lycee|erea|lp|cfa|ensemble scolaire|institution|groupe scolaire)\b", n):
        return "etablissements"
    return "autres"


def _empreinte(i):
    ident = str(i.get("id") or f"{i.get('date', '')}|{i.get('etablissement', '')}")
    return hashlib.sha256(ident.encode("utf-8")).hexdigest()[:12]


def _seances(v):
    try:
        return max(1, int(v))
    except (TypeError, ValueError):
        return 1


def synchroniser(donnees, conf, aujourd_hui=None):
    """Applique l'export du Hub à conf (dict de confiance.yaml). → liste des changements."""
    aujourd_hui = aujourd_hui or datetime.date.today().isoformat()
    premier = not conf.get("deja_comptees")
    comptees = set(conf.get("deja_comptees") or [])
    for liste in ("etablissements", "mediatheques", "autres"):
        conf.setdefault(liste, [])
    connus = {_cle(n) for liste in ("etablissements", "mediatheques", "autres") for n in conf[liste]}
    changements = []
    for i in sorted(donnees.get("interventions") or [], key=lambda x: str(x.get("date") or "")):
        nom = re.sub(r"\s+", " ", str(i.get("etablissement") or "")).strip()
        date = str(i.get("date") or "")[:10]
        if not nom or not date or date > aujourd_hui:
            continue
        e = _empreinte(i)
        if e in comptees:
            continue
        comptees.add(e)
        if _cle(nom) not in connus:
            connus.add(_cle(nom))
            liste = _type(nom, i.get("type"))
            conf[liste].append(nom)
            changements.append(f"+ {nom} ({liste})")
        if not premier:
            n = _seances(i.get("seances"))
            conf["interventions"] = int(conf.get("interventions") or 0) + n
            changements.append(f"+{n} intervention{'s' if n > 1 else ''} ({nom}, {date})")
    conf["deja_comptees"] = sorted(comptees)
    return changements


def lire():
    import yaml
    return yaml.safe_load(FICHIER.read_text(encoding="utf-8")) or {}


def ecrire(conf):
    import yaml
    txt = FICHIER.read_text(encoding="utf-8")
    entete = "".join(l for l in txt.splitlines(keepends=True) if l.startswith("#"))
    FICHIER.write_text(entete + yaml.safe_dump(conf, allow_unicode=True, sort_keys=False, width=1000),
                       encoding="utf-8")


def mettre_a_jour(bavard=True):
    """Appelé par construire_site.py. Ne casse jamais la construction."""
    if not SOURCE.exists():
        return None
    try:
        donnees = json.loads(SOURCE.read_text(encoding="utf-8-sig"))
        conf = lire()
        avant = json.dumps(conf, sort_keys=True)
        changements = synchroniser(donnees, conf)
        if json.dumps(conf, sort_keys=True) != avant:
            ecrire(conf)
    except Exception as e:
        if bavard:
            print(f"Confiance : {SOURCE.name} illisible ({e}) — confiance.yaml garde la version précédente.")
        return None
    if bavard:
        print("Confiance : " + ("; ".join(changements) if changements else "rien de nouveau dans le Hub") + ".")
    return changements


if __name__ == "__main__":
    if mettre_a_jour() is None:
        print(f"Rien fait : {SOURCE} introuvable ou illisible.")
        sys.exit(1)
