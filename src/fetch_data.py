"""
Script client : interroge l'API du fournisseur (route GET /visitors_hourly)
pour chaque date allant du paramètre d'entrée jusqu'à aujourd'hui inclus,
et dépose les données collectées sous forme de CSV mensuels dans data/raw/.
"""

import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

import requests

API_URL = "http://127.0.0.1:8000/visitors"
HOURLY_API_URL = "http://127.0.0.1:8000/visitors_hourly"

# Métadonnées du capteur simulé (en réalité, elles viendraient de l'inventaire
# des capteurs/magasins connectés au fournisseur).
ID_CAPTEUR = "CAPT-001"
ID_MAGASIN = "MAG-001"
UNITE = "visiteurs"

# Unités volontairement absurdes pour simuler de la donnée non fiable (G)
UNITES_INCOHERENTES = ["Litres", "kg", "°C", "N/A", ""]

CSV_FIELDNAMES = ["date", "heure", "id_capteur", "id_magasin", "nombre_visiteurs", "unite"]

UNRELIABLE_DATA_RATE = 0.10  # 10% des lignes contiennent une anomalie


def parse_start_date(args: list[str]) -> date:
    if len(args) != 2:
        print("Usage : python fetch_data.py YYYY-MM-DD")
        sys.exit(1)

    date_arg = args[1]
    try:
        return date.fromisoformat(date_arg)
    except ValueError:
        print(f"Erreur : '{date_arg}' n'est pas une date valide (format attendu : YYYY-MM-DD)")
        sys.exit(1)


def query_api(url: str, params: dict | None = None):
    """
    Fonction générique : interroge n'importe quelle API REST en GET
    et renvoie sa réponse JSON. Ne connaît rien de l'API appelée
    (ni son domaine métier, ni sa structure de réponse) : c'est le
    rôle de l'appelant d'interpréter le JSON renvoyé.
    """
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def fetch_visitors(day: date) -> int:
    """Interroge NOTRE API (le fournisseur simulé) pour le total d'un jour donné."""
    data = query_api(API_URL, params={"day": day.isoformat()})
    return data["visitors"]


def fetch_visitors_hourly(day: date) -> list[dict]:
    """Interroge NOTRE API pour le détail heure par heure d'un jour donné."""
    return query_api(HOURLY_API_URL, params={"day": day.isoformat()})


def build_rows_for_day(day: date) -> list[dict]:
    """
    Construit les lignes CSV (une par heure) pour un jour donné, au format
    attendu : date, heure, id_capteur, id_magasin, nombre_visiteurs, unite.
    """
    hourly_data = fetch_visitors_hourly(day)
    return [
        {
            "date": day.isoformat(),
            "heure": entry["hour"],
            "id_capteur": ID_CAPTEUR,
            "id_magasin": ID_MAGASIN,
            "nombre_visiteurs": entry["visitors"],
            "unite": UNITE,
        }
        for entry in hourly_data
    ]


def inject_unreliable_data(rows: list[dict], seed: int = 123) -> list[dict]:
    """
    (G) Corrompt volontairement une partie des lignes pour simuler de la
    donnée non fiable telle qu'on la rencontrerait chez un vrai fournisseur :
    id_capteur manquant (NULL) ou unité incohérente. Déterministe (seed fixe)
    pour que le jeu de données corrompu soit reproductible.
    """
    rng = random.Random(seed)
    corrupted_rows = []

    for row in rows:
        row = dict(row)  # copie, pour ne pas modifier l'original
        if rng.random() < UNRELIABLE_DATA_RATE:
            anomaly_type = rng.choice(["id_capteur_null", "unite_incoherente"])
            if anomaly_type == "id_capteur_null":
                row["id_capteur"] = ""  # représentation CSV d'une valeur NULL
            elif anomaly_type == "unite_incoherente":
                row["unite"] = rng.choice(UNITES_INCOHERENTES)
        corrupted_rows.append(row)

    return corrupted_rows


def write_monthly_csvs(rows: list[dict], output_dir: str = "data/raw") -> list[Path]:
    """
    (H) Regroupe les lignes par mois (année-mois de la colonne "date") et
    écrit un fichier CSV par mois dans output_dir. Renvoie la liste des
    fichiers créés.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    rows_by_month: dict[str, list[dict]] = {}
    for row in rows:
        month_key = row["date"][:7]  # "YYYY-MM-DD" -> "YYYY-MM"
        rows_by_month.setdefault(month_key, []).append(row)

    written_files = []
    for month_key, month_rows in rows_by_month.items():
        file_path = output_path / f"visitors_{month_key}.csv"
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(month_rows)
        written_files.append(file_path)

    return written_files


def main():
    start_date = parse_start_date(sys.argv)
    today = date.today()

    if start_date > today:
        print(f"La date de départ ({start_date}) est dans le futur, rien à récupérer.")
        return

    all_rows = []
    current_day = start_date
    while current_day <= today:
        all_rows.extend(build_rows_for_day(current_day))
        print(f"{current_day.isoformat()} : récupéré ({len(all_rows)} lignes cumulées)")
        current_day += timedelta(days=1)

    all_rows = inject_unreliable_data(all_rows)
    written_files = write_monthly_csvs(all_rows)

    print(f"\n{len(written_files)} fichier(s) CSV écrit(s) :")
    for f in written_files:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
