"""Calcul de l'Indice d'Infestation Global.

Rôle : appliquer la règle RM2 du cahier des charges §12.2 :

    indice = 60 x min(1, heures_au_dessus_de_85 / 48) + 40 x taux_de_detection_IA

L'indice est calculé par parcelle (0 à 100), puis agrégé en moyenne pour le
tableau de bord. Les seuils de niveau sont ceux de la maquette et du CDC :
moins de 30 faible, de 30 à 60 modéré, plus de 60 élevé.

Module volontairement pur : aucune dépendance à FastAPI, SQLAlchemy ou à la
base, pour rester testable seul et réutilisable par le simulateur (#6).
Auteur : MEKONTSO Olivier Steve (MOD-A4, issue #13).
"""

from __future__ import annotations

from collections.abc import Iterable

# Seuil d'alerte humidité (RM1) et durée au-delà de laquelle l'alerte tombe.
HUMIDITY_THRESHOLD_PCT = 85.0
ALERT_DURATION_HOURS = 48.0
# Une fenêtre d'analyse porte sur 7 jours.
WINDOW_HOURS = 168.0

# Pondérations de la formule RM2.
HUMIDITY_WEIGHT = 60.0
IA_WEIGHT = 40.0

# Seuils de niveau (maquette, écran 2).
LEVEL_LOW_MAX = 30
LEVEL_MODERATE_MAX = 60

# Plancher du volume sain estimé (hypothèse de démonstration).
HEALTHY_VOLUME_FLOOR_PCT = 20
HEALTHY_VOLUME_SLOPE = 0.7


def _round_half_up(value: float) -> int:
    """Arrondit à l'entier supérieur sur les demis, comme la maquette.

    `round()` de Python arrondit les demis au pair (82,5 -> 82) alors que la
    maquette affiche 83 : on garde le comportement de la maquette.
    """
    return int(value + 0.5)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def compute_infestation_index(hours_above_85: float, ia_detection_rate: float) -> int:
    """Calcule l'indice d'infestation d'une parcelle (0 à 100).

    :param hours_above_85: heures consécutives au-dessus de 85 % d'humidité,
        sur la fenêtre d'analyse (0 à 168).
    :param ia_detection_rate: taux de détection IA de la parcelle, de 0 à 1.
    :raises ValueError: si une valeur sort de son domaine.
    """
    if hours_above_85 < 0:
        raise ValueError("hours_above_85 ne peut pas être négatif")
    if not 0.0 <= ia_detection_rate <= 1.0:
        raise ValueError("ia_detection_rate doit être compris entre 0 et 1")

    humidity_part = HUMIDITY_WEIGHT * min(1.0, hours_above_85 / ALERT_DURATION_HOURS)
    ia_part = IA_WEIGHT * ia_detection_rate
    return _round_half_up(_clamp(humidity_part + ia_part))


def level_for(index: int) -> str:
    """Retourne le niveau d'alerte : `faible`, `modere` ou `eleve`."""
    if index < LEVEL_LOW_MAX:
        return "faible"
    if index <= LEVEL_MODERATE_MAX:
        return "modere"
    return "eleve"


def is_alert(hours_above_85: float) -> bool:
    """Vrai si la parcelle est en alerte RM1 (plus de 48 h au-dessus de 85 %)."""
    return hours_above_85 >= ALERT_DURATION_HOURS


def aggregate_index(indices: Iterable[int]) -> int:
    """Agrège les indices parcellaires en indice global (moyenne arrondie)."""
    values = list(indices)
    if not values:
        return 0
    return _round_half_up(sum(values) / len(values))


def estimated_healthy_volume_pct(index: int) -> int:
    """Volume sain estimé à 7 jours, en pourcentage.

    Hypothèse de démonstration : `max(20, 100 - 0,7 x indice)`. À calibrer
    avec les données ICCO/CICC avant le livrable final.
    """
    return int(max(HEALTHY_VOLUME_FLOOR_PCT, 100 - _round_half_up(index * HEALTHY_VOLUME_SLOPE)))
