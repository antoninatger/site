# Site antoninatger.com — version 1 (générateur statique)

*Créé le 6 septembre 2026. Ce dossier est le futur dépôt GitHub `antoninatger/site`. Tout est du texte : les pages sont des fichiers Markdown, le site est reconstruit en quelques secondes, et GitHub Pages le publie à chaque `push`. Aucun WordPress, aucune base de données.*

## Les fichiers

| Quoi | Où |
|---|---|
| Réglages (titre, menu, pied de page, formulaires) | `site.yaml` |
| Les pages (accueil, contact, formations, jeux, livres, à propos, presse, parcours, mentions…) | `contenu/pages/*.md` |
| Une fiche par intervention (15) | `contenu/interventions/*.md` |
| Les billets du blog (importés de WordPress) | `contenu/blog/*.md` |
| Catégories du blog (4 au lieu de 14) | `contenu/categories.yaml` |
| Références, témoignages, listes « ils m'ont fait confiance », jeux | `contenu/references.yaml` |
| Anciennes adresses WordPress → nouvelles | `contenu/redirections.yaml` |
| Mise en page (Jinja2) | `gabarits/*.html` |
| Style, script, favicon | `static/` |
| Photos et PDF (importés de WordPress) | `images/uploads/` |
| Le site construit (ne pas modifier, ne pas versionner) | `_site/` |
| Outil de relecture (serveur local, barre de commentaires, remarques) | `relecture/` |

## Les fichiers .bat

