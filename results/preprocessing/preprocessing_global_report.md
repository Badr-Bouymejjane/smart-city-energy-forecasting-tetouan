
# Rapport global détaillé — Notebook 03 Prétraitement

## 1. Objectif général du notebook

Ce notebook correspond à la phase de prétraitement du pipeline KDD du projet **Smart City Energy Forecasting — Tetouan**. Il transforme le fichier brut `Tetuan City power consumption.csv` en datasets horaires propres, validés et prêts pour le notebook `04_feature_engineering.ipynb`.

Le prétraitement respecte la logique du projet : conserver le dataset brut dans `data/raw`, produire des fichiers propres dans `data/processed`, sauvegarder les scalers dans `models`, et générer un rapport de contrôle dans `results/preprocessing`.

## 2. Cellule 1 — Importation des bibliothèques et des fonctions `src`

Cette cellule importe les bibliothèques nécessaires au notebook :

- `pandas` pour les DataFrames et les séries temporelles ;
- `numpy` pour les contrôles numériques ;
- `Path` pour gérer les chemins de manière portable ;
- `json` pour sauvegarder le rapport de preprocessing ;
- `display` et `Markdown` pour afficher les tableaux et le rapport final dans le notebook.

Elle ajoute ensuite la racine du projet à `sys.path` afin de pouvoir importer les fonctions du dossier `src/`.

Les fonctions importées depuis `src.data_loader` centralisent le chargement du dataset, le renommage des colonnes, la conversion temporelle, la conversion numérique, la création de `target` et `total_load`, et l'audit qualité.

Les fonctions importées depuis `src.preprocessing` centralisent les opérations de preprocessing : contrôle des 6 mesures par heure, resampling horaire, recherche des heures manquantes, gestion des valeurs manquantes, contrôle physique, détection des anomalies, annotation des pics de charge, split chronologique, scaling sans fuite de données et sauvegarde des sorties.

Cette organisation rend le notebook plus professionnel : le notebook décrit et exécute le pipeline, tandis que le code réutilisable est placé dans `src/`.

## 3. Cellule 2 — Définition des chemins du projet

Cette cellule définit les chemins principaux du projet :

- fichier brut : `C:\Users\Badr\UB\0_Inbox\00-projects-code\dm-pfm-project\smart-city-energy-forecasting-tetouan\data\raw\Tetuan City power consumption.csv` ;
- dossier des datasets transformés : `C:\Users\Badr\UB\0_Inbox\00-projects-code\dm-pfm-project\smart-city-energy-forecasting-tetouan\data\processed` ;
- dossier des scalers et modèles : `C:\Users\Badr\UB\0_Inbox\00-projects-code\dm-pfm-project\smart-city-energy-forecasting-tetouan\models` ;
- dossier du rapport de preprocessing : `C:\Users\Badr\UB\0_Inbox\00-projects-code\dm-pfm-project\smart-city-energy-forecasting-tetouan\results\preprocessing`.

Le code suppose une structure GitHub professionnelle où le notebook se trouve dans `notebooks/` et les données dans `data/raw/`. Une alternative est prévue si le CSV est placé directement à la racine du projet.

Les dossiers de sortie sont créés automatiquement avec `mkdir(parents=True, exist_ok=True)`, ce qui évite les erreurs si les dossiers n'existent pas encore.

## 4. Cellule 3 — Chargement standardisé du dataset Tetouan

Le fichier brut contient `52416` observations et `9` colonnes. La fonction `load_tetouan_data()` réalise automatiquement les étapes suivantes :

1. lecture du CSV ;
2. nettoyage des noms de colonnes, notamment les doubles espaces dans les noms des zones ;
3. renommage technique des variables ;
4. conversion de la colonne temporelle en `datetime` ;
5. conversion des variables météo et consommation en numérique ;
6. tri chronologique ;
7. suppression contrôlée des doublons temporels si nécessaire ;
8. création de `target = zone1_power` ;
9. création de `total_load = zone1_power + zone2_power + zone3_power` ;
10. indexation temporelle.

Résultat obtenu : le dataset chargé contient `52416` lignes et `10` colonnes, avec une fréquence brute inférée de `10min`.

