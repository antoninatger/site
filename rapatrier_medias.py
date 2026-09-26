# -*- coding: utf-8 -*-
"""
rapatrier_medias.py — Télécharge les visuels que les pages du site utilisent mais qui ne sont pas
dans l'export du blog (couvertures, logos, photos des pages Bibliographie), depuis antoninatger.com,
vers images/uploads/AAAA/MM/. À lancer une fois, depuis le PC (il faut Internet), tant que WordPress répond.

    python rapatrier_medias.py
"""
import urllib.request, urllib.parse, sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
DEST = ICI / "images" / "uploads"
BASE = "https://antoninatger.com/wp-content/uploads/"
FICHIERS = """
2018/11/cultura-defense.jpg
2018/11/dsc_0507.jpg
2018/11/img_20181005_135008.jpg
2018/11/img_20181103_121857-2.jpg
2018/11/librairie-dialogue.jpg
2018/12/article-le-parisien4541452473039796823.jpg
2018/12/biblioteca_magazine_sharp6991886659975644923.png
2018/12/cestenville_dc3a9cembre_20182053665877715287419.jpg
2018/12/couv_interfeel_rc3a9duite.jpg
2018/12/img_20181211_194238_5248275567805265749039.jpg
2018/12/img_20181215_214134_8367679184982592834216.jpg
2018/12/img_20181216_133720991375392856528900.jpg
2018/12/img_20181216_1355297856479150307718689.jpg
2018/12/img_20181218_154839_9981864927620918086534.jpg
2018/12/mon-quotidien_sharp-15215279362143752904.jpg
2018/12/var-matin2552853952468518399.jpg
2019/01/img_20190126_1546376807665775385215946.jpg
2019/02/img_20190213_145339_9277943688063859936724.jpg
2022/09/photo-4_flou.jpg
2022/11/img_20221105_115139_534-1.webp
2023/02/20211210_135632.jpg
2023/08/1-college-jean-moulin-trevoux-3.jpg
2023/11/2-450215437-e1700955923614.jpg
2023/11/3-2-831621556-e1700956034704.jpg
2023/12/20231222_1431498427290980719176928.jpg
2023/12/college-balzac-self-data.png
2024/01/20220929_174617.jpg
2024/05/20240503_1532306835844626328064646.jpg
2024/09/20221019_la-motte-servolex.jpg
2024/09/aristide-berges-14-12-2022.png
2024/09/article-le-progres-crope.jpg
2024/09/voiron.-fake-news-et-esprit-critique-au-lycec2a6ue-ferdinand-buisson-images-1.jpg
2024/09/voiron.-fake-news-et-esprit-critique-au-lycee295a0ue-ferdinand-buisson-images-0.jpg
2024/12/tedx2024_by_fred_giraud-21281291258691058558378665.jpg
2025/02/bafkreibzcomnscl5mtzl5p756acis6goaodoh3n5avluzt4bxto76eg53y.jpg
2025/03/img-20250228-wa0008-edited.jpg
2025/03/img-20250301-wa0005-edited-1.jpg
2025/03/img_20241108_095801.jpg
2025/03/signal-2025-03-05-205515-edited.jpeg
2025/06/1000065401.jpg
2025/11/medijska-pismenost-antonin-atger-croatie.jpg
2025/12/image-1.png
2026/03/interfeel-2.jpg
2026/03/interfeel-3.jpg
2026/04/614DJAQ-kGL._SY522_.jpg
2026/04/Logo-IF-Croatie-2023-novi-1030x689-1.png
2026/04/Logo_Metropole_Lyon_-_2022.svg_.png
2026/04/Logo_Val_Oise.svg_.png
2026/04/Logo_de_lAssemblee_nationale_francaise.svg_.png
2026/04/ambassade-france-croatie-1.png
2026/04/flou-1776598922318.png
2026/04/unicef_vert.webp
2026/05/lycee-francais-international.jpg
2026/05/photo-bourg-en-bresse-lycee-Carriat.jpg
2026/07/impots-complots-thumbnail.jpg
2026/07/padf-screenshot.webp
2026/07/signal-2026-07-24-11-59-07-278.jpg
""".split()


def rapatrier():
    ok = deja = rate = 0
    for rel in FICHIERS:
        cible = DEST / rel
        if cible.exists():
            deja += 1
            continue
        cible.parent.mkdir(parents=True, exist_ok=True)
        url = BASE + urllib.parse.quote(rel)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (rapatriement antoninatger.com)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                cible.write_bytes(r.read())
            ok += 1
            print("  ✓", rel)
        except Exception as e:
            rate += 1
            print("  ✗", rel, "→", e)
    print(f"\n{ok} téléchargé(s), {deja} déjà présent(s), {rate} échec(s). Relancer « 1 - Importer le blog.bat » n'est pas nécessaire.")
    if ok:
        print("Les fichiers sont bruts (non réduits) : python importer_blog.py --sans-images ne les touche pas ; c'est voulu pour les logos et couvertures.")


if __name__ == "__main__":
    rapatrier()
