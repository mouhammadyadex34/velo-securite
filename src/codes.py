"""Nomenclature des variables BAAC utilisées (guide ONISR « Description des bases de données annuelles
des accidents corporels de la circulation routière », version 2019 et suivantes).

Chaque entrée : description, et pour les variables codées, le libellé de chaque code.
Ce fichier sert à la fois au décodage et à la génération du dictionnaire des données."""

NR = {"-1": "Non renseigné"}

CARACTERISTIQUES = {
    "Num_Acc": ("Identifiant de l'accident, commun aux quatre tables", None),
    "jour": ("Jour du mois de l'accident", None),
    "mois": ("Mois de l'accident", None),
    "an": ("Année de l'accident", None),
    "hrmn": ("Heure et minutes de l'accident (hh:mm)", None),
    "lum": ("Conditions d'éclairage", {"1": "Plein jour", "2": "Crépuscule ou aube", "3": "Nuit sans éclairage public",
                                       "4": "Nuit avec éclairage public non allumé", "5": "Nuit avec éclairage public allumé", **NR}),
    "dep": ("Code INSEE du département (2A, 2B pour la Corse, 971 à 988 pour l'outre-mer)", None),
    "com": ("Code INSEE de la commune (arrondissement pour Paris, Lyon, Marseille)", None),
    "agg": ("Localisation", {"1": "Hors agglomération", "2": "En agglomération"}),
    "int": ("Type d'intersection", {"1": "Hors intersection", "2": "Intersection en X", "3": "Intersection en T",
                                    "4": "Intersection en Y", "5": "Intersection à plus de 4 branches", "6": "Giratoire",
                                    "7": "Place", "8": "Passage à niveau", "9": "Autre intersection", **NR}),
    "atm": ("Conditions atmosphériques", {"1": "Normale", "2": "Pluie légère", "3": "Pluie forte", "4": "Neige, grêle",
                                          "5": "Brouillard, fumée", "6": "Vent fort, tempête", "7": "Temps éblouissant",
                                          "8": "Temps couvert", "9": "Autre", **NR}),
    "col": ("Type de collision", {"1": "Deux véhicules, frontale", "2": "Deux véhicules, par l'arrière", "3": "Deux véhicules, par le côté",
                                  "4": "Trois véhicules et plus, en chaîne", "5": "Trois véhicules et plus, collisions multiples",
                                  "6": "Autre collision", "7": "Sans collision", **NR}),
    "adr": ("Adresse postale (renseignée pour les accidents en agglomération)", None),
    "lat": ("Latitude (WGS84, virgule décimale dans le fichier source)", None),
    "long": ("Longitude (WGS84, virgule décimale dans le fichier source)", None),
}

LIEUX = {
    "Num_Acc": ("Identifiant de l'accident", None),
    "catr": ("Catégorie de route", {"1": "Autoroute", "2": "Route nationale", "3": "Route départementale", "4": "Voie communale",
                                    "5": "Hors réseau public", "6": "Parc de stationnement ouvert à la circulation publique",
                                    "7": "Route de métropole urbaine", "9": "Autre"}),
    "voie": ("Numéro ou nom de la route", None),
    "v1": ("Indice numérique du numéro de route", None),
    "v2": ("Lettre indice alphanumérique de la route", None),
    "circ": ("Régime de circulation", {"1": "À sens unique", "2": "Bidirectionnelle", "3": "À chaussées séparées",
                                       "4": "Avec voies d'affectation variable", **NR}),
    "nbv": ("Nombre total de voies de circulation", None),
    "vosp": ("Voie réservée existant sur la route, que l'accident y ait lieu ou non",
             {"0": "Sans objet", "1": "Piste cyclable", "2": "Bande cyclable", "3": "Voie réservée", **NR}),
    "prof": ("Profil en long de la route", {"1": "Plat", "2": "Pente", "3": "Sommet de côte", "4": "Bas de côte", **NR}),
    "pr": ("Numéro du PR de rattachement", None),
    "pr1": ("Distance en mètres au PR", None),
    "plan": ("Tracé en plan", {"1": "Partie rectiligne", "2": "En courbe à gauche", "3": "En courbe à droite", "4": "En S", **NR}),
    "lartpc": ("Largeur du terre-plein central en mètres", None),
    "larrout": ("Largeur de la chaussée affectée à la circulation en mètres", None),
    "surf": ("État de la surface", {"1": "Normale", "2": "Mouillée", "3": "Flaques", "4": "Inondée", "5": "Enneigée", "6": "Boue",
                                    "7": "Verglacée", "8": "Corps gras, huile", "9": "Autre", **NR}),
    "infra": ("Aménagement, infrastructure", {"0": "Aucun", "1": "Souterrain, tunnel", "2": "Pont, autopont", "3": "Bretelle d'échangeur",
                                               "4": "Voie ferrée", "5": "Carrefour aménagé", "6": "Zone piétonne", "7": "Zone de péage",
                                               "8": "Chantier", "9": "Autre", **NR}),
    "situ": ("Situation de l'accident", {"0": "Aucune", "1": "Sur chaussée", "2": "Sur bande d'arrêt d'urgence", "3": "Sur accotement",
                                         "4": "Sur trottoir", "5": "Sur piste cyclable", "6": "Sur autre voie spéciale", "8": "Autre", **NR}),
    "vma": ("Vitesse maximale autorisée (km/h)", None),
}

