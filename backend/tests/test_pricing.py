"""Tests MOD-A4 : courbe de prix prédictive (RM3, RM5) et contrat §4.5.

Auteur : MEKONTSO Olivier Steve (issue #13).
"""

import json
import re
from pathlib import Path

import pytest

from app.services.pricing import (
    FORMULA_VERSION,
    adjust_price,
    build_forecast,
    forecast_payload,
)

DOC = Path(__file__).resolve().parents[2] / "docs" / "CONTRAT_JSON.md"
BLOC_JSON = re.compile(r"```json\s*\n(.*?)```", re.DOTALL)

DATES = [f"2026-11-0{jour}" for jour in range(4, 10)] + ["2026-11-10"]
REFERENCES = [1050, 1060, 1055, 1070, 1065, 1080, 1085]
INDICES = [0, 8, 14, 28, 42, 55, 62]


def _contrat_prix() -> dict:
    """Extrait l'exemple du contrat §4.5 pour vérifier l'alignement."""
    texte = DOC.read_text(encoding="utf-8")
    section = texte.split("### 4.5 Courbe de prix prédictive", 1)[1]
    return json.loads(BLOC_JSON.search(section).group(1))


def test_prix_reference_inchange_sans_infestation():
    assert adjust_price(1000, 0) == 1000


def test_prix_augmente_avec_l_indice():
    # 1085 x (1 + 0,15 x 62 / 100) = 1185,905
    assert adjust_price(1085, 62) == pytest.approx(1185.905)


def test_prix_refuse_les_entrees_invalides():
    with pytest.raises(ValueError):
        adjust_price(0, 10)
    with pytest.raises(ValueError):
        adjust_price(1000, -1)
    with pytest.raises(ValueError):
        adjust_price(1000, 101)


def test_courbe_sur_sept_jours():
    points = build_forecast(DATES, REFERENCES, INDICES)
    assert len(points) == 7
    assert points[0].adjusted_price == 1050
    assert points[-1].adjusted_price == pytest.approx(1185.905)


def test_courbe_refuse_les_sequences_incoherentes():
    with pytest.raises(ValueError):
        build_forecast(DATES, REFERENCES[:3], INDICES)
    with pytest.raises(ValueError):
        build_forecast([], [], [])


def test_payload_conforme_au_contrat():
    payload = forecast_payload(build_forecast(DATES, REFERENCES, INDICES))
    attendu = _contrat_prix()

    assert set(payload) == set(attendu)
    assert payload["unit"] == attendu["unit"]
    assert payload["formula_version"] == attendu["formula_version"] == FORMULA_VERSION
    assert payload["is_demo"] is True
    assert payload["horizon_days"] == 7
    assert set(payload["points"][0]) == set(attendu["points"][0])
