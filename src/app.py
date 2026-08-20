"""
Application Streamlit : visualisation du trafic e-commerce transformé,
lu directement depuis le fichier Parquet avec DuckDB.
"""

import duckdb
import plotly.express as px
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


def filter_by_capteur(df, capteur_id):
    """
    (C) Filtre le DataFrame pour ne garder que les lignes du capteur
    sélectionné.
    """
    return df[df["id_capteur"] == capteur_id]


def create_daily_chart(df):
    """
    (D) Construit une courbe (Plotly) du trafic journalier pour le
    capteur sélectionné : une valeur par date, triée chronologiquement.
    """
    fig = px.line(
        df.sort_values("date"),
        x="date",
        y="total_visiteurs",
        markers=True,
        title="Trafic journalier",
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Nombre de visiteurs")
    return fig


def main():
    st.set_page_config(page_title="Trafic e-commerce", layout="wide")
    st.title("📊 Trafic e-commerce — Tableau de bord")

    df = load_data()

    # (B) Liste déroulante des capteurs disponibles
    capteurs = get_capteurs(df)
    selected_capteur = st.selectbox("Choisir un capteur :", capteurs)

    # (C) Affichage des données filtrées pour le capteur sélectionné
    st.subheader(f"Données pour le capteur {selected_capteur}")
    filtered_df = filter_by_capteur(df, selected_capteur)
    st.dataframe(filtered_df)

    # (D) Courbe du trafic journalier, avec Plotly
    st.subheader("Courbe du trafic journalier")
    fig = create_daily_chart(filtered_df)
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()