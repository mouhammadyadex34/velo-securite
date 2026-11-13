# Dictionnaire des données

Source : bases annuelles des accidents corporels de la circulation routière (BAAC, ONISR), data.gouv.fr, Licence Ouverte. Années 2020 à 2024, restreintes aux accidents impliquant au moins une bicyclette (`catv = 1`) ou un vélo à assistance électrique (`catv = 80`).

Clé de jointure : `Num_Acc` relie les quatre tables ; `id_vehicule` relie un usager à son véhicule. « Rempli » compte les valeurs ni vides ni égales à `-1` (non renseigné).

## Contrôles de qualité

- Accidents sans coordonnées : 0 ; hors métropole : 958.
- Accidents avec plusieurs lignes dans `lieux` : {'2020': 0, '2021': 0, '2022': 0, '2023': 2602, '2024': 2515} (changement de format en 2023).
- Piétons rattachés à un vélo, exclus des cyclistes : 1679.
- Codes commune absents du référentiel actuel (fusions de communes) : 57.
- Cyclistes à gravité non renseignée, exclus : 11.
- Format de `mois` selon l'année : {'2020': 'sans zéro (3)', '2021': 'sur deux chiffres (03)', '2022': 'sur deux chiffres (03)', '2023': 'sur deux chiffres (03)', '2024': 'sur deux chiffres (03)'} ; d'où 21 valeurs distinctes pour 12 mois.

## Table `caracteristiques`

27 885 lignes : une ligne par accident : quand  où  dans quelles conditions.

