"""Étape 0 (facultative) : retélécharger la BAAC 2020-2024 sur data.gouv.fr et la restreindre aux accidents
impliquant un vélo, puis l'inventaire des aménagements cyclables. Les fichiers BAAC obtenus sont ceux de
data/raw/ (déjà versionnés) ; l'inventaire, trop lourd, ne l'est pas.

Usage : python src/telecharger.py
"""
import csv
import io
import json
from pathlib import Path
from urllib.request import urlopen

from codes import VELO

RACINE = Path(__file__).resolve().parents[1]
BRUT = RACINE / "data" / "raw"
API = "https://www.data.gouv.fr/api/1/datasets/53698f4ca3a729239d2036df/"
INVENTAIRE = ("https://static.data.gouv.fr/resources/amenagements-cyclables-france-metropolitaine/20261103-150341/"
              "france-20261103.parquet")  # Geovelo, licence ODbL, 70 Mo
GEO = "https://geo.api.gouv.fr/communes?fields=code,nom,population,codeDepartement,codeRegion&format=json"
TABLES = {"caracteristiques": ("ca",), "lieux": ("lieux",), "vehicules": ("vehicules",), "usagers": ("usagers",)}
ANNEES = range(2020, 2025)


def lire_csv(octets):
    """Décode en UTF-8, ou en Latin-1 si besoin, et renvoie l'en-tête et les lignes (séparateur ;)."""
    try:
        texte = octets.decode("utf-8")
    except UnicodeDecodeError:
        texte = octets.decode("latin-1")
    lignes = list(csv.reader(io.StringIO(texte), delimiter=";"))
    entete = [c.strip() for c in lignes[0]]
    entete[0] = "Num_Acc"  # « Accident_Id » dans certains millésimes
    return entete, [[c.strip() for c in l] for l in lignes[1:] if l]


def accidents_velo(entete_veh, lignes_veh):
    i = entete_veh.index("catv")
    return {l[0] for l in lignes_veh if l[i] in VELO}


def filtrer(tables_annee, annee):
    """tables_annee : {table: (entête, lignes)} -> {table: liste de dicts} restreints aux accidents vélo."""
    ids = accidents_velo(*tables_annee["vehicules"])
    return {t: [{"annee": str(annee), **dict(zip(h, l))} for l in lignes if l[0] in ids]
            for t, (h, lignes) in tables_annee.items()}


def ressource(ressources, annee, prefixe):
    for r in ressources:
        titre = r["title"].lower()
        if str(annee) in titre and titre.startswith(prefixe) and "immatricul" not in titre and r["url"].endswith(".csv"):
            return r["url"]
    raise LookupError(f"{prefixe} {annee} introuvable")


def main():
    ressources = json.load(urlopen(API))["resources"]
    sortie = {t: [] for t in TABLES}
    for annee in ANNEES:
        brut = {t: lire_csv(urlopen(ressource(ressources, annee, p[0])).read()) for t, p in TABLES.items()}
        for t, lignes in filtrer(brut, annee).items():
            sortie[t] += lignes
    BRUT.mkdir(parents=True, exist_ok=True)
    for t, lignes in sortie.items():
        colonnes = list(dict.fromkeys(k for l in lignes for k in l))
        with open(BRUT / f"velo_{t}_2020_2024.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, colonnes)
            w.writeheader()
            w.writerows(lignes)
    communes = json.load(urlopen(GEO))
    arr = json.load(urlopen(GEO + "&type=arrondissement-municipal"))
    with open(BRUT / "communes_population.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["code", "nom", "population", "codeDepartement", "codeRegion", "type"])
        for c, typ in [(c, "commune") for c in communes] + [(c, "arrondissement") for c in arr]:
            w.writerow([c["code"], c["nom"], c.get("population", ""), c.get("codeDepartement", ""), c.get("codeRegion", ""), typ])


def inventaire():
    """Inventaire national des aménagements cyclables (non versionné, utilisé par amenagements.py)."""
    from amenagements import SOURCE
    with urlopen(INVENTAIRE) as r, open(SOURCE, "wb") as f:
        while bloc := r.read(1 << 20):
            f.write(bloc)


if __name__ == "__main__":
    main()
    inventaire()
