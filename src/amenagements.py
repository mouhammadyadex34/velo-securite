"""Étape 1 bis : croiser chaque accident avec les aménagements cyclables réels (seconde source).

La BAAC dit si l'accident a eu lieu « sur piste cyclable » (champ `situ`), d'après le procès-verbal.
On confronte cette information à une source indépendante : l'inventaire national des aménagements
cyclables (Geovelo et contributeurs OpenStreetMap, data.gouv.fr). Pour chaque accident de métropole,
on calcule la distance au plus proche aménagement de chaque catégorie.

Le fichier source (70 Mo) n'est pas versionné : `make donnees` le télécharge. Le résultat
`data/processed/proximite_amenagements.csv`, petit, est versionné pour que la suite tourne sans lui.

Usage : python src/amenagements.py
"""
import json
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
BRUT, TRAITE = RACINE / "data" / "raw", RACINE / "data" / "processed"
SOURCE = BRUT / "amenagements_cyclables_france-20261103.parquet"
SORTIE = TRAITE / "proximite_amenagements.csv"

# Regroupement des valeurs du champ `ame_d` / `ame_g` (schéma national des aménagements cyclables)
SEPARE = {"PISTE CYCLABLE", "VOIE VERTE", "DOUBLE SENS CYCLABLE PISTE", "AMENAGEMENT MIXTE PIETON VELO HORS VOIE VERTE"}
MARQUAGE = {"BANDE CYCLABLE", "DOUBLE SENS CYCLABLE BANDE", "COULOIR BUS+VELO", "CHAUSSEE A VOIE CENTRALE BANALISEE",
            "ACCOTEMENT REVETU HORS CVCB", "VELO RUE", "DOUBLE SENS CYCLABLE NON MATERIALISE"}
CATEGORIES = {"separe": "Séparé de la circulation (piste, voie verte…)", "marquage": "Marquage sur chaussée (bande, couloir bus…)"}

SEUIL_M = 20          # un accident est « sur ou au bord » d'un aménagement à moins de 20 m
SEUILS_SENSIBILITE = (10, 20, 30, 50)
RAYON_MAX_M = 500     # au-delà, la distance n'est pas calculée (aménagement « lointain »)


def categorie(ame_d, ame_g):
    cotes = {ame_d, ame_g}
    if cotes & SEPARE:
        return "separe"
    if cotes & MARQUAGE:
        return "marquage"
    return None


def classe_proximite(d_separe, d_marquage, seuil=SEUIL_M):
    """Classe d'un accident selon l'aménagement le plus protecteur à moins de `seuil` mètres."""
    if pd.notna(d_separe) and d_separe <= seuil:
        return "Aménagement séparé à moins de 20 m"
    if pd.notna(d_marquage) and d_marquage <= seuil:
        return "Marquage seul à moins de 20 m"
    proche = [d for d in (d_separe, d_marquage) if pd.notna(d)]
    if not proche or min(proche) > 50:
        return "Aucun aménagement à moins de 50 m"
    return "Aménagement entre 20 et 50 m"


def calculer():
    import geopandas as gpd

    g = gpd.read_parquet(SOURCE, columns=["ame_d", "ame_g", "date_maj", "geometry"])
    info = {"troncons": len(g), "date_maj_min": str(g["date_maj"].min().date()), "date_maj_max": str(g["date_maj"].max().date())}
    g["cat"] = [categorie(a, b) for a, b in zip(g["ame_d"], g["ame_g"])]
    info["troncons_par_categorie"] = {k: int(v) for k, v in g["cat"].value_counts().items()}
    g = g[g["cat"].notna()].to_crs(2154)  # Lambert-93 : distances en mètres
    info["km_par_categorie"] = {k: round(float(v) / 1000) for k, v in g.length.groupby(g["cat"]).sum().items()}

    acc = pd.read_csv(TRAITE / "accidents.csv", usecols=["Num_Acc", "lat", "long", "metropole"], low_memory=False)
    acc = acc[acc["metropole"]].reset_index(drop=True)
    pts = gpd.GeoDataFrame(acc[["Num_Acc"]], geometry=gpd.points_from_xy(acc["long"], acc["lat"]), crs=4326).to_crs(2154)
    for cat in CATEGORIES:
        j = gpd.sjoin_nearest(pts, g.loc[g["cat"] == cat, ["geometry"]], max_distance=RAYON_MAX_M, distance_col="d")
        pts[f"dist_{cat}_m"] = j.loc[~j.index.duplicated(), "d"].round(1)
    out = pd.DataFrame(pts.drop(columns="geometry"))
    out["proximite"] = [classe_proximite(s, m) for s, m in zip(out["dist_separe_m"], out["dist_marquage_m"])]
    TRAITE.mkdir(parents=True, exist_ok=True)
    out.to_csv(SORTIE, index=False)
    (TRAITE / "amenagements_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return out, info


def concordance(cy, seuil=SEUIL_M):
    """Accord entre la BAAC (« sur piste cyclable ») et l'inventaire (aménagement séparé à moins de `seuil` m),
    au niveau des accidents de métropole."""
    a = cy.drop_duplicates("Num_Acc").dropna(subset=["proximite"])
    baac = a["situ"] == "5"
    inv = a["dist_separe_m"] <= seuil
    return {"seuil_m": seuil, "accidents": int(len(a)),
            "baac_sur_piste": int(baac.sum()),
            "baac_sur_piste_et_inventaire": int((baac & inv).sum()),
            "part_baac_confirmee": round(float((baac & inv).sum() / baac.sum()), 3),
            "inventaire_proche": int(inv.sum()),
            "inventaire_proche_mais_baac_hors_piste": int((inv & ~baac).sum()),
            "part_inventaire_proche_note_sur_piste": round(float((baac & inv).sum() / inv.sum()), 3)}


if __name__ == "__main__":
    if not SOURCE.exists():
        print(f"{SOURCE.name} absent : étape sautée, le fichier versionné {SORTIE.name} est réutilisé "
              "(`make donnees` pour le télécharger).")
        raise SystemExit(0)
    out, info = calculer()
    print(json.dumps(info, ensure_ascii=False, indent=2))
    print(out["proximite"].value_counts().to_string())
