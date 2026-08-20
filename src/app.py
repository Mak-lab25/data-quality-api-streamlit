"""
Application Streamlit : visualisation du trafic e-commerce transformé,
lu directement depuis le fichier Parquet avec DuckDB.
"""

import duckdb
import streamlit as st

PARQUET_PATH = "data/processed/filtered/visitors_transformed.parquet"


def load_data():
    """
    (A) Ouvre la donnée Parquet avec DuckDB. On convertit directement en
    DataFrame Pandas (.df()) car Streamlit sait nativement afficher et
    manipuler des DataFrames (tableaux, graphiques, filtres...).
    """
    return duckdb.sql(f"SELECT * FROM '{PARQUET_PATH}'").df()


def get_capteurs(df):
    """Renvoie la liste triée des identifiants de capteurs uniques présents dans la donnée."""
    return sorted(df["id_capteur"].unique())


def main():
    st.set_page_config(page_title="Trafic e-commerce", layout="wide")
    st.title("📊 Trafic e-commerce — Tableau de bord")

    df = load_data()

    # (B) Liste déroulante des capteurs disponibles
    capteurs = get_capteurs(df)
    selected_capteur = st.selectbox("Choisir un capteur :", capteurs)

    st.write(f"Capteur sélectionné : **{selected_capteur}**")


if __name__ == "__main__":
    main()