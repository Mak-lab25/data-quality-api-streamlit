"""
Script de transformation : lit l'ensemble des fichiers CSV bruts stockés
dans data/raw/ (un fichier par mois), les combine, les agrège par jour,
et filtre les lignes non fiables.
"""

import duckdb

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

    valid_count = duckdb.sql("SELECT COUNT(*) FROM valid_rows").fetchone()[0]
    print(f"Lignes de départ : {row_count}")
    print(f"Lignes valides conservées : {valid_count}")
    print(f"Lignes supprimées : {row_count - valid_count}")


if __name__ == "__main__":
    main()