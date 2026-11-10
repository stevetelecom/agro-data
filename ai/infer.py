"""Inférence du modèle de détection de la pourriture brune.

Rôle : retourner un drapeau binaire et un score de confiance pour une image
(BF2, PB-06). Le prototype est volontairement **sans dépendance lourde** : il
valide l'image puis produit un score déterministe à partir de son empreinte
SHA-256, en attendant l'entraînement MobileNetV2 (`ai/train.py`).

Le seuil de décision est configurable via `IA_DETECTION_THRESHOLD` (BF2.5).
`is_demo` reste à `true` tant que le modèle n'est pas entraîné sur un jeu
d'images validé par le PO.

Auteur : MEKONTSO Olivier Steve (MOD-A5, issue #14).
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

# Limite du contrat §4.7 : 5 Mo maximum.
MAX_IMAGE_BYTES = 5 * 1024 * 1024
DEFAULT_THRESHOLD = 0.5
MODEL_NAME = "mobilenetv2-v1"
IS_DEMO = True

MAGIC_JPEG = b"\xff\xd8\xff"
MAGIC_PNG = b"\x89PNG\r\n\x1a\n"


class InvalidImageError(ValueError):
    """Image absente, trop volumineuse ou d'un format non supporté."""


@dataclass(frozen=True)
class DiagnosticResult:
    """Résultat d'un diagnostic d'image (contrat §4.7)."""

    phytophthora_detected: int
    confidence: float
    label: str
    recommendation: str
    model: str
    is_demo: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "phytophthora_detected": self.phytophthora_detected,
            "confidence": self.confidence,
            "label": self.label,
            "recommendation": self.recommendation,
            "model": self.model,
            "is_demo": self.is_demo,
        }


def _clamp_threshold(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def detection_threshold() -> float:
    """Lit le seuil de décision, avec repli sur la valeur par défaut."""
    raw = os.getenv("IA_DETECTION_THRESHOLD")
    if raw is None or raw.strip() == "":
        return DEFAULT_THRESHOLD
    try:
        return _clamp_threshold(float(raw))
    except ValueError:
        return DEFAULT_THRESHOLD


def image_format(data: bytes) -> str:
    """Retourne `jpeg` ou `png` d'après les octets d'en-tête, sinon lève une erreur."""
    if data.startswith(MAGIC_JPEG):
        return "jpeg"
    if data.startswith(MAGIC_PNG):
        return "png"
    raise InvalidImageError("image illisible : JPEG ou PNG attendu")


def _demo_score(data: bytes) -> float:
    """Score déterministe dans [0, 1) : même image, même résultat.

    Ce n'est **pas** un modèle entraîné : la valeur sert uniquement à faire
    fonctionner la démonstration de bout en bout tant que `ai/train.py` n'a pas
    produit de poids validés.
    """
    digest = hashlib.sha256(data).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def predict(image: bytes, *, threshold: float | None = None) -> DiagnosticResult:
    """Diagnostique une image et retourne le drapeau et la confiance.

    :param image: contenu binaire de l'image (JPEG ou PNG, 5 Mo maximum).
    :param threshold: seuil de décision ; par défaut `IA_DETECTION_THRESHOLD`.
    :raises InvalidImageError: si l'image est vide, trop lourde ou illisible.
    """
    if not isinstance(image, (bytes, bytearray)):
        raise InvalidImageError("image illisible : contenu binaire attendu")
    data = bytes(image)
    if not data:
        raise InvalidImageError("image vide")
    if len(data) > MAX_IMAGE_BYTES:
        raise InvalidImageError("image trop volumineuse (5 Mo maximum)")
    image_format(data)

    seuil = detection_threshold() if threshold is None else _clamp_threshold(threshold)
    score = _demo_score(data)
    detected = int(score >= seuil)
    confidence = round(score if detected else 1.0 - score, 2)

    return DiagnosticResult(
        phytophthora_detected=detected,
        confidence=confidence,
        label="pourriture brune" if detected else "cabosse saine",
        recommendation=(
            "Pulvérisation ciblée sur la parcelle concernée."
            if detected
            else "Aucune action immédiate ; poursuivre la surveillance."
        ),
        model=MODEL_NAME,
        is_demo=IS_DEMO,
    )