0. **Installer** — une fois : `pip install -r requirements.txt` (markdown, jinja2, pyyaml, pillow).
1. **Importer le blog** — copie `..\blog\export\` (billets + images réduites à 1600 px) dans `contenu/blog/` et `images/uploads/`. À relancer après un nouvel export ; seuls les fichiers nouveaux sont retraités. (Fait le 6 septembre : 233 billets, 662 fichiers, 481 Mo → 172 Mo.)
1b. **Rapatrier les visuels du site** — télécharge depuis antoninatger.com les 57 images que les pages utilisent mais qui n'étaient pas dans les billets (couvertures des tomes 2 et 3, logos des partenaires, photos des anciennes pages). Une fois, avec Internet, avant de quitter WordPress.
2. **Construire le site** — génère `_site/` et vérifie les liens internes. Le compte-rendu s'affiche ; « Liens internes (hors images) : tous valides » est ce qu'on veut.
3. **Voir le site** — ouvre http://localhost:8791/ sur le site construit.
4. **Publier** — construit, vérifie, `git add`, `commit`, `push`. GitHub Actions reconstruit et met en ligne dans les deux minutes.
5. **Relire le site** — construit le site et l'ouvre sur http://localhost:8792/ avec une barre « Relecture » en bas à droite (voir ci-dessous).

## Relire et commenter (5 - Relire le site.bat)

Le site s'affiche normalement, avec une barre noire en bas à droite. **Commenter** passe en mode remarque : on survole, un cadre rouge montre l'élément, on clique, on choisit une catégorie (Texte, Mise en page, Couleur / police, Supprimer, Déplacer, Ajouter, Autre), on écrit, on enregistre. Une épingle numérotée reste sur l'élément ; on la clique pour modifier, marquer faite ou supprimer. **Remarque sur la page** sert pour ce qui ne tient pas à un élément précis ; le lien **N remarques à traiter** ouvre le tableau de toutes les remarques, avec un champ pour les remarques sur tout le site. Échap quitte le mode. Réduire la fenêtre à moins de 700 px permet de commenter la version téléphone (la largeur d'écran est enregistrée avec chaque remarque).

Tout s'écrit dans `relecture/relecture.json`, résumé lisible dans `relecture/RELECTURE.md` (régénéré à chaque enregistrement). **Une session Claude lit `RELECTURE.md`**, applique les corrections, puis marque les remarques faites (tableau, ou `statut: fait` dans le JSON, avec une `reponse` si utile). Rien de tout cela n'existe sur le site en ligne : la barre n'est injectée que par le serveur local.

## Écrire

**Un billet** : un fichier `contenu/blog/AAAA-MM-JJ-mon-titre.md` :

```
---
titre: "Mon titre"
date: "2026-09-10T09:00:00"
categories: ["Esprit critique"]
image_une: "/images/uploads/2026/09/ma-photo.jpg"
---
Le texte, en Markdown. Une vidéo YouTube : {youtube: IDENTIFIANT | Titre}
```

L'adresse sera `/2026/09/10/mon-titre/`. `categories` : Esprit critique, Actualités, Conseils d'écriture, Écrits. `brouillon: true` cache le billet. Les photos vont dans `images/uploads/AAAA/MM/`.

**Une fiche d'intervention** : copier une fiche existante. Les champs de l'en-tête : `titre`, `sous_titre`, `duree`, `publics` (liste), `groupe` (scolaire / adultes / autres), `ordre`, `adage` (vrai si l'offre existe sur ADAGE), `distance` (vrai si possible en visio), `video` (identifiant YouTube), `programmes` (liste), `materiel`, `ou`, `pdf`. Les témoignages liés à une fiche sont dans `references.yaml` (champ `intervention` = nom du fichier de la fiche).

**Une page** : `contenu/pages/nom.md` → `/nom/`. En-tête : `titre`, `eyebrow`, `lead`, `description` (pour Google et les partages), `image` (partage), `large: true` pour une page sans colonne de lecture.

**Le pied de page, le menu, l'adresse du formulaire** : `site.yaml`.

## Ce qui est branché et ce qui attend

- **Formulaires de contact et listes d'attente** : Web3Forms, le même service et la même clé que les jeux (`site.yaml`, `formulaires`). Les messages arrivent dans Outlook, avec un objet qui commence par `[Contact site]` ou `[Liste d'attente formations]`. Gratuit jusqu'à 250 envois par mois.
- **Abonnement au blog** : le formulaire envoie l'adresse à WordPress.com (site `amanalat.wordpress.com`, identifiant 31556844), qui gère la liste existante et le mail de confirmation. Rien à créer.
- **Mise en ligne** : dépôt GitHub → Settings → Pages → Source « GitHub Actions » ; domaine `antoninatger.com` (le fichier `CNAME` est prêt) et DNS chez le registrar (voir `A-FAIRE-ANTONIN.md`).
- **Jeux** : les liens pointent vers `jeux.antoninatger.com` (Cloudflare Pages, voir `jeux-reserves/`) et vers le Fakemètre sur GitHub Pages. Tant que le domaine n'existe pas, ces liens ne répondent pas : `site.yaml` → `jeux_url` peut être remis à `https://antoninatger.github.io/jeux` en attendant.
- **Image de partage par défaut** : `images/site/partage.jpg` (1200 × 630) à fournir ; en attendant, les pages sans image n'ont pas de vignette sur LinkedIn.
- **Mesure d'audience** : aucune. À décider (Plausible, Umami ou rien).

## Vérifier avant la mise en ligne

`2 - Construire le site.bat` doit finir sans lien cassé ; la liste des images manquantes doit être vide après l'import (les 14 images que l'export n'a pas pu récupérer sont listées dans `blog/export/RAPPORT.txt` : elles resteront cassées dans les vieux billets, sauf à les remettre à la main dans `images/uploads/`).

## Filtres de la page Interventions (27 septembre 2026)

La page `/interventions/` se filtre par **âge** (primaire, collège, lycée, supérieur, adultes), **cadre**
(scolaire, hors scolaire), **durée** (1 h, 2 h) et **format** (présentiel, à distance). Dans un même groupe
les choix s'additionnent, entre groupes ils se cumulent ; l'adresse garde les filtres
(`/interventions/?age=college&mode=distanciel`), on peut donc envoyer un lien déjà filtré.

Rien à remplir : tout est déduit de `publics`, `duree` et `distance`. Si une déduction est fausse, on
l'impose dans l'en-tête de la fiche :

    ages: [college, lycee]            # primaire, college, lycee, superieur, adultes
    cadre: [scolaire]                 # scolaire, hors-scolaire
    formats: [1h]                     # 1h, 2h
    presentiel: false                 # seulement à distance (cas de « Intervention à distance »)