| Variable | Description | Rempli | Valeurs distinctes | Codes ou exemples |
|---|---|---:|---:|---|
| `Num_Acc` | Identifiant de l'accident, commun aux quatre tables | 100% | 27885 | `202000000011` ; `202000000014` ; `202000000031` |
| `jour` | Jour du mois de l'accident | 100% | 31 | `5` ; `7` ; `4` |
| `mois` | Mois de l'accident | 100% | 21 | `3` ; `9` ; `6` |
| `an` | Année de l'accident | 100% | 5 | `2020` ; `2021` ; `2022` |
| `hrmn` | Heure et minutes de l'accident (hh:mm) | 100% | 1202 | `11:50` ; `13:20` ; `20:00` |
| `lum` | Conditions d'éclairage | 100% | 6 | `1` Plein jour (78%) ; `5` Nuit avec éclairage public allumé (13%) ; `2` Crépuscule ou aube (6%) ; `3` Nuit sans éclairage public (2%) ; `4` Nuit avec éclairage public non allumé (0%) ; `-1` Non renseigné (0%) |
| `dep` | Code INSEE du département (2A, 2B pour la Corse, 971 à 988 pour l'outre-mer) | 100% | 104 | `59` ; `51` ; `75` |
| `com` | Code INSEE de la commune (arrondissement pour Paris, Lyon, Marseille) | 100% | 6059 | `59143` ; `51454` ; `75117` |
| `agg` | Localisation | 100% | 2 | `2` En agglomération (83%) ; `1` Hors agglomération (17%) |
| `int` | Type d'intersection | 100% | 9 | `1` Hors intersection (46%) ; `2` Intersection en X (17%) ; `3` Intersection en T (17%) ; `6` Giratoire (10%) ; `9` Autre intersection (4%) ; `4` Intersection en Y (3%) ; … |
| `atm` | Conditions atmosphériques | 100% | 10 | `1` Normale (83%) ; `2` Pluie légère (8%) ; `8` Temps couvert (4%) ; `7` Temps éblouissant (3%) ; `3` Pluie forte (1%) ; `9` Autre (0%) ; … |
| `col` | Type de collision | 99% | 8 | `3` Deux véhicules, par le côté (53%) ; `2` Deux véhicules, par l'arrière (12%) ; `6` Autre collision (12%) ; `1` Deux véhicules, frontale (11%) ; `7` Sans collision (9%) ; `-1` Non renseigné (1%) ; … |
| `adr` | Adresse postale (renseignée pour les accidents en agglomération) | 100% | 17204 | `BEAUCHAMP  (RUE LEON )` ; `Avenue de l’Europe` ; `BOULEVARD DE REIMS` |
| `lat` | Latitude (WGS84, virgule décimale dans le fichier source) | 100% | 27611 | `50,6785000` ; `49,2556464` ; `48,8891650` |
| `long` | Longitude (WGS84, virgule décimale dans le fichier source) | 100% | 27680 | `2,8742000` ; `4,0611947` ; `2,2975300` |

## Table `lieux`

33 045 lignes : une ligne par voie concernée (plusieurs lignes par accident en carrefour depuis 2023).

| Variable | Description | Rempli | Valeurs distinctes | Codes ou exemples |
|---|---|---:|---:|---|
| `Num_Acc` | Identifiant de l'accident | 100% | 27885 | `202000000011` ; `202000000014` ; `202000000031` |
| `catr` | Catégorie de route | 100% | 8 | `4` Voie communale (65%) ; `3` Route départementale (30%) ; `7` Route de métropole urbaine (3%) ; `2` Route nationale (2%) ; `9` Autre (1%) ; `6` Parc de stationnement ouvert à la circulation publique (0%) ; … |
| `voie` | Numéro ou nom de la route | 100% | 11738 | `22` ; `N/A` ; `1516` |
| `v1` | Indice numérique du numéro de route | 80% | 4 | `0` ; `2` ; `3` |
| `v2` | Lettre indice alphanumérique de la route | 100% | 29 | `N/A` ; `A` ; `D` |
| `circ` | Régime de circulation | 94% | 5 | `2` Bidirectionnelle (63%) ; `1` À sens unique (24%) ; `-1` Non renseigné (6%) ; `3` À chaussées séparées (6%) ; `4` Avec voies d'affectation variable (1%) |
| `nbv` | Nombre total de voies de circulation | 95% | 15 | `3` ; `2` ; `4` |
| `vosp` | Voie réservée existant sur la route, que l'accident y ait lieu ou non | 96% | 5 | `0` Sans objet (64%) ; `1` Piste cyclable (19%) ; `2` Bande cyclable (7%) ; `3` Voie réservée (5%) ; `-1` Non renseigné (4%) |
| `prof` | Profil en long de la route | 100% | 5 | `1` Plat (80%) ; `2` Pente (17%) ; `4` Bas de côte (2%) ; `3` Sommet de côte (1%) ; `-1` Non renseigné (0%) |
| `pr` | Numéro du PR de rattachement | 69% | 185 | `(1)` ; `0` ; `15` |
| `pr1` | Distance en mètres au PR | 69% | 970 | `(1)` ; `0` ; `625` |
| `plan` | Tracé en plan | 100% | 5 | `1` Partie rectiligne (85%) ; `2` En courbe à gauche (8%) ; `3` En courbe à droite (6%) ; `4` En S (1%) ; `-1` Non renseigné (0%) |
| `lartpc` | Largeur du terre-plein central en mètres | 0% | 15 | `0` ; `1,5` ; `10,2` |
| `larrout` | Largeur de la chaussée affectée à la circulation en mètres | 11% | 56 | `4` ; `5` ; `9` |
| `surf` | État de la surface | 100% | 10 | `1` Normale (85%) ; `2` Mouillée (14%) ; `9` Autre (0%) ; `7` Verglacée (0%) ; `3` Flaques (0%) ; `-1` Non renseigné (0%) ; … |
| `infra` | Aménagement, infrastructure | 94% | 10 | `0` Aucun (79%) ; `5` Carrefour aménagé (8%) ; `-1` Non renseigné (6%) ; `9` Autre (4%) ; `6` Zone piétonne (1%) ; `2` Pont, autopont (1%) ; … |
| `situ` | Situation de l'accident | 100% | 8 | `1` Sur chaussée (77%) ; `5` Sur piste cyclable (16%) ; `6` Sur autre voie spéciale (2%) ; `8` Autre (2%) ; `4` Sur trottoir (2%) ; `3` Sur accotement (1%) ; … |
| `vma` | Vitesse maximale autorisée (km/h) | 96% | 27 | `50` ; `30` ; `70` |

## Table `vehicules`

51 735 lignes : une ligne par véhicule impliqué.

| Variable | Description | Rempli | Valeurs distinctes | Codes ou exemples |
|---|---|---:|---:|---|
| `Num_Acc` | Identifiant de l'accident | 100% | 27885 | `202000000011` ; `202000000014` ; `202000000031` |
| `id_vehicule` | Identifiant unique du véhicule, repris dans la table usagers | 100% | 51735 | `154 742 255` ; `154 742 256` ; `154 742 248` |
| `num_veh` | Identifiant du véhicule dans l'accident (A01, B01…) | 100% | 48 | `A01` ; `B01` ; `Z01` |
| `senc` | Sens de circulation | 100% | 5 | `1` PK ou PR croissant (42%) ; `2` PK ou PR décroissant (31%) ; `3` Absence de repère (19%) ; `0` Inconnu (7%) ; `-1` Non renseigné (0%) |
| `catv` | Catégorie du véhicule | 100% | 31 | `1` Bicyclette (50%) ; `7` Véhicule léger (32%) ; `80` Vélo à assistance électrique (6%) ; `10` Véhicule utilitaire (4%) ; `33` Motocyclette > 125 cm3 (1%) ; `50` Engin de déplacement personnel à moteur (1%) ; … |
| `obs` | Obstacle fixe heurté | 100% | 19 | `0` ; `12` ; `6` |
| `obsm` | Obstacle mobile heurté | 100% | 8 | `2` Véhicule (76%) ; `0` Aucun (13%) ; `9` Autre (8%) ; `1` Piéton (3%) ; `4` Véhicule sur rail (0%) ; `5` Animal domestique (0%) ; … |
| `choc` | Point de choc initial | 100% | 11 | `2` ; `5` ; `4` |
| `manv` | Manœuvre principale avant l'accident | 100% | 28 | `15` ; `19` ; `16` |
| `motor` | Type de motorisation | 100% | 8 | `5` Humaine (48%) ; `1` Hydrocarbures (36%) ; `3` Électrique (8%) ; `0` Inconnue (6%) ; `2` Hybride électrique (2%) ; `6` Autre (1%) ; … |
| `occutc` | Nombre d'occupants dans le transport en commun | 1% | 6 | `1` ; `4` ; `2` |

## Table `usagers`

55 056 lignes : une ligne par personne impliquée (conducteur  passager  piéton).

| Variable | Description | Rempli | Valeurs distinctes | Codes ou exemples |
|---|---|---:|---:|---|
| `Num_Acc` | Identifiant de l'accident | 100% | 27885 | `202000000011` ; `202000000014` ; `202000000031` |
| `id_vehicule` | Identifiant du véhicule de l'usager (pour un piéton : le véhicule qui l'a heurté) | 100% | 51378 | `154 742 255` ; `154 742 256` ; `154 742 248` |
| `num_veh` | Identifiant du véhicule dans l'accident | 100% | 48 | `A01` ; `B01` ; `Y01` |
| `place` | Place occupée dans le véhicule | 100% | 11 | `1` ; `10` ; `2` |
| `catu` | Catégorie d'usager | 100% | 3 | `1` Conducteur (93%) ; `2` Passager (4%) ; `3` Piéton (3%) |
| `grav` | Gravité de l'atteinte | 100% | 5 | `1` Indemne (45%) ; `4` Blessé léger (39%) ; `3` Blessé hospitalisé (plus de 24 h) (13%) ; `2` Tué (dans les 30 jours) (2%) ; `-1` Non renseigné (0%) |
| `sexe` | Sexe de l'usager | 97% | 3 | `1` Masculin (70%) ; `2` Féminin (27%) ; `-1` Non renseigné (3%) |
| `an_nais` | Année de naissance | 97% | 104 | `1934` ; `2005` ; `1936` |
| `trajet` | Motif du déplacement | 97% | 8 | `5` Promenade – loisirs (37%) ; `0` Non renseigné (20%) ; `1` Domicile – travail (17%) ; `9` Autre (10%) ; `4` Utilisation professionnelle (8%) ; `3` Courses – achats (3%) ; … |
| `secu1` | Premier équipement de sécurité | 97% | 9 | `1` Ceinture (32%) ; `8` Non déterminable (27%) ; `2` Casque (27%) ; `0` Aucun équipement (11%) ; `-1` Non renseigné (3%) ; `4` Gilet réfléchissant (0%) ; … |
| `secu2` | Deuxième équipement de sécurité (mêmes codes que secu1) | 61% | 11 | `8` ; `0` ; `4` |
| `secu3` | Troisième équipement de sécurité (mêmes codes que secu1) | 2% | 10 | `9` ; `0` ; `6` |
| `locp` | Localisation du piéton | 51% | 11 | `0` ; `2` ; `1` |
| `actp` | Action du piéton | 51% | 13 | `0` ; `3` ; `1` |
| `etatp` | Piéton seul ou non | 3% | 4 | `2` ; `1` ; `3` |
| `id_usager` | Identifiant unique de l'usager (à partir de 2021) | 82% | 45304 | `267 638` ; `267 639` ; `267 625` |