L'audit qualité confirme que les données sont exploitables pour la suite du pipeline.

## 5. Cellule 4 — Contrôle de cohérence de `target` et `total_load`

Cette cellule vérifie deux règles essentielles du projet :

- `target` doit être exactement égale à `zone1_power` ;
- `total_load` doit être égale à la somme des trois zones.

Résultats :

- `target = zone1_power` : `True` ;
- `total_load = zone1_power + zone2_power + zone3_power` : `True`.

Ce contrôle est important parce que `target` est la variable cible principale du projet. Une erreur dans cette colonne fausserait le feature engineering, la modélisation et l'évaluation.

## 6. Cellule 5 — Rééchantillonnage horaire et contrôle temporel

Le dataset brut est mesuré toutes les 10 minutes. Pour construire une série horaire fiable, il ne suffit pas de faire une moyenne par heure : il faut vérifier que chaque heure contient exactement 6 mesures de 10 minutes.

La fonction `check_10min_measurements_per_hour()` vérifie cette condition. Le résultat obtenu est :

- nombre attendu de mesures par heure : `6` ;
- heures contrôlées : `8736` ;
- heures avec un nombre incorrect de mesures : `0`.

Ensuite, `resample_hourly()` calcule la moyenne horaire des variables numériques. Le dataset horaire obtenu contient `8736` lignes et `10` colonnes.

La fonction `find_missing_hours()` vérifie que la grille horaire est complète. Nombre d'heures manquantes détectées : `0`.

Ce choix est aligné avec la stratégie du projet : utiliser la granularité 10 minutes pour l'audit et l'EDA fine, puis utiliser la granularité horaire pour la modélisation principale.

## 7. Cellule 6 — Gestion sécurisée des valeurs manquantes

La fonction `handle_missing_values()` applique une stratégie prudente :

1. interpolation temporelle limitée pour les petits trous ;
2. forward fill limité ;
3. suppression contrôlée des lignes restantes si des valeurs manquantes persistent.

Le notebook évite volontairement le backfill global, car il peut utiliser de l'information future pour reconstruire le passé.

Résultats :

- valeurs manquantes avant traitement : `0` ;
- valeurs manquantes après traitement : `0` ;
- dimensions après nettoyage : `(8736, 15)`.

Comme le dataset Tetouan est déjà propre, cette étape sert surtout à rendre le pipeline robuste.

## 8. Cellule 7 — Contrôle des plages physiques et détection exploratoire des anomalies

La fonction `check_physical_ranges()` vérifie les incohérences impossibles ou suspectes :

- consommation négative ;
- humidité hors intervalle `[0, 100]` ;
- température hors plage réaliste ;
- vitesse du vent négative.

Somme des incohérences physiques détectées : `0`.

La fonction `summarize_outliers()` applique ensuite un Rolling Z-Score basé sur le passé. Cette méthode compare chaque valeur à son contexte récent au lieu de la comparer à toute la distribution globale. C'est plus adapté aux séries énergétiques, car la consommation dépend fortement de l'heure, du jour et de la saison.

Les anomalies détectées ne sont pas automatiquement supprimées. Dans un projet énergétique, un pic peut représenter un vrai événement métier et non une erreur technique.

## 9. Cellule 8 — Annotation des pics de charge et validation finale stricte

La fonction `annotate_load_outliers()` ajoute les colonnes suivantes :

- `target_rolling_zscore` ;
- `total_load_rolling_zscore` ;
- `is_target_outlier` ;
- `is_total_load_outlier` ;
- `is_load_outlier`.

Les Rolling Z-Scores initiaux impossibles à calculer au début de la série sont remplacés par `0`, ce qui signifie qu'aucun écart local n'est détecté au début du dataset.

Résultats :

- anomalies sur `target` : `0` ;
- anomalies sur `total_load` : `0` ;
- anomalies de charge globales : `0`.

La fonction `validate_clean_hourly_dataset()` bloque le notebook si le dataset contient encore des valeurs manquantes, des doublons temporels ou une fréquence non horaire.

Validation finale :

- valeurs manquantes finales : `0` ;
- doublons finaux : `0` ;
- fréquence finale : `h`.

## 10. Cellule 9 — Split chronologique train / validation / test

