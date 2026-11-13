"""Étape 3 : préparer les données du tableau de bord (dashboard/data.json).

- indicateurs et séries par année, matrice heure x jour
- grille de 0,1 degré pour la carte nationale (France métropolitaine)
- points individuels pour les Pyrénées-Atlantiques (64) et les Landes (40)
- résultats des hypothèses, concordance des deux sources, points noirs

Usage : python src/tableau_de_bord.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
TRAITE = RACINE / "data" / "processed"
PAS = 0.1  # taille de la maille de la grille, en degrés


def main():
    cy = pd.read_csv(TRAITE / "cyclistes.csv", dtype={"dep": str, "com": str, "agg": str, "situ": str, "lum": str},
                     parse_dates=["date"], low_memory=False)
    res = json.loads((RACINE / "resultats" / "resultats.json").read_text(encoding="utf-8"))
    cy["annee"] = cy["date"].dt.year

    m = cy[cy["metropole"]]
    m = m.assign(glat=(np.floor(m["lat"] / PAS) * PAS + PAS / 2).round(3), glon=(np.floor(m["long"] / PAS) * PAS + PAS / 2).round(3))
    grille = (m.groupby(["glat", "glon"]).agg(n=("grav", "size"), graves=("grave", "sum"), tues=("tue", "sum"))
              .reset_index().values.tolist())

    sud = cy[cy["dep"].isin(["64", "40"]) & cy["metropole"]].copy()
    sud["g"] = np.select([sud["tue"], sud["grave"]], [2, 1], 0)
    points = sud[["lat", "long", "annee", "g", "agg", "situ", "commune", "antagoniste"]].round({"lat": 5, "long": 5})
    points = points.fillna("").values.tolist()
    top_sud = (sud.groupby("commune").agg(n=("grav", "size"), graves=("grave", "sum")).sort_values("n", ascending=False)
               .head(10).reset_index().values.tolist())

    hj = cy.pivot_table(index="jour_semaine", columns="heure", values="grav", aggfunc="size", fill_value=0)
    hj = hj.reindex(index=range(7), columns=range(24), fill_value=0).values.tolist()
    mois = cy.groupby(cy["date"].dt.month).size().reindex(range(1, 13), fill_value=0).tolist()

    pn = pd.read_csv(RACINE / "resultats" / "points_noirs.csv", dtype={"dep": str})
    pn["adresse"] = pn["adresse"].fillna("")
    points_noirs = pn[["lat", "lon", "accidents", "graves", "tues", "commune", "adresse", "dep", "annees"]].values.tolist()
    synth_pn = json.loads((RACINE / "resultats" / "points_noirs.json").read_text(encoding="utf-8"))
    info_am = TRAITE / "amenagements_info.json"

    data = {"periode": res["periode"], "cyclistes": res["cyclistes"], "accidents": res["accidents"], "tues": res["tues"],
            "graves": res["graves"], "par_annee": res["par_annee"], "heure_jour": hj, "mois": mois,
            "hypotheses": res["hypotheses"], "taille_commune": res["taille_commune"], "antagonistes": res["antagonistes"],
            "grille": {"pas": PAS, "colonnes": ["lat", "lon", "n", "graves", "tues"], "cellules": grille},
            "sud_ouest": {"colonnes": ["lat", "lon", "annee", "gravite", "agg", "situ", "commune", "antagoniste"],
                          "points": points, "communes": top_sud, "n": len(sud), "graves": int(sud["grave"].sum()),
                          "tues": int(sud["tue"].sum())},
            "points_noirs": {"colonnes": ["lat", "lon", "accidents", "graves", "tues", "commune", "adresse", "dep", "annees"],
                             "liste": points_noirs, **synth_pn},
            "concordance": res.get("concordance_baac_inventaire", {}).get("20"),
            "sensibilite_h6": res.get("sensibilite_h6", []),
            "amenagements": json.loads(info_am.read_text(encoding="utf-8")) if info_am.exists() else None,
            "source": "BAAC 2020-2024 (ONISR, data.gouv.fr, Licence Ouverte) ; populations : geo.api.gouv.fr"}
    out = RACINE / "dashboard" / "data.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(out, round(out.stat().st_size / 1024), "Ko", len(grille), "mailles", len(points), "points sud-ouest")


if __name__ == "__main__":
    main()
