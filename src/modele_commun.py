"""Étape 4 : exprimer les données dans un modèle commun d'« événements de sécurité à vélo ».

Le modèle est décrit dans docs/modele_commun.md. Il vise à accueillir, dans un même format, des sources
différentes : accidents déclarés (BAAC), inventaire des aménagements, et demain des enquêtes auprès des
cyclistes ou des capteurs embarqués sur les vélos. Ce script implémente la correspondance pour les deux
sources présentes dans le dépôt et vérifie chaque enregistrement.

Usage : python src/modele_commun.py
"""
import json
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
TRAITE = RACINE / "data" / "processed"

TYPES = {"accident_corporel", "presque_accident", "signalement", "mesure_capteur"}
GRAVITES = {"indemne", "blesse_leger", "blesse_hospitalise", "tue", "sans_objet", "inconnue"}
PRECISIONS_TEMPS = {"minute", "heure", "jour", "mois"}

GRAV_BAAC = {"1": "indemne", "4": "blesse_leger", "3": "blesse_hospitalise", "2": "tue"}
LUM_BAAC = {"1": "jour", "2": "crepuscule", "3": "nuit_sans_eclairage", "4": "nuit_eclairage_eteint", "5": "nuit_eclairee"}

# Champs obligatoires du modèle et leur type
SCHEMA = {
    "id": str, "type": str, "source": str, "id_source": str,
    "debut": str, "precision_temps": str,
    "lon": float, "lat": float, "precision_position_m": (int, float, type(None)),
    "mode": str, "role": str, "gravite": str,
    "contexte": dict, "infrastructure": dict, "provenance": dict,
}


def depuis_baac(cy):
    """Un enregistrement par cycliste de la BAAC (métropole et outre-mer)."""
    out = []
    for r in cy.itertuples(index=False):
        heure = getattr(r, "hrmn", None)
        debut = pd.Timestamp(r.date)
        precision = "jour"
        if isinstance(heure, str) and ":" in heure:
            hh, mm = heure.split(":")[:2]
            debut = debut.replace(hour=int(hh), minute=int(mm))
            precision = "minute"
        infra = {}
        if pd.notna(getattr(r, "proximite", None)):
            infra = {"classe_proximite": r.proximite,
                     "distance_separe_m": None if pd.isna(r.dist_separe_m) else float(r.dist_separe_m),
                     "distance_marquage_m": None if pd.isna(r.dist_marquage_m) else float(r.dist_marquage_m),
                     "source": "inventaire national des aménagements cyclables"}
        out.append({
            "id": f"baac:{r.Num_Acc}:{r.id_vehicule}:{r.num_occurrence}",
            "type": "accident_corporel", "source": "BAAC", "id_source": str(r.Num_Acc),
            "debut": debut.isoformat(timespec="minutes"), "precision_temps": precision,
            "lon": float(r.long), "lat": float(r.lat),
            "precision_position_m": None,  # non publiée par la BAAC
            "mode": "vae" if r.vae else "velo", "role": "conducteur" if str(r.catu) == "1" else "passager",
            "gravite": GRAV_BAAC.get(str(r.grav), "inconnue"),
            "contexte": {"agglomeration": str(r.agg) == "2", "eclairage": LUM_BAAC.get(str(r.lum), "inconnu"),
                         "sur_piste_selon_source": str(r.situ) == "5", "antagoniste": r.antagoniste,
                         "commune_insee": None if pd.isna(r.com) else str(r.com)},
            "infrastructure": infra,
            "provenance": {"jeu": "BAAC 2020-2024, ONISR", "licence": "Licence Ouverte 2.0",
                           "champs": ["Num_Acc", "an", "mois", "jour", "hrmn", "lat", "long", "grav", "catu", "catv",
                                      "agg", "lum", "situ", "com"]},
        })
    return out


def valider(e):
    """Liste des erreurs d'un enregistrement (vide s'il est conforme au modèle)."""
    err = [f"champ manquant : {k}" for k in SCHEMA if k not in e]
    err += [f"type incorrect : {k}" for k, t in SCHEMA.items() if k in e and not isinstance(e[k], t)]
    if e.get("type") not in TYPES:
        err.append("type d'événement inconnu")
    if e.get("gravite") not in GRAVITES:
        err.append("gravité hors échelle commune")
    if e.get("precision_temps") not in PRECISIONS_TEMPS:
        err.append("précision temporelle inconnue")
    if isinstance(e.get("lat"), float) and not -90 <= e["lat"] <= 90:
        err.append("latitude invalide")
    if isinstance(e.get("lon"), float) and not -180 <= e["lon"] <= 180:
        err.append("longitude invalide")
    return err


def main():
    cy = pd.read_csv(TRAITE / "cyclistes.csv", dtype=str, keep_default_na=False, na_values=[""])
    cy["vae"] = cy["vae"] == "True"
    prox = TRAITE / "proximite_amenagements.csv"
    if prox.exists():
        cy = cy.merge(pd.read_csv(prox, dtype={"Num_Acc": str}), on="Num_Acc", how="left")
    cy["num_occurrence"] = cy.groupby(["Num_Acc", "id_vehicule"]).cumcount()
    cy = cy.dropna(subset=["lat", "long"])
    cy[["lat", "long"]] = cy[["lat", "long"]].astype(float)
    ev = depuis_baac(cy)
    erreurs = {e["id"]: valider(e) for e in ev if valider(e)}
    with open(TRAITE / "evenements.jsonl", "w", encoding="utf-8") as f:
        for e in ev:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    exemple = [e for e in ev if e["infrastructure"]][:2]
    (RACINE / "docs" / "exemple_evenements.json").write_text(json.dumps(exemple, ensure_ascii=False, indent=2), encoding="utf-8")
    return ev, erreurs


if __name__ == "__main__":
    ev, err = main()
    print(len(ev), "événements,", len(err), "non conformes")