La fonction `temporal_train_val_test_split()` découpe le dataset selon l'ordre temporel :

- train : passé ;
- validation : période intermédiaire ;
- test : futur.

Aucun shuffle n'est utilisé, car mélanger le passé et le futur créerait une fuite d'information.

Résultats :

- train : `(6115, 15)` de `2017-01-01 00:00:00` à `2017-09-12 18:00:00` ;
- validation : `(1310, 15)` de `2017-09-12 19:00:00` à `2017-11-06 08:00:00` ;
- test : `(1311, 15)` de `2017-11-06 09:00:00` à `2017-12-30 23:00:00`.

Ce découpage prépare correctement la modélisation temporelle.

## 11. Cellule 10 — Normalisation de base sans data leakage

La normalisation est faite avec `scale_train_val_test()`.

Règle appliquée :

- le scaler des features est ajusté uniquement sur `train_df` ;
- le scaler de la cible est ajusté uniquement sur `train_df` ;
- validation et test sont seulement transformés.

Les variables explicatives utilisées dans ce notebook sont uniquement les variables météo de base :

`['temperature', 'humidity', 'wind_speed', 'general_diffuse_flows', 'diffuse_flows']`

Les colonnes de consommation instantanée (`target`, `zone1_power`, `zone2_power`, `zone3_power`, `total_load`) sont conservées dans les fichiers propres, mais elles ne sont pas utilisées directement comme variables explicatives. Elles seront utilisées plus tard uniquement sous forme de lags ou de rolling features basées sur le passé.

Cette règle évite le data leakage.

## 12. Cellule 11 — Sauvegarde des datasets, fichiers normalisés, scalers et rapport JSON

La fonction `save_preprocessing_outputs()` sauvegarde les fichiers suivants dans `data/processed` :

- dataset horaire complet nettoyé ;
- train propre ;
- validation propre ;
- test propre ;
- fichiers normalisés de base `X` et `y`.

La fonction `save_scalers()` sauvegarde les scalers dans `models`.

Le rapport JSON est sauvegardé ici :

`C:\Users\Badr\UB\0_Inbox\00-projects-code\dm-pfm-project\smart-city-energy-forecasting-tetouan\results\preprocessing\preprocessing_report.json`

Ce rapport permet de tracer automatiquement les dimensions, la période couverte, les fréquences, les valeurs manquantes, les doublons, les anomalies, les features utilisées et les fichiers sauvegardés.

## 13. Cellule 12 — Résumé final du preprocessing

Cette cellule affiche un résumé compact du pipeline : dimensions, période, fréquence, valeurs manquantes, doublons, anomalies, features de base, splits et rapport sauvegardé.

Elle confirme que le notebook a produit un dataset propre, horaire, sans valeurs manquantes, sans doublons et prêt pour le feature engineering.

## 14. Règles importantes pour le notebook `04_feature_engineering.ipynb`

Les fichiers propres conservent les colonnes de consommation instantanée. Cela est volontaire, car ces colonnes sont nécessaires pour construire des variables retardées.

Règle autorisée :

- `target_lag_1h` ;
- `target_lag_24h` ;
- `target_lag_168h` ;
- rolling mean/std/min/max calculés avec `shift(1)`.

Règle interdite :

- utiliser `target`, `zone1_power`, `zone2_power`, `zone3_power` ou `total_load` au même timestamp comme variables explicatives directes ;
- utiliser les z-scores de charge et les indicateurs d'outliers de charge comme features prédictives directes si ces informations ne sont pas disponibles au moment de la prédiction.

## 15. Verdict final

Le notebook simplifié est aligné avec le projet et avec l'architecture GitHub attendue. Il conserve les garanties scientifiques de l'ancien notebook, mais il supprime les définitions longues et répétitives en utilisant les fonctions du dossier `src/`.

Le preprocessing est validé :

- dataset brut chargé correctement ;
- fréquence 10 minutes contrôlée ;
- resampling horaire validé ;
- aucune heure manquante ;
- aucune valeur manquante finale ;
- aucune incohérence physique détectée ;
- anomalies documentées et conservées ;
- split chronologique correct ;
- normalisation sans data leakage ;
- sorties sauvegardées pour le notebook suivant.
