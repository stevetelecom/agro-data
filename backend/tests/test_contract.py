"""Test de contrat : le document docs/CONTRAT_JSON.md reste aligné sur le schéma Pydantic.

Rôle : détecter immédiatement toute divergence entre la référence écrite
(cahier des charges §12.1) et l'implémentation du backend.
Auteur : MEKONTSO Olivier Steve (MOD-G1, issue #4).
"""

import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.crud import PlotRead
from app.schemas.diagnostic import DiagnosticRead
from app.schemas.indicators import KpisRead, PriceForecastRead
from app.schemas.measurement import MeasurementCreate

DOC = Path(__file__).resolve().parents[2] / "docs" / "CONTRAT_JSON.md"
BLOC_JSON = re.compile(r"```json\s*\n(.*?)```", re.DOTALL)

CHAMPS_RACINE = {"device_id", "timestamp", "climate", "diagnostic_ia", "geo_enc"}


def _exemple(section: str) -> dict:
    """Extrait et décode le premier bloc JSON qui suit une section du document."""
    texte = DOC.read_text(encoding="utf-8")
    assert section in texte, f"section absente du contrat : {section}"
    extrait = texte.split(section, 1)[1]
    bloc = BLOC_JSON.search(extrait)
    assert bloc is not None, f"aucun bloc JSON après : {section}"
    return json.loads(bloc.group(1))


def test_document_de_contrat_present():
    assert DOC.is_file(), "docs/CONTRAT_JSON.md est la référence du contrat d'échange"


def test_exemple_canonique_valide_le_schema():
    payload = _exemple("### 3.1 Exemple canonique")
    mesure = MeasurementCreate.model_validate(payload)
    assert mesure.device_id == "AMB-P001"
    assert mesure.timestamp == 1792800000
    assert mesure.climate.air_humidity_pct == 88.2
    assert mesure.diagnostic_ia.phytophthora_detected == 0
    assert mesure.diagnostic_ia.confidence == 0.93


def test_champs_documentes_identiques_au_schema():
    assert set(MeasurementCreate.model_fields) == CHAMPS_RACINE
    assert set(_exemple("### 3.1 Exemple canonique")) == CHAMPS_RACINE


def test_exemple_rejete_est_refuse_par_le_schema():
    payload = _exemple("## 5. Exemples rejetés")
    with pytest.raises(ValidationError):
        MeasurementCreate.model_validate(payload)


def test_exemple_kpis_valide_le_schema():
    payload = _exemple("### 4.4 Indicateurs du tableau de bord")
    kpis = KpisRead.model_validate(payload)
    assert set(payload) == set(KpisRead.model_fields)
    assert kpis.level in {"faible", "modere", "eleve"}


def test_exemple_prix_valide_le_schema():
    payload = _exemple("### 4.5 Courbe de prix prédictive")
    prix = PriceForecastRead.model_validate(payload)
    assert set(payload) == set(PriceForecastRead.model_fields)
    assert prix.formula_version == "v1"


def test_exemple_parcelle_valide_le_schema():
    payload = _exemple("### 4.6 Parcelles")
    parcelle = PlotRead.model_validate(payload)
    assert set(payload) == set(PlotRead.model_fields)
    assert parcelle.level in {"faible", "modere", "eleve"}


def test_exemple_diagnostic_valide_le_schema():
    payload = _exemple("### 4.7 Diagnostic IA")
    diagnostic = DiagnosticRead.model_validate(payload)
    assert set(payload) == set(DiagnosticRead.model_fields)
    assert diagnostic.is_demo is True
