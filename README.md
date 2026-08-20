# Data Quality API & Streamlit Dashboard

Projet réalisé dans le cadre du programme data upskilling.

## Objectifs
- Créer et requêter une API
- Détecter et résoudre des problèmes de data quality
- Manipuler de la donnée (SQL / Pandas / DuckDB / Spark)
- Visualiser les résultats via une app Streamlit

## Statut
🚧 En cours de construction

## Le format Parquet vs CSV — ce qu'on en a retenu

Dans ce projet, les données brutes sont stockées en CSV (`data/raw/`), mais
une fois transformées, elles sont sauvegardées en **Parquet** (`data/processed/`).
Petit résumé de pourquoi ces deux formats ne jouent pas le même rôle.

### La différence fondamentale : ligne vs colonne

- **CSV** est un format "ligne" (*row-oriented*) : chaque ligne du fichier
  correspond à une ligne de données, colonnes séparées par des virgules,
  tout en texte brut.
- **Parquet** est un format "colonne" (*columnar*) : les données sont
  stockées colonne par colonne, chacune avec son propre type et sa
  propre compression.

### Ce que ça change concrètement

| Critère | CSV | Parquet |
|---|---|---|
| Lisible à l'œil (Notepad, Excel...) | ✅ Oui | ❌ Non (format binaire) |
| Typage des colonnes | ❌ Tout est du texte, à retyper à la lecture | ✅ Schéma typé intégré au fichier |
| Compression | Faible | Forte (données homogènes par colonne) |
| Lire seulement certaines colonnes | ❌ Impossible (il faut tout lire) | ✅ Oui (on ne charge que les colonnes utiles) |
| Usage typique | Échange simple, petits volumes | Stockage analytique, gros volumes, data lakes |

### Pourquoi ça compte en pratique

Quand une requête ne porte que sur 2-3 colonnes d'une table qui en a 30,
Parquet ne lit **que** ces colonnes sur le disque — un CSV, lui, doit être
lu intégralement, ligne par ligne, colonnes inutiles comprises. Sur de
gros volumes, l'écart de vitesse et de taille de fichier devient très
significatif, ce qui explique pourquoi Parquet est devenu le format
standard des pipelines data en entreprise (data lakes, Spark, BigQuery...),
là où le CSV reste surtout utilisé pour des échanges simples ou de petits
volumes.

### La limite qu'on a observée

Sur notre volume de test (15 lignes), la différence de taille entre CSV et
Parquet n'est pas vraiment démonstrative — l'avantage de Parquet se
révèle à partir d'un volume plus réaliste (des milliers/millions de lignes),
pas sur un petit échantillon.
