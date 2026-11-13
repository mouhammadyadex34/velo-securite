.PHONY: tout donnees tests voir

# Toute la chaîne, des fichiers bruts au tableau de bord
tout:
	cd src && python prepare.py && python analyse.py && python dictionnaire.py && python tableau_de_bord.py

donnees:
	cd src && python telecharger.py

tests:
	python -m pytest -q

voir:
	cd dashboard && python -m http.server 8000
