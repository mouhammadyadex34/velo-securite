"""Étape 2 : tester des hypothèses sur la gravité des accidents de cyclistes, puis produire figures et résultats.

Mesure principale : la part de cyclistes « gravement atteints » (tués ou hospitalisés plus de 24 h)
parmi les cyclistes impliqués. On compare des groupes par un rapport de risques (RR) avec un intervalle
de confiance à 95 % et un test du khi-deux.

Usage : python src/analyse.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, norm

from amenagements import SEUILS_SENSIBILITE, concordance
from codes import label

RACINE = Path(__file__).resolve().parents[1]
TRAITE, FIG, RES = RACINE / "data" / "processed", RACINE / "figures", RACINE / "resultats"
BLEU, GRIS, ROUGE = "#1b4f86", "#9aa5b1", "#c0392b"


def charger():
    cy = pd.read_csv(TRAITE / "cyclistes.csv", dtype={"dep": str, "com": str, "lum": str, "agg": str, "situ": str},
                     parse_dates=["date"], low_memory=False)
    acc = pd.read_csv(TRAITE / "accidents.csv", dtype={"dep": str, "com": str}, parse_dates=["date"], low_memory=False)
    prox = TRAITE / "proximite_amenagements.csv"
    if prox.exists():  # seconde source : inventaire des aménagements cyclables
        cy = cy.merge(pd.read_csv(prox), on="Num_Acc", how="left")
    return cy, acc


def comparer(expose, reference, nom, libelle_expose, libelle_ref, strate=None):
    """Rapport des proportions de cyclistes gravement atteints : exposés / référence."""
    a, n1 = int(expose["grave"].sum()), len(expose)
    c, n0 = int(reference["grave"].sum()), len(reference)
    p1, p0 = a / n1, c / n0
    rr = p1 / p0
    se = np.sqrt(1 / a - 1 / n1 + 1 / c - 1 / n0)
    lo, hi = np.exp(np.log(rr) - 1.96 * se), np.exp(np.log(rr) + 1.96 * se)
    chi2, pval, _, _ = chi2_contingency([[a, n1 - a], [c, n0 - c]])
    return {"hypothese": nom, "strate": strate, "groupe": libelle_expose, "reference": libelle_ref,
            "n_groupe": n1, "graves_groupe": a, "part_groupe": round(p1, 4),
            "n_reference": n0, "graves_reference": c, "part_reference": round(p0, 4),
            "rapport_risques": round(float(rr), 2), "ic95": [round(float(lo), 2), round(float(hi), 2)], "p_valeur": float(f"{pval:.2e}") if pval > 0 else 1e-300}


def comparer_ajuste(expose, reference, nom, libelle_expose, libelle_ref, strate=None, par="taille_ville"):
    """Rapport de risques de Mantel-Haenszel, ajusté sur `par` (une strate par classe de taille de commune).
    Intervalle de confiance par la variance de Greenland-Robins."""
    num = den = var = 0.0
    for k in set(expose[par]) | set(reference[par]):
        e, r = expose[expose[par] == k], reference[reference[par] == k]
        n1, n0 = len(e), len(r)
        if n1 == 0 or n0 == 0:
            continue
        a, c, N = e["grave"].sum(), r["grave"].sum(), n1 + n0
        num += a * n0 / N
        den += c * n1 / N
        var += (n1 * n0 * (a + c) - a * c * N) / N ** 2
    rr = num / den
    se = np.sqrt(var / (num * den))
    lo, hi = np.exp(np.log(rr) - 1.96 * se), np.exp(np.log(rr) + 1.96 * se)
    pval = float(2 * norm.sf(abs(np.log(rr) / se)))
    brut = comparer(expose, reference, nom, libelle_expose, libelle_ref, strate)
    return {**brut, "ajuste_sur": "taille de la commune", "rapport_risques_brut": brut["rapport_risques"],
            "rapport_risques": round(float(rr), 2), "ic95": [round(float(lo), 2), round(float(hi), 2)],
            "p_valeur": float(f"{pval:.2e}") if pval > 0 else 1e-300}


def hypotheses(cy):
    R = []
    # H1 : hors agglomération, les accidents sont plus graves
    R.append(comparer(cy[cy["agg"] == "1"], cy[cy["agg"] == "2"], "H1 Localisation",
                      "Hors agglomération", "En agglomération"))
    # H2 : la nuit sans éclairage public aggrave les conséquences (comparé au plein jour)
    for agg, nom in (("1", "Hors agglomération"), ("2", "En agglomération")):
        d = cy[cy["agg"] == agg]
        if (d["lum"] == "3").sum() >= 30:
            R.append(comparer(d[d["lum"] == "3"], d[d["lum"] == "1"], "H2 Éclairage",
                              "Nuit sans éclairage", "Plein jour", strate=nom))
    # H3 : un accident survenu sur une piste cyclable est moins grave qu'un accident sur la chaussée
    #      (comparaison en agglomération pour ne pas mélanger avec l'effet de H1)
    d = cy[cy["agg"] == "2"]
    R.append(comparer(d[d["situ"] == "5"], d[d["situ"] == "1"], "H3 Piste cyclable",
                      "Sur piste cyclable", "Sur chaussée", strate="En agglomération"))
    # H3 bis : même comparaison, face à une voiture seulement (les pistes comptent plus d'accidents entre vélos)
    v = d[d["antagoniste"] == "Véhicule léger"]
    R.append(comparer(v[v["situ"] == "5"], v[v["situ"] == "1"], "H3 Piste cyclable",
                      "Sur piste cyclable", "Sur chaussée", strate="En agglomération, face à une voiture"))
    # H4 : la gravité dépend du véhicule antagoniste (référence : véhicule léger)
    ref = cy[cy["antagoniste"] == "Véhicule léger"]
    for ant in ("PL, bus, car, tram", "Véhicule utilitaire", "Aucun (seul)", "Deux-roues motorisé", "Autre vélo"):
        g = cy[cy["antagoniste"] == ant]
        if len(g) >= 30:
            R.append(comparer(g, ref, "H4 Antagoniste", ant, "Véhicule léger"))
    # H5 : le vélo à assistance électrique est associé à des accidents plus graves
    R.append(comparer(cy[cy["vae"]], cy[~cy["vae"]], "H5 VAE", "Vélo à assistance électrique", "Vélo classique"))
    # H3 ajustée : les pistes sont surtout dans les grandes villes, où les accidents sont moins graves
    d = cy[cy["agg"] == "2"]
    R.append(comparer_ajuste(d[d["situ"] == "5"], d[d["situ"] == "1"], "H3 Piste cyclable",
                             "Sur piste cyclable", "Sur chaussée", strate="En agglomération, ajusté"))
    # H6 : H3 refaite avec une source indépendante de la BAAC (inventaire des aménagements), brute puis ajustée
    if "proximite" in cy:
        d = cy[(cy["agg"] == "2") & cy["proximite"].notna()]
        ref = d[d["proximite"] == "Aucun aménagement à moins de 50 m"]
        for grp in ("Aménagement séparé à moins de 20 m", "Marquage seul à moins de 20 m"):
            g = d[d["proximite"] == grp]
            R.append(comparer(g, ref, "H6 Aménagement (inventaire)", grp, "Aucun aménagement à moins de 50 m",
                              strate="En agglomération"))
            R.append(comparer_ajuste(g, ref, "H6 Aménagement (inventaire)", grp, "Aucun aménagement à moins de 50 m",
                                     strate="En agglomération, ajusté"))
    return R


def sensibilite(cy):
    """H6 ajustée pour plusieurs seuils de distance : la conclusion ne doit pas dépendre du seuil choisi."""
    d = cy[(cy["agg"] == "2") & cy["proximite"].notna()]
    ref = d[d["proximite"] == "Aucun aménagement à moins de 50 m"]
    out = []
    for s in SEUILS_SENSIBILITE:
        r = comparer_ajuste(d[d["dist_separe_m"] <= s], ref, "H6 sensibilité", f"Séparé à moins de {s} m", "Aucun à moins de 50 m")
        out.append({"seuil_m": s, "n": r["n_groupe"], "rapport_risques_brut": r["rapport_risques_brut"],
                    "rapport_risques": r["rapport_risques"], "ic95": r["ic95"]})
    return out


def taux_par_taille(cy, communes):
    """Cyclistes victimes par an pour 100 000 habitants, selon la taille de la commune (France entière)."""
    p = communes[communes["type"] == "commune"].copy()
    p["population"] = pd.to_numeric(p["population"], errors="coerce")
    from prepare import classe_taille
    p["taille_ville"] = p["population"].map(classe_taille)
    pop = p.groupby("taille_ville")["population"].sum()
    annees = cy["date"].dt.year.nunique()
    t = cy[cy["taille_ville"] != "Inconnue"].groupby("taille_ville").agg(victimes=("grav", "size"), graves=("grave", "sum"),
                                                                            tues=("tue", "sum"))
    t["population"] = pop
    t["victimes_par_100k_par_an"] = (t["victimes"] / annees / t["population"] * 1e5).round(1)
    t["graves_par_100k_par_an"] = (t["graves"] / annees / t["population"] * 1e5).round(1)
    t["part_graves"] = (t["graves"] / t["victimes"]).round(3)
    return t.reset_index()


def figures(cy, taille, R):
    FIG.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    # F1 : évolution annuelle
    an = cy.groupby(cy["date"].dt.year).agg(victimes=("grav", "size"), tues=("tue", "sum"), vae=("vae", "mean"))
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.bar(an.index, an["victimes"], color=BLEU)
    for x, y, t in zip(an.index, an["victimes"], an["tues"]):
        ax.text(x, y + 60, f"{t} tués", ha="center", fontsize=9)
    ax.set_title("Cyclistes victimes d'un accident corporel par an (France)", loc="left")
    ax.set_ylabel("cyclistes")
    fig.tight_layout(); fig.savefig(FIG / "01_victimes_par_an.png", dpi=160); plt.close(fig)

    # F2 : heure x jour de semaine
    m = cy.pivot_table(index="jour_semaine", columns="heure", values="grav", aggfunc="size", fill_value=0)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.imshow(m.values, aspect="auto", cmap="Blues")
    ax.set_yticks(range(7), ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"])
    ax.set_xticks(range(0, 24, 2), [f"{h}h" for h in range(0, 24, 2)])
    ax.set_title("Quand les cyclistes sont-ils victimes ? (heure × jour, 2020-2024)", loc="left")
    fig.tight_layout(); fig.savefig(FIG / "02_heure_jour.png", dpi=160); plt.close(fig)

    # F3 : rapports de risques
    fig, ax = plt.subplots(figsize=(8, 0.42 * len(R) + 1.2))
    lab = [f"{r['groupe']}" + (f" ({r['strate'].lower()})" if r["strate"] else "") + f"\nvs {r['reference'].lower()}" for r in R]
    y = np.arange(len(R))[::-1]
    for yi, r in zip(y, R):
        ax.plot(r["ic95"], [yi, yi], color=GRIS)
        coul = ROUGE if r["ic95"][0] > 1 else BLEU if r["ic95"][1] < 1 else GRIS
        ax.plot(r["rapport_risques"], yi, "o", color=coul)
    ax.axvline(1, color="black", lw=0.8)
    ax.set_yticks(y, lab, fontsize=7.5); ax.set_xscale("log")
    ticks = [0.35, 0.5, 0.7, 1, 1.5, 2, 3]
    ax.set_xticks(ticks, [str(t).replace(".", ",") for t in ticks]); ax.minorticks_off()
    ax.set_xlabel("rapport de risques d'être tué ou hospitalisé\n(échelle log, IC 95 %)")
    fig.tight_layout(); fig.savefig(FIG / "03_rapports_de_risques.png", dpi=160); plt.close(fig)

    # F4 : taux par taille de commune
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.barh(taille["taille_ville"].str[3:], taille["graves_par_100k_par_an"], color=BLEU)
    ax.set_xlabel("cyclistes tués ou hospitalisés, par an, pour 100 000 habitants")
    ax.set_title("Selon la taille de la commune de l'accident", loc="left")
    ax.invert_yaxis()
    fig.tight_layout(); fig.savefig(FIG / "04_taille_commune.png", dpi=160); plt.close(fig)

    # F5 : ce que change l'ajustement sur la taille de commune (H3 avec la BAAC, H6 avec l'inventaire)
    aj = [r for r in R if "ajuste_sur" in r]
    if aj:
        fig, ax = plt.subplots(figsize=(7.5, 0.7 * len(aj) + 1.2))
        y = np.arange(len(aj))[::-1]
        for yi, r in zip(y, aj):
            ax.annotate("", xy=(r["rapport_risques"], yi), xytext=(r["rapport_risques_brut"], yi),
                        arrowprops=dict(arrowstyle="->", color=GRIS))
            ax.plot(r["rapport_risques_brut"], yi, "o", color=GRIS)
            ax.plot(r["ic95"], [yi - 0.12] * 2, color=BLEU, lw=1)
            ax.plot(r["rapport_risques"], yi, "o", color=BLEU)
        src = {"H3": "Selon la BAAC :", "H6": "Selon l'inventaire :"}
        ax.set_yticks(y, [f"{src[r['hypothese'][:2]]}\n{r['groupe'].lower()}" for r in aj], fontsize=8)
        ax.axvline(1, color="black", lw=0.8)
        ax.set_xscale("log"); ax.set_xticks([0.35, 0.5, 0.7, 1], ["0,35", "0,5", "0,7", "1"]); ax.minorticks_off()
        ax.set_xlabel("rapport de risques, en agglomération\ngris : brut ; bleu : ajusté sur la taille de commune (IC 95 %)")
        ax.set_title("L'ajustement sur la taille de commune réduit l'effet apparent", loc="left", fontsize=10)
        fig.tight_layout(); fig.savefig(FIG / "05_ajustement.png", dpi=160); plt.close(fig)


def main():
    cy, acc = charger()
    communes = pd.read_csv(RACINE / "data" / "raw" / "communes_population.csv", dtype=str)
    R = hypotheses(cy)
    accord = {s: concordance(cy, s) for s in SEUILS_SENSIBILITE} if "proximite" in cy else {}
    sens = sensibilite(cy) if "proximite" in cy else []
    taille = taux_par_taille(cy, communes)
    figures(cy, taille, R)
    an = cy.groupby(cy["date"].dt.year).agg(victimes=("grav", "size"), graves=("grave", "sum"), tues=("tue", "sum"),
                                            part_vae=("vae", "mean"))
    an["part_vae"] = an["part_vae"].round(3)
    res = {
        "periode": "2020-2024", "cyclistes": len(cy), "accidents": len(acc), "tues": int(cy["tue"].sum()),
        "graves": int(cy["grave"].sum()), "part_graves": round(cy["grave"].mean(), 4),
        "par_annee": {int(k): {kk: (float(vv) if isinstance(vv, float) else int(vv)) for kk, vv in v.items()} for k, v in an.iterrows()},
        "hypotheses": R,
        "sensibilite_h6": sens,
        "concordance_baac_inventaire": accord,
        "taille_commune": taille.to_dict(orient="records"),
        "antagonistes": cy.groupby("antagoniste").agg(n=("grav", "size"), part_graves=("grave", "mean")).round(3).reset_index().to_dict(orient="records"),
        "eclairage": {label("caracteristiques", "lum", k): {"n": int(len(g)), "part_graves": round(g["grave"].mean(), 3)}
                      for k, g in cy.groupby("lum")},
    }
    RES.mkdir(exist_ok=True)
    (RES / "resultats.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = main()
    for h in r["hypotheses"]:
        print(f"{h['hypothese']:<20} {h['groupe']:<30} {h['part_groupe']:.1%} vs {h['part_reference']:.1%}  "
              f"RR {h['rapport_risques']} {h['ic95']} p={h['p_valeur']}  (n={h['n_groupe']}/{h['n_reference']})")
    print(pd.DataFrame(r["taille_commune"]).to_string())
    print(json.dumps(r["sensibilite_h6"], ensure_ascii=False))
    print(json.dumps(r["concordance_baac_inventaire"].get(20), ensure_ascii=False, indent=1))