CATV = {"0": "Indéterminable", "1": "Bicyclette", "2": "Cyclomoteur < 50 cm3", "3": "Voiturette", "7": "Véhicule léger",
        "10": "Véhicule utilitaire", "13": "Poids lourd 3,5 à 7,5 t", "14": "Poids lourd > 7,5 t", "15": "Poids lourd avec remorque",
        "16": "Tracteur routier seul", "17": "Tracteur routier avec semi-remorque", "20": "Engin spécial", "21": "Tracteur agricole",
        "30": "Scooter < 50 cm3", "31": "Motocyclette 50 à 125 cm3", "32": "Scooter 50 à 125 cm3", "33": "Motocyclette > 125 cm3",
        "34": "Scooter > 125 cm3", "35": "Quad léger", "36": "Quad lourd", "37": "Autobus", "38": "Autocar", "39": "Train",
        "40": "Tramway", "41": "3 roues motorisé ≤ 50 cm3", "42": "3 roues motorisé 50 à 125 cm3", "43": "3 roues motorisé > 125 cm3",
        "50": "Engin de déplacement personnel à moteur", "60": "Engin de déplacement personnel sans moteur",
        "80": "Vélo à assistance électrique", "99": "Autre véhicule"}

VEHICULES = {
    "Num_Acc": ("Identifiant de l'accident", None),
    "id_vehicule": ("Identifiant unique du véhicule, repris dans la table usagers", None),
    "num_veh": ("Identifiant du véhicule dans l'accident (A01, B01…)", None),
    "senc": ("Sens de circulation", {"0": "Inconnu", "1": "PK ou PR croissant", "2": "PK ou PR décroissant", "3": "Absence de repère", **NR}),
    "catv": ("Catégorie du véhicule", CATV),
    "obs": ("Obstacle fixe heurté", None),
    "obsm": ("Obstacle mobile heurté", {"0": "Aucun", "1": "Piéton", "2": "Véhicule", "4": "Véhicule sur rail", "5": "Animal domestique",
                                        "6": "Animal sauvage", "9": "Autre", **NR}),
    "choc": ("Point de choc initial", None),
    "manv": ("Manœuvre principale avant l'accident", None),
    "motor": ("Type de motorisation", {"0": "Inconnue", "1": "Hydrocarbures", "2": "Hybride électrique", "3": "Électrique",
                                       "4": "Hydrogène", "5": "Humaine", "6": "Autre", **NR}),
    "occutc": ("Nombre d'occupants dans le transport en commun", None),
}

USAGERS = {
    "Num_Acc": ("Identifiant de l'accident", None),
    "id_usager": ("Identifiant unique de l'usager (à partir de 2021)", None),
    "id_vehicule": ("Identifiant du véhicule de l'usager (pour un piéton : le véhicule qui l'a heurté)", None),
    "num_veh": ("Identifiant du véhicule dans l'accident", None),
    "place": ("Place occupée dans le véhicule", None),
    "catu": ("Catégorie d'usager", {"1": "Conducteur", "2": "Passager", "3": "Piéton"}),
    "grav": ("Gravité de l'atteinte", {"1": "Indemne", "2": "Tué (dans les 30 jours)", "3": "Blessé hospitalisé (plus de 24 h)",
                                        "4": "Blessé léger", **NR}),
    "sexe": ("Sexe de l'usager", {"1": "Masculin", "2": "Féminin", **NR}),
    "an_nais": ("Année de naissance", None),
    "trajet": ("Motif du déplacement", {"0": "Non renseigné", "1": "Domicile – travail", "2": "Domicile – école", "3": "Courses – achats",
                                         "4": "Utilisation professionnelle", "5": "Promenade – loisirs", "9": "Autre", **NR}),
    "secu1": ("Premier équipement de sécurité", {"0": "Aucun équipement", "1": "Ceinture", "2": "Casque", "3": "Dispositif enfants",
                                                   "4": "Gilet réfléchissant", "5": "Airbag (2RM, 3RM)", "6": "Gants",
                                                   "7": "Gants et airbag", "8": "Non déterminable", "9": "Autre", **NR}),
    "secu2": ("Deuxième équipement de sécurité (mêmes codes que secu1)", None),
    "secu3": ("Troisième équipement de sécurité (mêmes codes que secu1)", None),
    "locp": ("Localisation du piéton", None),
    "actp": ("Action du piéton", None),
    "etatp": ("Piéton seul ou non", None),
}

TABLES = {"caracteristiques": CARACTERISTIQUES, "lieux": LIEUX, "vehicules": VEHICULES, "usagers": USAGERS}

VELO = {"1", "80"}  # bicyclette, vélo à assistance électrique


def label(table, col, code):
    """Libellé d'un code, ou le code lui-même s'il n'est pas décrit."""
    spec = TABLES[table][col][1] or {}
    return spec.get(str(code), str(code))
