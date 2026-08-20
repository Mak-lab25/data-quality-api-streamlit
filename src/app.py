"""
Application Streamlit : visualisation du trafic e-commerce transformé,
lu directement depuis le fichier Parquet avec DuckDB.
"""

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import timedelta

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


def get_lieux(df):
    """Renvoie la liste triée des identifiants de lieux (magasins) uniques présents dans la donnée."""
    return sorted(df["id_magasin"].unique())


def get_capteurs_for_lieu(df, lieu_id):
    """Renvoie les capteurs qui appartiennent à un lieu donné (liste dépendante du lieu sélectionné)."""
    return sorted(df[df["id_magasin"] == lieu_id]["id_capteur"].unique())


def filter_by_capteur(df, capteur_id):
    """
    (C) Filtre le DataFrame pour ne garder que les lignes du capteur
    sélectionné.
    """
    return df[df["id_capteur"] == capteur_id]


def filter_by_period(df, period_days):
    """
    (F) Restreint le DataFrame aux "period_days" derniers jours par
    rapport à aujourd'hui (7 pour une vue "semaine", 30 pour une vue
    "mois").
    """
    cutoff = pd.Timestamp.today().normalize() - timedelta(days=period_days)
    return df[df["date"] >= cutoff]


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

    # (F) Sidebar : sélection en cascade lieu -> capteur, + période
    st.sidebar.header("Filtres")

    lieux = get_lieux(df)
    selected_lieu = st.sidebar.selectbox("Lieu :", lieux)

    capteurs_du_lieu = get_capteurs_for_lieu(df, selected_lieu)
    selected_capteur = st.sidebar.selectbox("Capteur :", capteurs_du_lieu)

    periode_label = st.sidebar.radio(
        "Période :", ["Semaine (7 derniers jours)", "Mois (30 derniers jours)"]
    )
    period_days = 7 if periode_label.startswith("Semaine") else 30

    # (C) Filtrage des données pour le lieu, le capteur et la période choisis
    filtered_df = filter_by_capteur(df, selected_capteur)
    filtered_df = filtered_df[filtered_df["id_magasin"] == selected_lieu]
    filtered_df = filter_by_period(filtered_df, period_days)

    st.subheader(f"Données pour le capteur {selected_capteur} ({selected_lieu}) — {periode_label}")
    st.dataframe(filtered_df)

    # (D) Courbe du trafic journalier, avec Plotly
    st.subheader("Courbe du trafic journalier")
    fig = create_daily_chart(filtered_df)
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()