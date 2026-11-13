"""Étape 2 bis : repérer les « points noirs », lieux où les accidents de vélo se répètent.

Méthode : DBSCAN sur les coordonnées en Lambert-93. Un point noir regroupe au moins 5 accidents
dont chacun est à moins de 50 m d'un autre accident du groupe, sur 2020-2024. Le rayon court évite
d'enchaîner des rues entières dans les centres denses.

Attention : un point noir signale où les accidents se concentrent, pas où le risque par passage
est le plus élevé. Sans comptage des vélos, un carrefour très fréquenté ressort mécaniquement.

Usage : python src/points_noirs.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

RACINE = Path(__file__).resolve().parents[1]
TRAITE, RES = RACINE / "data" / "processed", RACINE / "resultats"
RAYON_M, MIN_ACCIDENTS = 50, 5


def lambert93(lon, lat):
    from pyproj import Transformer
    t = Transformer.from_crs(4326, 2154, always_xy=True)
    return t.transform(np.asarray(lon), np.asarray(lat))


def detecter(acc, rayon=RAYON_M, minimum=MIN_ACCIDENTS):
    """Ajoute à `acc` (accidents de métropole) une colonne `point_noir` : numéro du groupe, ou -1."""
    x, y = lambert93(acc["long"], acc["lat"])
    acc = acc.copy()
    acc["x"], acc["y"] = x, y
    acc["point_noir"] = DBSCAN(eps=rayon, min_samples=minimum).fit(np.c_[x, y]).labels_
    return acc


PARTICULES = ("DE LA", "DE L'", "DES", "DU", "DE", "D'")


def nettoyer_adresse(a):
    """La BAAC écrit souvent la particule à la fin (« ALSACE LORRAINE D' ») : on la remet devant."""
    if not isinstance(a, str) or not a.strip():
        return ""
    a = " ".join(a.replace("’", "'").split())
    for p in PARTICULES:
        if a.upper().endswith(" " + p):
            a = f"{p} {a[: -len(p) - 1]}"
            break
    a = a.title() if a.isupper() else a
    a = " " + a.replace("' ", "'")
    for p in ("De", "Des", "Du", "La", "Le", "Les"):
        a = a.replace(f" {p} ", f" {p.lower()} ")
    for p in ("L'", "D'"):
        a = a.replace(f" {p}", f" {p.lower()}")
    return a.strip()


def resumer(acc):
    """Une ligne par point noir, triée par nombre d'accidents puis de cyclistes gravement atteints."""
    k = acc[acc["point_noir"] >= 0]
    adr = k["adr"].map(nettoyer_adresse)
    adresse = adr.groupby(k["point_noir"]).agg(lambda s: s[s != ""].mode().iloc[0] if (s != "").any() else "")
    r = k.groupby("point_noir").agg(
        accidents=("Num_Acc", "size"), graves=("cycliste_grave", "sum"), tues=("cycliste_tue", "sum"),
        lat=("lat", "mean"), lon=("long", "mean"), dep=("dep", "first"), commune=("commune", "first"),
        annees=("annee", "nunique"), en_intersection=("int", lambda s: round(float((s.astype(str) != "1").mean()), 2)),
        antagoniste=("antagoniste", lambda s: s.mode().iloc[0]),
        etendue_m=("x", lambda s: 0.0))
    # étendue = plus grande distance au centre du groupe
    for i, g in k.groupby("point_noir"):
        r.loc[i, "etendue_m"] = float(np.hypot(g["x"] - g["x"].mean(), g["y"] - g["y"].mean()).max().round())
    r["adresse"] = adresse
    r[["graves", "tues"]] = r[["graves", "tues"]].astype(int)
    r[["lat", "lon"]] = r[["lat", "lon"]].round(5)
    return r.sort_values(["accidents", "graves"], ascending=False).reset_index()


def main():
    acc = pd.read_csv(TRAITE / "accidents.csv", dtype={"dep": str, "com": str, "int": str}, low_memory=False)
    acc = acc[acc["metropole"]]
    acc["cycliste_grave"] = acc["cycliste_grave"].fillna(False).astype(bool)
    acc["cycliste_tue"] = acc["cycliste_tue"].fillna(False).astype(bool)
    acc = detecter(acc)
    r = resumer(acc)
    RES.mkdir(exist_ok=True)
    r.to_csv(RES / "points_noirs.csv", index=False)
    synthese = {"rayon_m": RAYON_M, "minimum_accidents": MIN_ACCIDENTS, "points_noirs": int(len(r)),
                "accidents_dans_un_point_noir": int(r["accidents"].sum()),
                "part_des_accidents": round(float(r["accidents"].sum() / len(acc)), 3),
                "graves_dans_un_point_noir": int(r["graves"].sum()),
                "part_accidents_graves_dans_points_noirs": round(float(r["graves"].sum() / r["accidents"].sum()), 3),
                "part_accidents_graves_ailleurs": round(float(acc.loc[acc["point_noir"] < 0, "cycliste_grave"].mean()), 3),
                "part_sans_autre_vehicule_dans_points_noirs": round(float((acc.loc[acc["point_noir"] >= 0, "antagoniste"] == "Aucun (seul)").mean()), 3),
                "part_sans_autre_vehicule_ailleurs": round(float((acc.loc[acc["point_noir"] < 0, "antagoniste"] == "Aucun (seul)").mean()), 3),
                "part_pieton_implique_dans_points_noirs": round(float(acc.loc[acc["point_noir"] >= 0, "pieton_implique"].mean()), 3),
                "part_pieton_implique_ailleurs": round(float(acc.loc[acc["point_noir"] < 0, "pieton_implique"].mean()), 3),
                "sud_ouest": int(r["dep"].isin(["64", "40"]).sum())}
    (RES / "points_noirs.json").write_text(json.dumps(synthese, ensure_ascii=False, indent=2), encoding="utf-8")
    return r, synthese


if __name__ == "__main__":
    r, s = main()
    print(json.dumps(s, ensure_ascii=False, indent=2))
    print(r.head(15).to_string())
    print(r[r["dep"].isin(["64", "40"])].to_string())
