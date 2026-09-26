# -*- coding: utf-8 -*-
"""
serveur_relecture.py — Relire le site en le commentant directement dans le navigateur.

Sert le site construit (`_site/`) sur http://localhost:8792/ en glissant dans chaque page une petite
barre d'outils : on active le mode « commenter », on clique un élément de la page, on écrit la remarque.
Tout est enregistré dans `relecture/relecture.json` et résumé dans `relecture/RELECTURE.md`, qu'une
session Claude lit ensuite pour appliquer les corrections.

    python relecture/serveur_relecture.py            (ou « 5 - Relire le site.bat »)

Aucune dépendance. Le site lui-même n'est pas modifié : la barre n'existe que sur ce serveur local.
"""
import datetime, json, mimetypes, os, re, shutil, sys, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

ICI = Path(__file__).resolve().parent
SITE = ICI.parent / "_site"
FICHIER = ICI / "relecture.json"
RESUME = ICI / "RELECTURE.md"
SAUVEGARDES = ICI / "_sauvegardes"
PORT = 8792
PREFIXE = "/__relecture"
CATEGORIES = ["Texte", "Mise en page", "Couleur / police", "Supprimer", "Déplacer", "Ajouter", "Autre"]

INJECTION = (f'<link rel="stylesheet" href="{PREFIXE}/overlay.css">'
             f'<script src="{PREFIXE}/overlay.js" defer></script>')


# ---------------------------------------------------------------- données

def charger():
    if FICHIER.exists():
        try:
            d = json.loads(FICHIER.read_text(encoding="utf-8"))
            d.setdefault("commentaires", [])
            d.setdefault("prochain_id", 1)
            return d
        except Exception as e:
            print("relecture.json illisible :", e)
    return {"commentaires": [], "prochain_id": 1}


def enregistrer(d):
    SAUVEGARDES.mkdir(exist_ok=True)
    if FICHIER.exists():
        stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        shutil.copy2(FICHIER, SAUVEGARDES / f"relecture-{stamp}.json")
        anciennes = sorted(SAUVEGARDES.glob("relecture-*.json"))
        for f in anciennes[:-40]:
            try:
                f.unlink()
            except OSError:
                pass
    FICHIER.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    RESUME.write_text(resume_md(d), encoding="utf-8")


def resume_md(d):
    cs = d["commentaires"]
    ouverts = [c for c in cs if c.get("statut") != "fait"]
    lignes = [f"# Relecture du site — {len(cs)} remarque(s), {len(ouverts)} à traiter",
              "",
              f"*Généré par `relecture/serveur_relecture.py` le {datetime.datetime.now():%d/%m/%Y à %H:%M}. "
              "Ne pas modifier à la main : les remarques se gèrent dans le navigateur (« 5 - Relire le site.bat »). "
              "Une session Claude lit ce fichier, applique les corrections, et coche les remarques traitées via le tableau ou directement dans `relecture.json` (`statut: fait`).*",
              ""]
    if not cs:
        lignes.append("_Aucune remarque pour l'instant._")
        return "\n".join(lignes) + "\n"
    # ordre : premières remarques d'abord, par page
    pages = []
    for c in cs:
        if c["page"] not in pages:
            pages.append(c["page"])
    for page in pages:
        lot = [c for c in cs if c["page"] == page]
        titre = next((c.get("titre_page") for c in lot if c.get("titre_page")), "") or page
        n_ouv = sum(1 for c in lot if c.get("statut") != "fait")
        ou_page = "" if page == "*" else f" — `{page}`"
        lignes.append(f"## {titre}{ou_page} — {len(lot)} remarque(s), {n_ouv} à traiter")
        lignes.append("")
        for c in sorted(lot, key=lambda c: (c.get("statut") == "fait", c["id"])):
            case = "[x]" if c.get("statut") == "fait" else "[ ]"
            cat = c.get("categorie") or "Autre"
            if c.get("selecteur"):
                extrait = (c.get("texte_element") or "").strip().replace("\n", " ")
                extrait = f" — « {extrait[:110]}{'…' if len(extrait) > 110 else ''} »" if extrait else ""
                ou = f"`{c.get('balise', '?')}`" + (f" dans `{c['bloc']}`" if c.get("bloc") else "") + extrait
            else:
                ou = "remarque générale sur tout le site" if page == "*" else "remarque générale sur la page"
            lignes.append(f"- {case} **#{c['id']} · {cat}** — {ou}")
            for l in (c.get("commentaire") or "").strip().splitlines():
                lignes.append(f"  > {l}" if l.strip() else "  >")
            details = []
            if c.get("selecteur"):
                details.append(f"sélecteur : `{c['selecteur']}`")
            if c.get("ecran"):
                details.append(f"écran {c['ecran']} px")
            if c.get("cree"):
                details.append(c["cree"][:16].replace("T", " "))
            if c.get("statut") == "fait" and c.get("reponse"):
                details.append(f"réponse : {c['reponse']}")
            if details:
                lignes.append("  _" + " · ".join(details) + "_")
            lignes.append("")
    return "\n".join(lignes) + "\n"


# ---------------------------------------------------------------- serveur

