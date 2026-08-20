"""
Script de transformation : lit l'ensemble des fichiers CSV bruts stockés
dans data/raw/ (un fichier par mois), les combine, les agrège par jour,
filtre les lignes non fiables, et calcule une moyenne glissante par
jour de semaine.
"""

import duckdb
import duckdb
from pathlib import Path

RAW_DATA_GLOB = "data/raw/*.csv"
PROCESSED_DIR = Path("data/processed/filtered")

RAW_DATA_GLOB = "data/raw/*.csv"


def read_raw_data():
    """
    Lit tous les fichiers CSV présents dans data/raw/ et les combine
    en une seule table. DuckDB gère nativement les motifs "glob" (le *)
    et empile automatiquement les fichiers qui partagent les mêmes colonnes.
    """
    return duckdb.sql(f"SELECT * FROM read_csv_auto('{RAW_DATA_GLOB}')")


def daily_traffic():
    """
    Regroupe la donnée heure par heure en trafic journalier :
    un GROUP BY sur la date, avec un SUM du nombre de visiteurs.
    C'est tout l'intérêt d'avoir généré la donnée heure par heure au
    départ : elle peut ensuite être agrégée à n'importe quel niveau
    (jour, semaine, mois...) selon le besoin.
    """
    return duckdb.sql(f"""
        SELECT
            date,
            SUM(nombre_visiteurs) AS total_visiteurs
        FROM read_csv_auto('{RAW_DATA_GLOB}')
        GROUP BY date
        ORDER BY date
    """)


def filter_valid_rows():
    """
    (TRANSFORM DATA 3/7) Filtre les lignes non fiables, sur deux critères
    précis seulement :
    - id_capteur manquant (NULL)
    - unite incohérente (tout ce qui n'est pas exactement "visiteurs",
      ce qui exclut au passage les unités vides/NULL sans condition
      supplémentaire : en SQL, NULL = 'visiteurs' n'est jamais vrai)

    Volontairement, on ne filtre PAS ici les valeurs de nombre_visiteurs
    jugées trop faibles ou trop fortes : la détection des valeurs
    aberrantes viendra dans une étape ultérieure, séparée de ce
    nettoyage basique.
    """
    return duckdb.sql(f"""
        SELECT *
        FROM read_csv_auto('{RAW_DATA_GLOB}')
        WHERE id_capteur IS NOT NULL
          AND unite = 'visiteurs'
    """)


def daily_traffic_clean():
    """
    Recalcule le trafic journalier, mais cette fois à partir des lignes
    valides uniquement (issues de filter_valid_rows), en conservant
    id_capteur / id_magasin : ce sont les dimensions dont on aura besoin
    pour la window function de l'étape suivante (un même capteur/lieu
    peut avoir plusieurs séries de trafic à comparer entre elles).
    """
    valid_rows = filter_valid_rows()
    return duckdb.sql("""
        SELECT
            date,
            id_capteur,
            id_magasin,
            SUM(nombre_visiteurs) AS total_visiteurs
        FROM valid_rows
        GROUP BY date, id_capteur, id_magasin
        ORDER BY date
    """)


def add_same_weekday_rolling_average():
    """
    (TRANSFORM DATA 4/7) Window function : pour chaque ligne (un jour,
    un capteur, un lieu), calcule la moyenne du trafic sur les 4
    dernières occurrences du MÊME jour de la semaine (par exemple, pour
    un jeudi donné : la moyenne des 4 jeudis précédents), par capteur et
    par lieu.

    PARTITION BY isole chaque groupe (jour de semaine x lieu x capteur)
    pour que la fenêtre ne mélange jamais un jeudi avec un mardi. La
    fenêtre "ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING" ne regarde que les
    4 lignes précédentes DANS CE GROUPE, sans compter la ligne courante :
    on compare chaque jour à son historique, pas à lui-même.

    Tant qu'on n'a pas encore 4 occurrences précédentes du même jour de
    semaine dans l'historique (ex. le tout premier jeudi observé), la
    moyenne est calculée sur les occurrences disponibles, voire NULL s'il
    n'y en a aucune : c'est un comportement normal en début de période.
    """
    daily = daily_traffic_clean()
    return duckdb.sql("""
        SELECT
            date,
            dayname(date) AS jour_semaine,
            id_capteur,
            id_magasin,
            total_visiteurs,
            AVG(total_visiteurs) OVER (
                PARTITION BY dayname(date), id_magasin, id_capteur
                ORDER BY date
                ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING
            ) AS moyenne_4_derniers_memes_jours
        FROM daily
        ORDER BY date
    """)

