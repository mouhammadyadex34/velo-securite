.PHONY: tout donnees tests voir

# Toute la chaîne, des fichiers bruts au tableau de bord.
# L'étape « amenagements » est sautée si l'inventaire (70 Mo, non versionné) est absent :
# son résultat, data/processed/proximite_amenagements.csv, est versionné.
tout:
	cd src && python prepare.py && python amenagements.py && python points_noirs.py && python analyse.py \
	  && python modele_commun.py && python dictionnaire.py && python tableau_de_bord.py

donnees:
	cd src && python telecharger.py

tests:
	python -m pytest -q

voir:
	cd dashboard && python -m http.server 8000
