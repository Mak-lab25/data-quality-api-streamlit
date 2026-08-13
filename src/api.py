"""
API e-commerce : expose le trafic (visiteurs) généré par EcommerceTrafficSensor.
"""

from datetime import date

from fastapi import FastAPI

from sensor import EcommerceTrafficSensor

app = FastAPI(
    title="E-commerce Data API",
    description="API exposant les données de trafic et de commandes simulées.",
    version="0.1.0",
)

sensor = EcommerceTrafficSensor()


@app.get("/visitors")
def get_visitors(day: date) -> dict:
    """
    Renvoie le nombre total de visiteurs pour une date donnée
    (somme des visiteurs sur les 24 heures de la journée).

    Exemple : GET /visitors?day=2026-08-13
    """
    total_visitors = sum(sensor.get_visitors(day, hour) for hour in range(24))
    return {"day": day.isoformat(), "visitors": total_visitors}