class Relecture(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # silence sauf erreurs
        if args and str(args[1]).startswith(("4", "5")):
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    # --- utilitaires réponse
    def _envoyer(self, code, corps, type_="text/html; charset=utf-8", entetes=None):
        if isinstance(corps, str):
            corps = corps.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", type_)
        self.send_header("Content-Length", str(len(corps)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (entetes or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(corps)

    def _json(self, code, obj):
        self._envoyer(code, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

    def _lire_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
        except Exception:
            return None

    # --- routes
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        chemin = urllib.parse.urlsplit(self.path).path
        if chemin.startswith(PREFIXE):
            return self.outil_get(chemin[len(PREFIXE):])
        return self.servir_site(chemin)

    def do_POST(self):
        chemin = urllib.parse.urlsplit(self.path).path
        if chemin == PREFIXE + "/api/commentaires":
            d = self._lire_json()
            if not isinstance(d, dict) or not (d.get("commentaire") or "").strip():
                return self._json(400, {"erreur": "commentaire vide"})
            data = charger()
            c = {"id": data["prochain_id"], "page": d.get("page") or "/", "titre_page": (d.get("titre_page") or "")[:120],
                 "selecteur": (d.get("selecteur") or "")[:400], "balise": (d.get("balise") or "")[:60], "bloc": (d.get("bloc") or "")[:120],
                 "texte_element": (d.get("texte_element") or "")[:300], "categorie": d.get("categorie") if d.get("categorie") in CATEGORIES else "Autre",
                 "commentaire": d["commentaire"].strip()[:4000], "ecran": int(d.get("ecran") or 0) or None,
                 "statut": "ouvert", "cree": datetime.datetime.now().isoformat(timespec="minutes"), "modifie": None, "reponse": ""}
            data["commentaires"].append(c)
            data["prochain_id"] += 1
            enregistrer(data)
            return self._json(201, c)
        self._json(404, {"erreur": "route inconnue"})

    def do_PUT(self):
        m = re.fullmatch(PREFIXE + r"/api/commentaires/(\d+)", urllib.parse.urlsplit(self.path).path)
        if not m:
            return self._json(404, {"erreur": "route inconnue"})
        d = self._lire_json()
        if not isinstance(d, dict):
            return self._json(400, {"erreur": "JSON attendu"})
        data = charger()
        for c in data["commentaires"]:
            if c["id"] == int(m.group(1)):
                if "commentaire" in d and (d["commentaire"] or "").strip():
                    c["commentaire"] = d["commentaire"].strip()[:4000]
                if d.get("categorie") in CATEGORIES:
                    c["categorie"] = d["categorie"]
                if d.get("statut") in ("ouvert", "fait"):
                    c["statut"] = d["statut"]
                if "reponse" in d:
                    c["reponse"] = (d["reponse"] or "")[:1000]
                c["modifie"] = datetime.datetime.now().isoformat(timespec="minutes")
                enregistrer(data)
                return self._json(200, c)
        self._json(404, {"erreur": "remarque inconnue"})

    def do_DELETE(self):
        m = re.fullmatch(PREFIXE + r"/api/commentaires/(\d+)", urllib.parse.urlsplit(self.path).path)
        if not m:
            return self._json(404, {"erreur": "route inconnue"})
        data = charger()
        avant = len(data["commentaires"])
        data["commentaires"] = [c for c in data["commentaires"] if c["id"] != int(m.group(1))]
        if len(data["commentaires"]) == avant:
            return self._json(404, {"erreur": "remarque inconnue"})
        enregistrer(data)
        self._json(200, {"ok": True})

    def outil_get(self, reste):
        if reste in ("", "/"):
            return self._envoyer(200, (ICI / "tableau.html").read_text(encoding="utf-8"))
        if reste == "/api/commentaires":
            return self._json(200, {"commentaires": charger()["commentaires"], "categories": CATEGORIES})
        if reste in ("/overlay.js", "/overlay.css", "/tableau.html"):
            f = ICI / reste.lstrip("/")
            type_ = "application/javascript; charset=utf-8" if reste.endswith(".js") else "text/css; charset=utf-8" if reste.endswith(".css") else "text/html; charset=utf-8"
            return self._envoyer(200, f.read_bytes(), type_)
        self._json(404, {"erreur": "inconnu"})

    def servir_site(self, chemin):
        chemin = urllib.parse.unquote(chemin)
        rel = chemin.lstrip("/")
        if chemin.endswith("/") or chemin == "":
            rel = rel + "index.html"
        cible = (SITE / rel).resolve()
        if SITE.resolve() not in cible.parents and cible != SITE.resolve():
            return self._envoyer(403, "Interdit", "text/plain; charset=utf-8")
        if cible.is_dir():  # /blog → /blog/
            return self._envoyer(301, "", entetes={"Location": chemin + "/"})
        if not cible.exists():
            page404 = SITE / "404.html"
            corps = page404.read_text(encoding="utf-8") if page404.exists() else "<h1>Page introuvable</h1>"
            return self._envoyer(404, self.injecter(corps))
        type_, _ = mimetypes.guess_type(str(cible))
        type_ = type_ or "application/octet-stream"
        if cible.suffix.lower() in (".html", ".htm"):
            return self._envoyer(200, self.injecter(cible.read_text(encoding="utf-8")))
        if type_.startswith("text/") or type_ in ("application/javascript", "application/xml", "image/svg+xml"):
            type_ += "; charset=utf-8"
        self._envoyer(200, cible.read_bytes(), type_)

    @staticmethod
    def injecter(html):
        i = html.lower().rfind("</body>")
        return html[:i] + INJECTION + html[i:] if i >= 0 else html + INJECTION


def main():
    if not SITE.exists():
        sys.exit("Le site n'est pas construit : lancer d'abord « 2 - Construire le site.bat » (ou python construire_site.py).")
    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("font/woff2", ".woff2")
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Relecture)
    n = len(charger()["commentaires"])
    print(f"Relecture du site : http://localhost:{PORT}/   ({n} remarque(s) enregistrée(s), tableau sur http://localhost:{PORT}{PREFIXE}/)")
    print("Ctrl+C pour arrêter.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
