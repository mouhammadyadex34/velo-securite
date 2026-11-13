"""Contrôles automatiques : filtrage, cohérence des tables produites, calculs des hypothèses."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import analyse  # noqa: E402
import prepare  # noqa: E402
from telecharger import filtrer, lire_csv  # noqa: E402


@pytest.fixture(scope="module")
def tables():
    acc, cy, q = prepare.preparer()
    return acc, cy, q


def test_filtrage_garde_seulement_les_accidents_avec_un_velo():
    veh = lire_csv("Num_Acc;id_vehicule;catv\n1;a;7\n1;b;1\n2;c;7\n3;d;80\n".encode())
    car = lire_csv("Accident_Id;lum\n1;1\n2;1\n3;5\n".encode())
    out = filtrer({"vehicules": veh, "caracteristiques": car}, 2024)
    assert [l["Num_Acc"] for l in out["caracteristiques"]] == ["1", "3"]
    assert len(out["vehicules"]) == 3


def test_lecture_latin1():
    h, l = lire_csv("Num_Acc;adr\n1;Rue de l'Église\n".encode("latin-1"))
    assert l[0][1] == "Rue de l'Église"


def test_un_accident_par_ligne(tables):
    acc, _, _ = tables
    assert acc["Num_Acc"].is_unique


def test_tous_les_cyclistes_sont_sur_un_velo_et_pas_pietons(tables):
    _, cy, _ = tables
    assert set(cy["catv"].astype(str)) <= {"1", "80"}
    assert set(cy["catu"].astype(str)) <= {"1", "2"}
    assert (cy["grav"].astype(str) != "-1").all()


def test_chaque_accident_a_au_moins_un_cycliste_ou_un_pieton_exclu(tables):
    acc, cy, q = tables
    sans = acc["cyclistes"].isna().sum()
    assert sans <= q["pietons_rattaches_a_un_velo_exclus"] + q["gravite_non_renseignee"]


def test_coordonnees_metropole(tables):
    acc, _, _ = tables
    m = acc[acc["metropole"]]
    assert m["lat"].between(41, 51.5).all() and m["long"].between(-5.5, 10).all()


def test_rapport_de_risques_exemple_a_la_main():
    e = pd.DataFrame({"grave": [True] * 30 + [False] * 70})
    r = pd.DataFrame({"grave": [True] * 10 + [False] * 90})
    h = analyse.comparer(e, r, "test", "e", "r")
    assert h["rapport_risques"] == 3.0
    assert h["ic95"][0] < 3 < h["ic95"][1]


def test_resultats_coherents():
    res = json.loads((RACINE / "resultats" / "resultats.json").read_text(encoding="utf-8"))
    assert sum(a["victimes"] for a in res["par_annee"].values()) == res["cyclistes"]
    assert res["tues"] <= res["graves"] <= res["cyclistes"]


# --- Seconde source, points noirs, modèle commun

import amenagements  # noqa: E402
import modele_commun  # noqa: E402
import points_noirs  # noqa: E402


def test_categories_amenagements():
    assert amenagements.categorie("PISTE CYCLABLE", "AUCUN") == "separe"
    assert amenagements.categorie("AUCUN", "BANDE CYCLABLE") == "marquage"
    assert amenagements.categorie("BANDE CYCLABLE", "VOIE VERTE") == "separe"  # le plus protecteur l'emporte
    assert amenagements.categorie("AUCUN", "AUTRE") is None
    assert not amenagements.SEPARE & amenagements.MARQUAGE


def test_classe_de_proximite():
    c = amenagements.classe_proximite
    assert c(5, 1) == "Aménagement séparé à moins de 20 m"
    assert c(40, 12) == "Marquage seul à moins de 20 m"
    assert c(35, None) == "Aménagement entre 20 et 50 m"
    assert c(None, None) == c(300, 80) == "Aucun aménagement à moins de 50 m"


def test_proximite_couvre_tous_les_accidents_de_metropole(tables):
    acc, _, _ = tables
    prox = pd.read_csv(RACINE / "data" / "processed" / "proximite_amenagements.csv")
    assert prox["Num_Acc"].is_unique
    assert set(prox["Num_Acc"].astype(str)) == set(acc.loc[acc["metropole"], "Num_Acc"].astype(str))
    assert (prox[["dist_separe_m", "dist_marquage_m"]].dropna() <= amenagements.RAYON_MAX_M).all().all()


def test_ajustement_mantel_haenszel_sans_confusion():
    # même rapport (0,5) dans chaque strate : l'ajusté doit valoir 0,5 même si le brut est biaisé
    def strate(nom, n_e, n_r, p_r):
        e = pd.DataFrame({"grave": [True] * int(n_e * p_r / 2) + [False] * (n_e - int(n_e * p_r / 2)), "taille_ville": nom})
        r = pd.DataFrame({"grave": [True] * int(n_r * p_r) + [False] * (n_r - int(n_r * p_r)), "taille_ville": nom})
        return e, r
    e1, r1 = strate("ville", 1000, 100, 0.2)
    e2, r2 = strate("village", 100, 1000, 0.6)
    h = analyse.comparer_ajuste(pd.concat([e1, e2]), pd.concat([r1, r2]), "t", "e", "r")
    assert h["rapport_risques"] == 0.5
    assert h["rapport_risques_brut"] < 0.3  # le brut exagère l'effet
    assert h["ic95"][0] < 0.5 < h["ic95"][1]


def test_points_noirs_regroupe_les_accidents_proches():
    # 6 accidents à quelques mètres les uns des autres, 1 isolé à 5 km
    lat = [43.3000 + i * 0.0001 for i in range(6)] + [43.35]
    acc = pd.DataFrame({"lat": lat, "long": [-0.37] * 7})
    out = points_noirs.detecter(acc)
    assert out["point_noir"].iloc[:6].nunique() == 1 and (out["point_noir"].iloc[:6] >= 0).all()
    assert out["point_noir"].iloc[6] == -1


def test_adresses_baac_remises_dans_l_ordre():
    assert points_noirs.nettoyer_adresse("ALSACE LORRAINE D'") == "d'Alsace Lorraine"
    assert points_noirs.nettoyer_adresse("RUE DE RIVOLI") == "Rue de Rivoli"
    assert points_noirs.nettoyer_adresse(None) == ""


def test_modele_commun_valide_et_rejette():
    e = json.loads((RACINE / "docs" / "exemple_evenements.json").read_text(encoding="utf-8"))[0]
    assert modele_commun.valider(e) == []
    assert "gravité hors échelle commune" in modele_commun.valider({**e, "gravite": "grave"})
    assert any("manquant" in m for m in modele_commun.valider({k: v for k, v in e.items() if k != "lat"}))
