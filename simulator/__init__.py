"""Simulateur du boîtier AGRO-DATA (bloc C).

Rôle : regrouper le générateur (MOD-C1), les scénarios et le tampon
Store-and-Forward (MOD-C2) sous une seule commande.
"""

from simulator.generator import (
    DEFAULT_API_BASE,
    DEFAULT_API_KEY,
    DEFAULT_DEVICE_ID,
    TransientSendError,
    build_measurement,
    hourly_series,
    send_measurement,
    send_many,
    to_unix,
)
from simulator.scenarios import (
    COUPURE_RESEAU,
    HUMIDITE_CRITIQUE,
    SAIN,
    SCENARIOS,
    ScenarioRun,
    build_scenario,
    consecutive_hours_above,
)
from simulator.store_forward import FlushReport, StoreAndForward

__all__ = [
    "COUPURE_RESEAU",
    "DEFAULT_API_BASE",
    "DEFAULT_API_KEY",
    "DEFAULT_DEVICE_ID",
    "FlushReport",
    "HUMIDITE_CRITIQUE",
    "SAIN",
    "SCENARIOS",
    "ScenarioRun",
    "StoreAndForward",
    "TransientSendError",
    "build_measurement",
    "build_scenario",
    "consecutive_hours_above",
    "hourly_series",
    "send_measurement",
    "send_many",
    "to_unix",
]
