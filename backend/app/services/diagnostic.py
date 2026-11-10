"""Passerelle backend vers le module d'inférence IA.

Rôle : exposer `predict` au routeur `POST /api/v1/diagnostic` sans dupliquer la
logique du module `ai/`. Le module `ai/infer.py` est volontairement sans
dépendance lourde (pas de TensorFlow au runtime de démonstration).

Auteur : MEKONTSO Olivier Steve (MOD-A5, issue #14).
"""

from __future__ import annotations

import sys
from pathlib import Path

# `ai/` vit à la racine du dépôt, à côté de `backend/`.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ai.infer import (  # noqa: E402
    DEFAULT_THRESHOLD,
    IS_DEMO,
    MAX_IMAGE_BYTES,
    MODEL_NAME,
    DiagnosticResult,
    InvalidImageError,
    detection_threshold,
    image_format,
    predict,
)

__all__ = [
    "DEFAULT_THRESHOLD",
    "IS_DEMO",
    "MAX_IMAGE_BYTES",
    "MODEL_NAME",
    "DiagnosticResult",
    "InvalidImageError",
    "detection_threshold",
    "image_format",
    "predict",
]
