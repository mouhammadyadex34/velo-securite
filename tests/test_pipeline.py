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
