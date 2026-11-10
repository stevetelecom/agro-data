"""Courbe de prix prédictive.

Rôle : ajuster le prix de référence selon l'indice d'infestation (RM3) et
journaliser chaque calcul (RM5, audit).

Formule v1 (hypothèse de démonstration) :

    prix_ajuste = prix_reference x (1 + k x indice / 100)

avec `k = 0,15`. Ce coefficient reproduit le dernier point de la maquette
(1085 FCFA/kg à l'indice 62 donne 1186, la maquette affiche 1185) et reste à
calibrer avec les données publiques ICCO/CICC.

Module volontairement pur : aucune dépendance à FastAPI ou à la base.
Auteur : MEKONTSO Olivier Steve (MOD-A4, issue #13).
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass

logger = logging.getLogger("agro_data.pricing")

# Coefficients de la formule v1.
PRICE_COEFFICIENT = 0.15
FORMULA_VERSION = "v1"
PRICE_UNIT = "FCFA/kg"

# Le prototype affiche une courbe de démonstration (RM3).
IS_DEMO = True


@dataclass(frozen=True)
class PricePoint:
    """Un point de la courbe : prix de référence et prix ajusté."""

    date: str
    reference_price: float
    adjusted_price: float

    def as_dict(self) -> dict[str, object]:
        return {
            "date": self.date,
            "reference_price": round(self.reference_price, 2),
            "adjusted_price": round(self.adjusted_price, 2),
        }


def adjust_price(reference_price: float, index: int) -> float:
    """Applique la formule RM3 à un prix de référence pour un indice donné.

    :param reference_price: prix de référence en FCFA/kg, strictement positif.
    :param index: indice d'infestation de 0 à 100.
    :raises ValueError: si le prix ou l'indice sort de son domaine.
    """
    if reference_price <= 0:
        raise ValueError("reference_price doit être strictement positif")
    if not 0 <= index <= 100:
        raise ValueError("index doit être compris entre 0 et 100")
    return reference_price * (1 + PRICE_COEFFICIENT * index / 100)


def build_forecast(
    dates: Sequence[str],
    reference_prices: Sequence[float],
    indices: Sequence[int],
) -> list[PricePoint]:
    """Construit la courbe de prix sur un horizon de plusieurs jours.

    Les trois séquences doivent avoir la même longueur : un point par jour.
    """
    if not (len(dates) == len(reference_prices) == len(indices)):
        raise ValueError("dates, reference_prices et indices doivent avoir la même longueur")
    if not dates:
        raise ValueError("la courbe doit contenir au moins un point")

    points = [
        PricePoint(
            date=date,
            reference_price=float(reference),
            adjusted_price=adjust_price(float(reference), int(index)),
        )
        for date, reference, index in zip(dates, reference_prices, indices, strict=True)
    ]
    log_price_computation(points, indices)
    return points


def log_price_computation(points: Sequence[PricePoint], indices: Sequence[int]) -> None:
    """Journalise le calcul de prix : entrées, version de formule, résultat (RM5)."""
    for point, index in zip(points, indices, strict=True):
        logger.info(
            "price_computation formula=%s index=%s reference=%s adjusted=%s date=%s",
            FORMULA_VERSION,
            index,
            round(point.reference_price, 2),
            round(point.adjusted_price, 2),
            point.date,
        )


def forecast_payload(points: Sequence[PricePoint]) -> dict[str, object]:
    """Sérialise la courbe au format du contrat d'échange §4.5."""
    return {
        "unit": PRICE_UNIT,
        "horizon_days": len(points),
        "is_demo": IS_DEMO,
        "formula_version": FORMULA_VERSION,
        "points": [point.as_dict() for point in points],
    }
