"""
Script de transformation : lit l'ensemble des fichiers CSV bruts stockés
dans data/raw/ (un fichier par mois) et affiche le résultat sous forme
de table unique, grâce à DuckDB.
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


def main():
    table = read_raw_data()

    print(table)

    row_count = duckdb.sql(
        f"SELECT COUNT(*) AS total FROM read_csv_auto('{RAW_DATA_GLOB}')"
    ).fetchone()[0]
    print(f"Total de lignes lues (tous fichiers confondus) : {row_count}")


if __name__ == "__main__":
    main()