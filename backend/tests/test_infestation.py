"""Tests MOD-A4 : Indice d'Infestation Global (RM2, RM1).

Références : cahier des charges §12.2 et contrat d'échange §4.4.
Auteur : MEKONTSO Olivier Steve (issue #13).
"""

import pytest

from app.services.infestation import (
    aggregate_index,
    compute_infestation_index,
    estimated_healthy_volume_pct,
    is_alert,
    level_for,
)


def test_indice_nul_sans_humidite_ni_detection():
    assert compute_infestation_index(0, 0.0) == 0


def test_indice_plafonne_la_part_humidite_a_48_heures():
    # 48 h suffisent à saturer les 60 points d'humidité.
    assert compute_infestation_index(48, 0.0) == 60
    assert compute_infestation_index(168, 0.0) == 60


def test_indice_parcelle_en_alerte():
    # Cas de la maquette : 62 h au-dessus de 85 % et 55 % de détection.
    assert compute_infestation_index(62, 0.55) == 82


def test_indice_arrondi_au_superieur_sur_les_demis():
    # 24 h -> 30 points d'humidité, 0,0125 de détection -> 0,5 point.
    assert compute_infestation_index(24, 0.0125) == 31


def test_indice_borne_a_100():
    assert compute_infestation_index(1000, 1.0) == 100


def test_indice_refuse_les_entrees_invalides():
    with pytest.raises(ValueError):
        compute_infestation_index(-1, 0.0)
    with pytest.raises(ValueError):
        compute_infestation_index(10, 1.5)
    with pytest.raises(ValueError):
        compute_infestation_index(10, -0.1)


@pytest.mark.parametrize(
    ("index", "niveau"),
    [(0, "faible"), (29, "faible"), (30, "modere"), (60, "modere"), (61, "eleve"), (100, "eleve")],
)
def test_seuils_de_niveau(index, niveau):
    assert level_for(index) == niveau


def test_alerte_a_partir_de_48_heures():
    assert is_alert(47.9) is False
    assert is_alert(48) is True


def test_agregation_par_moyenne():
    assert aggregate_index([82, 35, 0, 45]) == 41
    assert aggregate_index([]) == 0


def test_volume_sain_estime():
    assert estimated_healthy_volume_pct(0) == 100
    assert estimated_healthy_volume_pct(62) == 57
    assert estimated_healthy_volume_pct(100) == 30
    assert estimated_healthy_volume_pct(200) == 20
