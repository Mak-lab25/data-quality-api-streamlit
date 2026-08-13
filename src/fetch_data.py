"""
Script client : interroge l'API du fournisseur (route GET /visitors) pour
chaque date allant du paramètre d'entrée jusqu'à aujourd'hui inclus.
"""

import sys
from datetime import date, timedelta

import requests

API_URL = "http://127.0.0.1:8000/visitors"


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


def query_api(url: str, params: dict | None = None) -> dict:
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
    """Interroge NOTRE API (le fournisseur simulé) pour un jour donné."""
    data = query_api(API_URL, params={"day": day.isoformat()})
    return data["visitors"]


def main():
    start_date = parse_start_date(sys.argv)
    today = date.today()

    if start_date > today:
        print(f"La date de départ ({start_date}) est dans le futur, rien à récupérer.")
        return

    current_day = start_date
    while current_day <= today:
        visitors = fetch_visitors(current_day)
        print(f"{current_day.isoformat()} : {visitors} visiteurs")
        current_day += timedelta(days=1)


if __name__ == "__main__":
    main()
