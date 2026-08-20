"""
DAG Airflow : orchestration horaire du pipeline de trafic e-commerce.

Deux tâches, exécutées via BashOperator :
  1. EXTRACT   -> lance fetch_data.py (va chercher la donnée du jour
                  chez le fournisseur / notre API)
  2. TRANSFORM -> lance read_data.py (lit, nettoie, transforme et
                  sauvegarde la donnée en Parquet)

IMPORTANT — voir la section "Limites de cette implémentation" du
README du projet : ce DAG est une démonstration pédagogique pensée
pour tourner EN LOCAL. Dans un vrai environnement de production, ni
Airflow ni ses workers n'exécuteraient ces scripts directement sur la
machine du scheduler (voir README pour le détail).
"""

from datetime import datetime, timedelta

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

PROJECT_DIR = "/home/makuser/data-quality-api-streamlit"

default_args = {
    "owner": "karen",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="ecommerce_traffic_pipeline",
    description="Récupère le trafic e-commerce depuis l'API fournisseur, puis le transforme.",
    default_args=default_args,
    start_date=datetime(2026, 8, 1),
    schedule="@hourly",
    catchup=False,
    tags=["ecommerce", "portfolio"],
) as dag:

    extract_task = BashOperator(
        task_id="extract",
        bash_command=f"cd {PROJECT_DIR} && python src/fetch_data.py $(date +%Y-%m-%d)",
    )

    transform_task = BashOperator(
        task_id="transform",
        bash_command=f"cd {PROJECT_DIR} && python src/read_data.py",
    )

    extract_task >> transform_task
