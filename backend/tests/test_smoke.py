"""Test de fumée : vérifie que la structure de base du backend est en place."""

from pathlib import Path


def test_backend_structure_exists():
    backend = Path(__file__).resolve().parents[1]
    assert (backend / "app" / "main.py").is_file()
    assert (backend / "requirements.txt").is_file()