def add_pct_change():
    """
    (TRANSFORM DATA 5/7) Ajoute une colonne pct_change : l'écart en
    pourcentage entre le trafic du jour et la moyenne glissante des 4
    dernières occurrences du même jour de semaine (calculée à l'étape
    précédente, moyenne_4_derniers_memes_jours).

        pct_change = (total_visiteurs - moyenne) / moyenne * 100

    NULLIF(moyenne, 0) évite une division par zéro si la moyenne calculée
    était nulle (cas limite, mais bonne pratique défensive en SQL).
    Quand la moyenne elle-même est NULL (pas encore d'historique pour ce
    jour de semaine), pct_change est naturellement NULL aussi : on ne
    peut pas mesurer un écart à une moyenne qui n'existe pas encore.
    """
    with_avg = add_same_weekday_rolling_average()
    return duckdb.sql("""
        SELECT
            *,
            ROUND(
                (total_visiteurs - moyenne_4_derniers_memes_jours)
                / NULLIF(moyenne_4_derniers_memes_jours, 0) * 100,
                1
            ) AS pct_change
        FROM with_avg
        ORDER BY date
    """)

def save_to_parquet():
    """
    (TRANSFORM DATA 6/7) Sauvegarde la donnée transformée (filtrée +
    moyenne glissante + pct_change) au format Parquet, dans
    data/processed/filtered/.

    Le Parquet est un format de stockage "colonne" (columnar), à
    l'opposé du CSV qui est un format "ligne" : au lieu de stocker
    chaque ligne les unes après les autres, Parquet stocke chaque
    COLONNE séparément, avec son propre type et sa propre compression.
    Deux conséquences concrètes :
    - Les fichiers sont nettement plus légers (compression bien plus
      efficace quand on compresse une colonne de valeurs homogènes
      plutôt que du texte mélangé ligne par ligne).
    - La lecture est plus rapide dès qu'on n'a besoin que de certaines
      colonnes : lire uniquement "pct_change" sur un Parquet ne charge
      QUE cette colonne, alors qu'un CSV doit être lu ligne par ligne
      en entier, colonnes inutiles comprises.
    C'est le format standard utilisé en entreprise pour stocker de la
    donnée déjà nettoyée, entre l'étape de transformation et l'étape
    d'analyse/visualisation.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    final_table = add_pct_change()
    output_path = PROCESSED_DIR / "visitors_transformed.parquet"
    final_table.write_parquet(str(output_path))
    return output_path


def main():
    table = read_raw_data()
    print(table)

    row_count = duckdb.sql(
        f"SELECT COUNT(*) AS total FROM read_csv_auto('{RAW_DATA_GLOB}')"
    ).fetchone()[0]
    print(f"Total de lignes lues (tous fichiers confondus) : {row_count}")

    print("\nTrafic journalier (GROUP BY date + SUM) :")
    print(daily_traffic())

    print("\nFiltrage des lignes non fiables (id_capteur manquant / unite incohérente) :")
    valid_rows = filter_valid_rows()
    print(valid_rows)

    total_rows = row_count
    valid_count = duckdb.sql("SELECT COUNT(*) FROM valid_rows").fetchone()[0]
    print(f"Lignes de départ : {total_rows}")
    print(f"Lignes valides conservées : {valid_count}")
    print(f"Lignes supprimées : {total_rows - valid_count}")

    print("\nMoyenne glissante sur les 4 derniers mêmes jours de la semaine :")
    print(add_same_weekday_rolling_average())

    print("\nÉcart en pourcentage à cette moyenne (pct_change) :")
    print(add_pct_change())

    print("\nSauvegarde au format Parquet dans data/processed/filtered/ :")
    parquet_path = save_to_parquet()
    print(f"Fichier écrit : {parquet_path}")


if __name__ == "__main__":
    main()