## Seconde source : inventaire des aménagements cyclables

Aménagements cyclables France métropolitaine (Geovelo et contributeurs OpenStreetMap, data.gouv.fr, licence ODbL) : 417 172 tronçons, mises à jour du 2007-04-01 au 2026-10-29. Chaque tronçon décrit l'aménagement du côté droit (`ame_d`) et du côté gauche (`ame_g`). La table dérivée ci-dessous est diffusée sous la même licence ODbL.

| Catégorie | Valeurs de `ame_d` ou `ame_g` | Longueur |
|---|---|---:|
| Séparé de la circulation | amenagement mixte pieton velo hors voie verte; double sens cyclable piste; piste cyclable; voie verte | 39 882 km |
| Marquage sur chaussée | accotement revetu hors cvcb; bande cyclable; chaussee a voie centrale banalisee; couloir bus+velo; double sens cyclable bande; double sens cyclable non materialise; velo rue | 20 635 km |

Table dérivée `data/processed/proximite_amenagements.csv`, une ligne par accident de métropole :

| Variable | Description |
|---|---|
| `Num_Acc` | Identifiant de l'accident (BAAC) |
| `dist_separe_m` | Distance en mètres au plus proche aménagement séparé (vide au-delà de 500 m) |
| `dist_marquage_m` | Distance en mètres au plus proche marquage cyclable (vide au-delà de 500 m) |
| `proximite` | Classe : aménagement séparé à moins de 20 m, sinon marquage seul à moins de 20 m, sinon aménagement entre 20 et 50 m, sinon aucun à moins de 50 m |
