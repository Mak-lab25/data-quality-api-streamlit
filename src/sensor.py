"""
Générateur de données e-commerce : trafic et commandes horaires
sur un catalogue produit, avec injection contrôlée d'anomalies
de data quality (valeurs nulles, valeurs improbables).
"""

import random
from datetime import date
from dataclasses import dataclass


@dataclass
class Produit:
    reference: str
    designation: str
    categorie: str
    prix: float


CATALOGUE = [
    Produit("REF-001", "Chaise de bureau ergonomique", "Mobilier", 149.90),
    Produit("REF-002", "Ordinateur portable 14 pouces", "Informatique", 899.00),
    Produit("REF-003", "Ramette papier A4 (500 feuilles)", "Fournitures", 4.50),
    Produit("REF-004", "Écran 24 pouces", "Informatique", 179.00),
    Produit("REF-005", "Armoire de rangement métallique", "Mobilier", 320.00),
]


class EcommerceTrafficSensor:
    """
    Simule le trafic (visiteurs) et les commandes d'un site e-commerce B2B,
    heure par heure, sur un catalogue produit donné.

    Pour un (jour, heure) donné, renvoie toujours le même résultat
    (déterminisme), y compris les anomalies de data quality injectées.
    """

    DAY_START_HOUR = 8
    DAY_END_HOUR = 19
    NIGHT_DIVIDER = 11
    CONVERSION_RATE = 0.03  # % de visiteurs qui passent commande
    DIRTY_DATA_RATE = 0.15  # % de commandes contenant une anomalie

    def __init__(self, catalogue=None, base_visitors: int = 200, seed: int = 42):
        self.catalogue = catalogue or CATALOGUE
        self.base_visitors = base_visitors
        self.seed = seed

    def _is_daytime(self, hour: int) -> bool:
        return self.DAY_START_HOUR <= hour <= self.DAY_END_HOUR

    def _hourly_factor(self, hour: int) -> float:
        return 1.0 if self._is_daytime(hour) else 1 / self.NIGHT_DIVIDER

    def _rng_for(self, day: date, hour: int, salt: str) -> random.Random:
        """RNG local et déterministe, propre à (jour, heure, salt)."""
        return random.Random(f"{day.isoformat()}-{hour}-{self.seed}-{salt}")

    def get_visitors(self, day: date, hour: int) -> int:
        if not (0 <= hour <= 23):
            raise ValueError("hour doit être compris entre 0 et 23")
        rng = self._rng_for(day, hour, "visitors")
        expected = self.base_visitors * self._hourly_factor(hour)
        return max(0, round(rng.gauss(expected, expected * 0.15)))

    def _apply_anomaly(self, order: dict, rng: random.Random) -> dict:
        """
        Corrompt volontairement UNE commande, avec une anomalie choisie
        aléatoirement parmi une liste de cas réalistes de data quality.
        Ne s'applique que si le tirage déclenche une anomalie (voir get_orders).
        """
        anomaly_type = rng.choice([
            "null_designation",
            "null_categorie",
            "null_prix",
            "prix_negatif",
            "prix_zero",
            "quantite_aberrante",
            "reference_inconnue",
        ])

        if anomaly_type == "null_designation":
            order["designation"] = None
        elif anomaly_type == "null_categorie":
            order["categorie"] = None
        elif anomaly_type == "null_prix":
            order["prix_unitaire"] = None
        elif anomaly_type == "prix_negatif":
            order["prix_unitaire"] = -abs(order["prix_unitaire"])
        elif anomaly_type == "prix_zero":
            order["prix_unitaire"] = 0.0
        elif anomaly_type == "quantite_aberrante":
            order["quantite"] = rng.randint(100, 999)
        elif anomaly_type == "reference_inconnue":
            order["reference_produit"] = f"REF-{rng.randint(900, 999)}"

        return order

    def get_orders(self, day: date, hour: int) -> list[dict]:
        """
        Renvoie les commandes passées durant cette heure. Une partie des
        commandes (DIRTY_DATA_RATE) contient volontairement une anomalie
        de data quality (valeur nulle ou improbable), de façon déterministe.
        """
        visitors = self.get_visitors(day, hour)
        rng_orders = self._rng_for(day, hour, "orders")
        rng_anomalies = self._rng_for(day, hour, "anomalies")
        nb_orders = round(visitors * self.CONVERSION_RATE)

        orders = []
        for i in range(nb_orders):
            produit = rng_orders.choice(self.catalogue)
            order = {
                "order_id": f"{day.isoformat()}-{hour:02d}-{i:03d}",
                "reference_produit": produit.reference,
                "designation": produit.designation,
                "categorie": produit.categorie,
                "quantite": rng_orders.randint(1, 5),
                "prix_unitaire": produit.prix,
                "day": day.isoformat(),
                "hour": hour,
            }

            if rng_anomalies.random() < self.DIRTY_DATA_RATE:
                order = self._apply_anomaly(order, rng_anomalies)

            orders.append(order)

        # Anomalie supplémentaire, plus rare : order_id dupliqué
        if orders and rng_anomalies.random() < 0.05:
            duplicate = dict(orders[-1])
            duplicate["order_id"] = orders[0]["order_id"]  # collision volontaire
            orders.append(duplicate)

        return orders


if __name__ == "__main__":
    sensor = EcommerceTrafficSensor()
    today = date(2026, 8, 13)

    total_orders = 0
    total_anomalies = 0

    for h in range(24):
        orders = sensor.get_orders(today, h)
        total_orders += len(orders)
        for o in orders:
            has_anomaly = (
                o["designation"] is None
                or o["categorie"] is None
                or o["prix_unitaire"] is None
                or (o["prix_unitaire"] is not None and o["prix_unitaire"] <= 0)
                or o["quantite"] > 10
                or not o["reference_produit"].startswith(("REF-00",))
            )
            if has_anomaly:
                total_anomalies += 1
        print(f"{h:02d}h : {sensor.get_visitors(today, h)} visiteurs, {len(orders)} commandes")

    print(f"\nTotal commandes : {total_orders}")
    print(f"Dont anomalies détectées (approx.) : {total_anomalies}")

    # Vérification du déterminisme (y compris les anomalies)
    assert sensor.get_orders(today, 14) == sensor.get_orders(today, 14)
    print("Déterminisme OK ✅")