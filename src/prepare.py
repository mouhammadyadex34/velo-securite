"""Étape 1 : nettoyer les quatre tables BAAC filtrées et construire deux tables d'analyse.

- accidents.csv : une ligne par accident impliquant un vélo
- cyclistes.csv : une ligne par cycliste (conducteur ou passager d'un vélo ou d'un VAE)
- qualite.json  : les contrôles de qualité et leurs résultats

Usage : python src/prepare.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from codes import VELO

RACINE = Path(__file__).resolve().parents[1]
BRUT, TRAITE = RACINE / "data" / "raw", RACINE / "data" / "processed"

# Rectangle de la France métropolitaine (Corse comprise)
METRO_LAT, METRO_LON = (41.0, 51.5), (-5.5, 10.0)


def lire(nom):
    return pd.read_csv(BRUT / nom, dtype=str, keep_default_na=False)


def classe_taille(pop):
    if pd.isna(pop):
        return "Inconnue"
    if pop < 2_000:
        return "1. Moins de 2 000 hab."
    if pop < 20_000:
        return "2. 2 000 à 20 000 hab."
    if pop < 100_000:
        return "3. 20 000 à 100 000 hab."
    return "4. Plus de 100 000 hab."


def communes():
    """Population par commune. Les arrondissements de Paris, Lyon et Marseille sont rattachés
    à leur commune pour la classe de taille."""
    p = lire("communes_population.csv")
    p["population"] = pd.to_numeric(p["population"], errors="coerce")
    villes = {"75": "75056", "69": "69123", "13": "13055"}
    pop_ville = p.set_index("code")["population"]
    arr = p["type"] == "arrondissement"
    p["code_ville"] = np.where(arr, p["codeDepartement"].map(villes), p["code"])
    p["pop_ville"] = p["code_ville"].map(pop_ville)
    return p


def preparer():
    q = {}
    c, l, v, u = (lire(f"velo_{t}_2020_2024.csv") for t in ("caracteristiques", "lieux", "vehicules", "usagers"))
    q["lignes_brutes"] = {"caracteristiques": len(c), "lieux": len(l), "vehicules": len(v), "usagers": len(u)}
    q["accidents_doublons_caracteristiques"] = int(c["Num_Acc"].duplicated().sum())

    # --- Caractéristiques : dates, heures, coordonnées
    for col in ("lat", "long"):
        c[col] = pd.to_numeric(c[col].str.replace(",", ".", regex=False), errors="coerce")
    c["date"] = pd.to_datetime(dict(year=c["an"].astype(int), month=c["mois"].astype(int), day=c["jour"].astype(int)), errors="coerce")
    c["heure"] = pd.to_numeric(c["hrmn"].str.split(":").str[0], errors="coerce")
    c["jour_semaine"] = c["date"].dt.dayofweek  # 0 = lundi
    c["metropole"] = c["lat"].between(*METRO_LAT) & c["long"].between(*METRO_LON)
    q["coordonnees_manquantes"] = int(c[["lat", "long"]].isna().any(axis=1).sum())
    q["accidents_outre_mer"] = int((~c["metropole"]).sum())
    q["dates_invalides"] = int(c["date"].isna().sum())
    q["formats_mois_par_annee"] = {a: ("sans zéro (3)" if (g["mois"].str.len() == 1).any() else "sur deux chiffres (03)")
                                   for a, g in c.groupby("annee")}

    # --- Lieux : depuis 2023, une ligne par voie (carrefour) ; avant, une seule ligne
    nb_lieux = l.groupby("Num_Acc").size()
    q["lieux_plusieurs_lignes"] = {a: int(((l["annee"] == a) & l["Num_Acc"].map(nb_lieux).gt(1)).groupby(l["Num_Acc"]).any().sum())
                                   for a in sorted(l["annee"].unique())}
    l["piste_ou_bande"] = l["vosp"].isin(["1", "2"])
    l["sur_piste"] = l["situ"] == "5"
    lieu = (l.groupby("Num_Acc")
            .agg(catr=("catr", "first"), vma=("vma", "first"), surf=("surf", "first"), situ=("situ", "first"),
                 voie_avec_piste_ou_bande=("piste_ou_bande", "any"), accident_sur_piste=("sur_piste", "any"),
                 nb_voies_lieux=("Num_Acc", "size"))
            .reset_index())

    # --- Véhicules : vélos, et l'antagoniste principal (le plus lourd des autres véhicules)
    v["est_velo"] = v["catv"].isin(VELO)
    # Antagoniste = le plus lourd des véhicules non-vélos ; à défaut un autre vélo ; sinon le cycliste est seul.
    poids = [("PL, bus, car, tram", {"13", "14", "15", "16", "17", "37", "38", "39", "40", "20", "21"}),
             ("Véhicule utilitaire", {"10"}), ("Véhicule léger", {"7", "3"}),
             ("Deux-roues motorisé", {"2", "30", "31", "32", "33", "34", "35", "36", "41", "42", "43"}),
             ("EDP (trottinette…)", {"50", "60"})]

    def antagoniste(d):
        autres = set(d.loc[~d["est_velo"], "catv"])
        for nom, cats in poids:
            if autres & cats:
                return nom
        if autres:
            return "Autre"
        return "Autre vélo" if d["est_velo"].sum() > 1 else "Aucun (seul)"

    veh = v.groupby("Num_Acc").agg(nb_vehicules=("catv", "size"), nb_velos=("est_velo", "sum"),
                                   vae=("catv", lambda s: bool((s == "80").any()))).reset_index()
    veh["antagoniste"] = veh["Num_Acc"].map(v.groupby("Num_Acc")[["catv", "est_velo"]].apply(antagoniste))

    # --- Communes
    p = communes()
    c = c.merge(p[["code", "nom", "population", "pop_ville", "code_ville"]].rename(columns={"code": "com", "nom": "commune"}),
                on="com", how="left")
    q["communes_inconnues"] = int(c["commune"].isna().sum())
    c["taille_ville"] = c["pop_ville"].map(classe_taille)

    acc = c.merge(lieu, on="Num_Acc", how="left").merge(veh, on="Num_Acc", how="left")
    acc["pieton_implique"] = acc["Num_Acc"].isin(set(u.loc[u["catu"] == "3", "Num_Acc"]))

    # --- Cyclistes : usagers conducteurs ou passagers d'un vélo (on exclut les piétons heurtés par un vélo)
    velos = v.loc[v["est_velo"], ["Num_Acc", "id_vehicule", "catv"]]
    cy = u.merge(velos, on=["Num_Acc", "id_vehicule"], how="inner")
    q["pietons_rattaches_a_un_velo_exclus"] = int((cy["catu"] == "3").sum())
    cy = cy[cy["catu"].isin(["1", "2"])].copy()
    q["gravite_non_renseignee"] = int((cy["grav"] == "-1").sum())
    cy = cy[cy["grav"] != "-1"]
    cy["tue"] = cy["grav"] == "2"
    cy["grave"] = cy["grav"].isin(["2", "3"])  # tué ou blessé hospitalisé
    cy["age"] = pd.to_numeric(cy["annee"], errors="coerce") - pd.to_numeric(cy["an_nais"], errors="coerce")
    cy["casque"] = cy[["secu1", "secu2", "secu3"]].eq("2").any(axis=1)
    cy["vae"] = cy["catv"] == "80"
    cols_acc = ["Num_Acc", "date", "hrmn", "heure", "jour_semaine", "lum", "agg", "int", "atm", "col", "dep", "com", "commune",
                "taille_ville", "lat", "long", "metropole", "catr", "vma", "surf", "situ", "voie_avec_piste_ou_bande",
                "accident_sur_piste", "nb_vehicules", "antagoniste"]
    cy = cy.merge(acc[cols_acc], on="Num_Acc", how="left")

    # gravité de l'accident = gravité maximale parmi ses cyclistes
    g = cy.groupby("Num_Acc").agg(cyclistes=("grav", "size"), cycliste_tue=("tue", "any"), cycliste_grave=("grave", "any"))
    acc = acc.merge(g, on="Num_Acc", how="left")

    q["accidents_finaux"] = len(acc)
    q["cyclistes_finaux"] = len(cy)
    TRAITE.mkdir(parents=True, exist_ok=True)
    acc.to_csv(TRAITE / "accidents.csv", index=False)
    cy.to_csv(TRAITE / "cyclistes.csv", index=False)
    (TRAITE / "qualite.json").write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")
    return acc, cy, q


if __name__ == "__main__":
    acc, cy, q = preparer()
    print(json.dumps(q, ensure_ascii=False, indent=2))
