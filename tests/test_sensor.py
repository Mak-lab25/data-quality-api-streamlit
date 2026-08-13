"""
Tests unitaires pour EcommerceTrafficSensor (src/ecommerce_sensor.py).
"""

from datetime import date, timedelta

import pytest

from sensor import EcommerceTrafficSensor, CATALOGUE


@pytest.fixture
def sensor():
    return EcommerceTrafficSensor()


@pytest.fixture
def some_day():
    return date(2026, 8, 13)


def _collect_orders_over_days(sensor, start_day, num_days=7):
    """Agrège les commandes sur plusieurs jours pour avoir un échantillon
    représentatif des anomalies (déterministe, donc reproductible)."""
    all_orders = []
    for d in range(num_days):
        day = start_day + timedelta(days=d)
        for hour in range(24):
            all_orders.extend(sensor.get_orders(day, hour))
    return all_orders


# ---------------------------------------------------------------------------
# get_visitors
# ---------------------------------------------------------------------------

def test_get_visitors_is_deterministic(sensor, some_day):
    assert sensor.get_visitors(some_day, 14) == sensor.get_visitors(some_day, 14)


def test_get_visitors_daytime_greater_than_nighttime(sensor, some_day):
    day_traffic = sensor.get_visitors(some_day, 14)
    night_traffic = sensor.get_visitors(some_day, 3)
    assert day_traffic > night_traffic


def test_get_visitors_invalid_hour_raises(sensor, some_day):
    with pytest.raises(ValueError):
        sensor.get_visitors(some_day, 24)
    with pytest.raises(ValueError):
        sensor.get_visitors(some_day, -1)


def test_get_visitors_never_negative(sensor, some_day):
    for hour in range(24):
        assert sensor.get_visitors(some_day, hour) >= 0


# ---------------------------------------------------------------------------
# get_orders — structure et déterminisme
# ---------------------------------------------------------------------------

def test_get_orders_is_deterministic(sensor, some_day):
    assert sensor.get_orders(some_day, 14) == sensor.get_orders(some_day, 14)


def test_get_orders_has_expected_keys(sensor, some_day):
    orders = sensor.get_orders(some_day, 14)
    assert orders, "Aucune commande générée pour ce créneau, ajuste le test"
    expected_keys = {
        "order_id", "reference_produit", "designation", "categorie",
        "quantite", "prix_unitaire", "day", "hour",
    }
    for order in orders:
        assert set(order.keys()) == expected_keys


def test_get_orders_day_and_hour_match_input(sensor, some_day):
    orders = sensor.get_orders(some_day, 14)
    for order in orders:
        assert order["day"] == some_day.isoformat()
        assert order["hour"] == 14


# ---------------------------------------------------------------------------
# Data quality — présence des anomalies attendues sur un échantillon large
# ---------------------------------------------------------------------------

def test_dataset_contains_null_values(sensor, some_day):
    orders = _collect_orders_over_days(sensor, some_day)
    assert any(o["designation"] is None for o in orders)
    assert any(o["categorie"] is None for o in orders)
    assert any(o["prix_unitaire"] is None for o in orders)


def test_dataset_contains_improbable_prices(sensor, some_day):
    orders = _collect_orders_over_days(sensor, some_day)
    negative_or_zero = [
        o for o in orders
        if o["prix_unitaire"] is not None and o["prix_unitaire"] <= 0
    ]
    assert negative_or_zero


def test_dataset_contains_improbable_quantities(sensor, some_day):
    orders = _collect_orders_over_days(sensor, some_day)
    assert any(o["quantite"] > 10 for o in orders)


def test_dataset_contains_unknown_reference(sensor, some_day):
    orders = _collect_orders_over_days(sensor, some_day)
    known_refs = {p.reference for p in CATALOGUE}
    assert any(o["reference_produit"] not in known_refs for o in orders)


def test_dataset_contains_duplicate_order_ids(sensor, some_day):
    orders = _collect_orders_over_days(sensor, some_day)
    order_ids = [o["order_id"] for o in orders]
    assert len(order_ids) != len(set(order_ids))


def test_clean_orders_have_no_anomalies(sensor, some_day):
    """Vérifie qu'il existe bien aussi des commandes 100% propres,
    pour confirmer que le taux d'anomalie n'est pas de 100%."""
    orders = _collect_orders_over_days(sensor, some_day)
    known_refs = {p.reference for p in CATALOGUE}
    clean_orders = [
        o for o in orders
        if o["designation"] is not None
        and o["categorie"] is not None
        and o["prix_unitaire"] is not None
        and o["prix_unitaire"] > 0
        and o["quantite"] <= 10
        and o["reference_produit"] in known_refs
    ]
    assert clean_orders