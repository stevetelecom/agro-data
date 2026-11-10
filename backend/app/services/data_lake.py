"""
Rôle : Data Lake simplifié — zone brute (JSON) et journal des rejets.
Auteur : NKWANE Mourad (MOD-A2).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.schemas.measurement import MeasurementCreate
from app.services.crypto import prepare_geo_enc

logger = logging.getLogger("agro_data.pipeline")


def _safe_component(value: object, default: str = "unknown") -> str:
    """Nettoie un identifiant avant de l'utiliser dans un nom de fichier."""
    texte = str(value) if value is not None else ""
    propre = "".join(char if char.isalnum() or char in "._-" else "_" for char in texte)
    return propre[:64] or default


def _lake_root() -> Path:
    """Racine du Data Lake (configurable via DATA_LAKE_DIR)."""
    root = Path(get_settings().data_lake_dir)
    raw = root / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    return root


def store_raw_measurement(payload: MeasurementCreate) -> Path:
    """
    Persiste le message JSON brut (zone brute) avant / avec le traitement.
    La zone traitée correspond aux lignes SQLAlchemy Measurement.

    `geo_enc` est chiffré AES-256-GCM avant écriture : aucune donnée
    géospatiale en clair ne doit atterrir dans la zone brute (BNF3).
    """
    root = _lake_root()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    filename = f"{_safe_component(payload.device_id)}_{payload.timestamp}_{stamp}.json"
    path = root / "raw" / filename
    data = payload.model_dump(mode="json")
    if data.get("geo_enc"):
        data["geo_enc"] = prepare_geo_enc(data["geo_enc"])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("data_lake raw stored path=%s device_id=%s", path, payload.device_id)
    return path


def log_rejection(device_id: str | None, timestamp: int | None, reason: str) -> None:
    """Journalise un rejet pipeline (logger + fichier rejects.log)."""
    root = _lake_root()
    line = (
        f"{datetime.now(timezone.utc).isoformat()}\t"
        f"device_id={device_id or '-'}\t"
        f"timestamp={timestamp if timestamp is not None else '-'}\t"
        f"reason={reason}\n"
    )
    rejects = root / "rejects.log"
    with rejects.open("a", encoding="utf-8") as handle:
        handle.write(line)
    logger.warning("measurement rejected device_id=%s reason=%s", device_id, reason)


def store_raw_dict(payload: dict) -> Path | None:
    """Écrit un dict brut (ex. avant validation complète) si besoin de debug."""
    root = _lake_root()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    device = _safe_component(payload.get("device_id"))
    ts = _safe_component(payload.get("timestamp"), default="0")
    data = dict(payload)
    if isinstance(data.get("geo_enc"), str) and data["geo_enc"]:
        data["geo_enc"] = prepare_geo_enc(data["geo_enc"])
    path = root / "raw" / f"{device}_{ts}_{stamp}_raw.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
