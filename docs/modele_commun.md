# Modèle commun des événements de sécurité à vélo

Les données sur la sécurité des cyclistes viennent de sources très différentes : procès-verbaux d'accidents, inventaires d'aménagements, enquêtes auprès des cyclistes, capteurs embarqués sur des vélos. Chacune a son vocabulaire, sa précision et ses biais. Ce modèle les ramène à un format unique pour pouvoir les croiser.

Il est implémenté dans [`src/modele_commun.py`](../src/modele_commun.py) pour les deux sources du dépôt (BAAC et inventaire des aménagements). La fonction `valider()` contrôle chaque enregistrement ; les 29 446 cyclistes de la BAAC passent le contrôle. Un exemple d'enregistrement est dans [`exemple_evenements.json`](exemple_evenements.json).

## Principes

1. **Un enregistrement par personne et par événement.** Un accident avec deux cyclistes donne deux enregistrements ; l'identifiant de la source (`id_source`) les relie.
2. **La précision fait partie de la donnée.** Une heure « à la minute » et une date « au jour près » ne se comparent pas de la même façon ; une position GPS de capteur et une position géocodée depuis une adresse non plus. Les champs `precision_temps` et `precision_position_m` le disent.
3. **Ce que dit la source est séparé de ce qu'on en déduit.** `contexte.sur_piste_selon_source` est la déclaration du procès-verbal ; `infrastructure` vient du croisement avec l'inventaire. Les deux peuvent se contredire, et c'est une information en soi (voir la concordance dans le README).
4. **La provenance est conservée** : jeu de données, licence, champs d'origine. Un résultat peut toujours être remonté jusqu'à sa source.

## Champs

| Champ | Type | Description |
|---|---|---|
| `id` | texte | Identifiant unique dans le modèle (`source:identifiant:véhicule:rang`) |
| `type` | texte | `accident_corporel`, `presque_accident`, `signalement`, `mesure_capteur` |
| `source`, `id_source` | texte | Source et identifiant dans la source |
| `debut` | date-heure ISO 8601 | Début de l'événement, heure locale |
| `precision_temps` | texte | `minute`, `heure`, `jour` ou `mois` |
| `lon`, `lat` | nombre | Position en WGS84 |
| `precision_position_m` | nombre ou vide | Incertitude de position en mètres, si la source la connaît |
| `mode` | texte | `velo`, `vae` (extensible : trottinette…) |
| `role` | texte | `conducteur`, `passager` |
| `gravite` | texte | Échelle commune : `indemne`, `blesse_leger`, `blesse_hospitalise`, `tue`, `sans_objet` (presque-accident), `inconnue` |
| `contexte` | objet | Conditions déclarées par la source : agglomération, éclairage, antagoniste, commune… |
| `infrastructure` | objet | Aménagement cyclable le plus proche et distances, avec la source utilisée |
| `provenance` | objet | Jeu de données, licence, champs d'origine |

## Correspondances

| Modèle | BAAC (implémenté) | Inventaire des aménagements (implémenté) | Enquête auprès des cyclistes (prévu) | Capteur embarqué (prévu) |
|---|---|---|---|---|
| `type` | `accident_corporel` | — (sert à `infrastructure`) | `presque_accident` ou `accident_corporel` déclaré | `mesure_capteur`, ou `presque_accident` détecté |
| `debut`, `precision_temps` | `an`, `mois`, `jour`, `hrmn` → minute | `date_maj` (date de mise à jour, pas de construction) | date et créneau déclarés → heure ou jour | horodatage de l'appareil → seconde |
| `lon`, `lat` | `lat`, `long` | géométrie des tronçons | adresse ou point placé sur une carte | GPS |
| `precision_position_m` | non publiée | — | dépend de la saisie | fournie par le GPS |
| `gravite` | `grav` : 1→indemne, 4→léger, 3→hospitalisé, 2→tué | — | déclarée | `sans_objet` |
| `contexte.antagoniste` | véhicule le plus lourd impliqué (`catv`) | — | déclaré | non observé |
| `infrastructure` | `situ`, `vosp` (déclaratif) | `ame_d`, `ame_g` regroupés en séparé / marquage | déduit de la position | déduit de la position |

Les colonnes « prévu » décrivent comment ces sources entreraient dans le modèle ; elles ne sont pas encore implémentées et devront être validées sur des données réelles.

## Ce que le modèle ne résout pas

- **L'exposition** : aucune de ces sources ne dit combien de cyclistes passent à un endroit. Des compteurs de passages seraient une source de plus, avec un `type` dédié.
- **Le décalage temporel** : l'inventaire décrit les aménagements de 2026, les accidents vont de 2020 à 2024. Un aménagement construit après un accident est compté à tort.
- **Les doublons entre sources** : un même accident peut être déclaré à la police et dans une enquête. Le rapprochement (même lieu, même moment, à la précision près) reste à écrire.
