"""Génère docs/dictionnaire_donnees.md à partir des fichiers bruts et de la nomenclature (codes.py).

Pour chaque variable : description, taux de remplissage, nombre de valeurs distinctes, exemples,
et pour les variables codées, la répartition des codes avec leur libellé.

Usage : python src/dictionnaire.py
"""
import json
from pathlib import Path

import pandas as pd

from codes import TABLES

RACINE = Path(__file__).resolve().parents[1]
FICHIERS = {"caracteristiques": "velo_caracteristiques_2020_2024.csv", "lieux": "velo_lieux_2020_2024.csv",
            "vehicules": "velo_vehicules_2020_2024.csv", "usagers": "velo_usagers_2020_2024.csv"}
ROLE = {"caracteristiques": "une ligne par accident : quand, où, dans quelles conditions",
        "lieux": "une ligne par voie concernée (plusieurs lignes par accident en carrefour depuis 2023)",
        "vehicules": "une ligne par véhicule impliqué",
        "usagers": "une ligne par personne impliquée (conducteur, passager, piéton)"}
VIDE = {"", "-1", " "}


def section(table, df):
    spec = TABLES[table]
    lignes = [f"## Table `{table}`", "", f"{len(df):,} lignes : {ROLE[table]}.".replace(",", " "), "",
              "| Variable | Description | Rempli | Valeurs distinctes | Codes ou exemples |", "|---|---|---:|---:|---|"]
    for col in df.columns:
        if col == "annee":
            continue
        desc, codes = spec.get(col, ("Non décrite dans la nomenclature", None))
        s = df[col].astype(str).str.strip()
        rempli = (~s.isin(VIDE)).mean()
        if codes:
            vc = s.value_counts()
            ex = " ; ".join(f"`{k}` {codes.get(k, '?')} ({v / len(s):.0%})" for k, v in vc.head(6).items())
            if len(vc) > 6:
                ex += " ; …"
        else:
            ex = " ; ".join(f"`{x}`" for x in s[~s.isin(VIDE)].drop_duplicates().head(3))
        lignes.append(f"| `{col}` | {desc} | {rempli:.0%} | {s.nunique()} | {ex} |")
    return "\n".join(lignes)


def main():
    q = json.loads((RACINE / "data" / "processed" / "qualite.json").read_text(encoding="utf-8"))
    parts = ["# Dictionnaire des données", "",
             "Source : bases annuelles des accidents corporels de la circulation routière (BAAC, ONISR), "
             "data.gouv.fr, Licence Ouverte. Années 2020 à 2024, restreintes aux accidents impliquant au moins "
             "une bicyclette (`catv = 1`) ou un vélo à assistance électrique (`catv = 80`).", "",
             "Clé de jointure : `Num_Acc` relie les quatre tables ; `id_vehicule` relie un usager à son véhicule. "
             "« Rempli » compte les valeurs ni vides ni égales à `-1` (non renseigné).", "",
             "## Contrôles de qualité", "",
             f"- Accidents sans coordonnées : {q['coordonnees_manquantes']} ; hors métropole : {q['accidents_outre_mer']}.",
             f"- Accidents avec plusieurs lignes dans `lieux` : {q['lieux_plusieurs_lignes']} (changement de format en 2023).",
             f"- Piétons rattachés à un vélo, exclus des cyclistes : {q['pietons_rattaches_a_un_velo_exclus']}.",
             f"- Codes commune absents du référentiel actuel (fusions de communes) : {q['communes_inconnues']}.",
             f"- Cyclistes à gravité non renseignée, exclus : {q['gravite_non_renseignee']}.",
             f"- Format de `mois` selon l'année : {q['formats_mois_par_annee']} ; d'où 21 valeurs distinctes pour 12 mois.", ""]
    for t, f in FICHIERS.items():
        parts += [section(t, pd.read_csv(RACINE / "data" / "raw" / f, dtype=str, keep_default_na=False)), ""]
    info = RACINE / "data" / "processed" / "amenagements_info.json"
    if info.exists():
        from amenagements import MARQUAGE, SEPARE, SEUIL_M
        i = json.loads(info.read_text(encoding="utf-8"))
        parts += ["## Seconde source : inventaire des aménagements cyclables", "",
                  "Aménagements cyclables France métropolitaine (Geovelo et contributeurs OpenStreetMap, data.gouv.fr, "
                  f"licence ODbL) : {i['troncons']:_} tronçons, mises à jour du {i['date_maj_min']} au {i['date_maj_max']}. ".replace("_", " ")
                  + "Chaque tronçon décrit l'aménagement du côté droit (`ame_d`) et du côté gauche (`ame_g`). "
                  "La table dérivée ci-dessous est diffusée sous la même licence ODbL.", "",
                  "| Catégorie | Valeurs de `ame_d` ou `ame_g` | Longueur |", "|---|---|---:|",
                  f"| Séparé de la circulation | {'; '.join(sorted(SEPARE)).lower()} | {i['km_par_categorie']['separe']:_} km".replace("_", " ") + " |",
                  f"| Marquage sur chaussée | {'; '.join(sorted(MARQUAGE)).lower()} | {i['km_par_categorie']['marquage']:_} km".replace("_", " ") + " |", "",
                  "Table dérivée `data/processed/proximite_amenagements.csv`, une ligne par accident de métropole :", "",
                  "| Variable | Description |", "|---|---|",
                  "| `Num_Acc` | Identifiant de l'accident (BAAC) |",
                  "| `dist_separe_m` | Distance en mètres au plus proche aménagement séparé (vide au-delà de 500 m) |",
                  "| `dist_marquage_m` | Distance en mètres au plus proche marquage cyclable (vide au-delà de 500 m) |",
                  f"| `proximite` | Classe : aménagement séparé à moins de {SEUIL_M} m, sinon marquage seul à moins de {SEUIL_M} m, "
                  "sinon aménagement entre 20 et 50 m, sinon aucun à moins de 50 m |", ""]
    out = RACINE / "docs" / "dictionnaire_donnees.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
