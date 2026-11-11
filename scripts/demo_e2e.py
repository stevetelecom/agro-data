"""Scénario de démonstration de bout en bout, reproductible en une commande.

Rôle : rejouer le parcours de la soutenance sans pytest — ingestion de 48 h
d'humidité critique, diagnostic IA, lecture des KPIs et de la courbe de prix —
et vérifier les critères 1, 3, 4 et 6 du CDC §17.

Prérequis : le backend tourne (`uvicorn app.main:app`). Le script n'utilise que
la bibliothèque standard.

Usage :

    python scripts/demo_e2e.py
    AGRO_API_BASE=http://127.0.0.1:8000 python scripts/demo_e2e.py

Code de sortie : 0 si toute la chaîne répond comme attendu, 1 sinon.
Auteur : MEKONTSO Olivier Steve (MOD-G1, issue #20).
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

API_BASE = os.getenv("AGRO_API_BASE", "http://127.0.0.1:8000").rstrip("/")
DEVICE_KEY = os.getenv("DEVICE_API_KEY", "agro-device-demo-key")
ADMIN_EMAIL = os.getenv("DEMO_ADMIN_EMAIL", "acheteur@ebolowa.cm")
ADMIN_PASSWORD = os.getenv("DEMO_ADMIN_PASSWORD", "demo1234")

# Le scénario critique doit alimenter la parcelle du jeu d'essai : un boîtier
# inconnu formerait un second groupe et diviserait l'indice global par deux
# (moyenne des parcelles), alors que la parcelle démontrée est bien en crise.
DEVICE_ID = os.getenv("DEMO_DEVICE_ID", "AMB-P001")
PNG = b"\x89PNG\r\n\x1a\n" + b"cabosse-demo"


def _request(method: str, path: str, *, body: bytes | None = None, headers: dict | None = None):
    """Appelle l'API et renvoie (statut, corps décodé)."""
    req = urllib.request.Request(f"{API_BASE}{path}", data=body, method=method)
    for cle, valeur in (headers or {}).items():
        req.add_header(cle, valeur)
    try:
        with urllib.request.urlopen(req, timeout=10) as reponse:
            brut = reponse.read()
            return reponse.status, json.loads(brut) if brut else None
    except urllib.error.HTTPError as erreur:
        return erreur.code, json.loads(erreur.read() or b"{}")
    except urllib.error.URLError as erreur:
        raise SystemExit(
            f"ÉCHEC : backend injoignable sur {API_BASE} ({erreur.reason}).\n"
            "Démarre-le d'abord dans un autre terminal, depuis la racine :\n"
            "  cd backend && python -m uvicorn app.main:app --port 8000\n"
            "Si l'API écoute ailleurs : AGRO_API_BASE=http://127.0.0.1:PORT "
            "python scripts/demo_e2e.py"
        ) from None


def _json(method: str, path: str, payload: dict, headers: dict | None = None):
    entetes = {"Content-Type": "application/json", **(headers or {})}
    return _request(method, path, body=json.dumps(payload).encode(), headers=entetes)


def _multipart(champ: str, nom: str, contenu: bytes, type_mime: str) -> tuple[bytes, str]:
    """Construit un corps multipart/form-data minimal."""
    frontiere = f"----agro{uuid.uuid4().hex}"
    corps = (
        f"--{frontiere}\r\n"
        f'Content-Disposition: form-data; name="{champ}"; filename="{nom}"\r\n'
        f"Content-Type: {type_mime}\r\n\r\n"
    ).encode() + contenu + f"\r\n--{frontiere}--\r\n".encode()
    return corps, f"multipart/form-data; boundary={frontiere}"


def _verifier(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"ÉCHEC : {message}")
    print(f"  OK  {message}")


def main() -> int:
    print(f"AGRO-DATA — démonstration de bout en bout sur {API_BASE}")

    # 0. Santé du service
    statut, _ = _request("GET", "/health")
    _verifier(statut == 200, "le backend répond sur /health")

    # 1. Connexion de l'acheteur (compte de démonstration)
    statut, corps = _json(
        "POST", "/api/v1/auth/login", {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    _verifier(statut == 200 and "access_token" in (corps or {}), "connexion JWT de l'acheteur")
    jeton = corps["access_token"]
    auth = {"Authorization": f"Bearer {jeton}"}

    # 2. Ingestion : 48 mesures horaires à 90 % d'humidité (critère 1)
    maintenant = int(time.time())
    acceptees = 0
    for decalage in range(48):
        mesure = {
            "device_id": DEVICE_ID,
            "timestamp": maintenant - (decalage + 1) * 3600,
            "climate": {
                "temperature_c": 27.0,
                "air_humidity_pct": 90.0,
                "soil_humidity_pct": 61.0,
            },
            # Le boîtier embarque l'IA : les 12 dernières heures signalent la
            # pourriture brune, comme le scénario critique du simulateur. Sans
            # détection, la formule RM2 plafonne à 60, soit « modéré ».
            "diagnostic_ia": {
                "phytophthora_detected": 1 if decalage < 12 else 0,
                "confidence": 0.61 if decalage < 12 else 0.9,
            },
            "geo_enc": "lat:2.383,lon:11.283",
        }
        statut, _ = _json(
            "POST", "/api/v1/measurements", mesure, {"X-API-Key": DEVICE_KEY}
        )
        acceptees += statut == 201
    _verifier(acceptees == 48, "48 mesures acceptées et écrites dans le Data Lake")

    # 3. Rejet d'une mesure malveillante (critère 6)
    mauvaise = {
        "device_id": "../etc/passwd",
        "timestamp": maintenant - 60,
        "climate": {"temperature_c": 27.0, "air_humidity_pct": 90.0, "soil_humidity_pct": 61.0},
        "diagnostic_ia": {"phytophthora_detected": 0, "confidence": 0.9},
        "geo_enc": "",
    }
    statut, _ = _json("POST", "/api/v1/measurements", mauvaise, {"X-API-Key": DEVICE_KEY})
    _verifier(statut == 422, "device_id malveillant rejeté (422)")

    # 4. Diagnostic IA (critère 4)
    corps_mp, type_mp = _multipart("image", "cabosse.png", PNG, "image/png")
    statut, diagnostic = _request(
        "POST", "/api/v1/diagnostic", body=corps_mp, headers={**auth, "Content-Type": type_mp}
    )
    _verifier(
        statut == 200 and diagnostic.get("phytophthora_detected") in (0, 1),
        f"diagnostic IA : drapeau={diagnostic.get('phytophthora_detected')} "
        f"confiance={diagnostic.get('confidence')} (is_demo={diagnostic.get('is_demo')})",
    )

    # 5. KPIs et alerte RM1 (critère 3)
    statut, kpis = _request("GET", "/api/v1/kpis", headers=auth)
    _verifier(statut == 200, "GET /api/v1/kpis répond")
    _verifier(kpis["active_alerts"] >= 1, "au moins une alerte active après 48 h > 85 %")
    _verifier(
        kpis["global_infestation_index"] >= 60,
        f"indice d'infestation={kpis['global_infestation_index']} (niveau {kpis['level']})",
    )

    # 6. Courbe de prix (critère 5, données identiques par l'API)
    statut, prix = _request("GET", "/api/v1/prices/forecast", headers=auth)
    _verifier(statut == 200 and bool(prix.get("points")), "GET /api/v1/prices/forecast répond")
    dernier = prix["points"][-1]
    _verifier(
        dernier["adjusted_price"] > dernier["reference_price"],
        f"prix ajusté {dernier['adjusted_price']} > référence {dernier['reference_price']} "
        f"({prix['unit']}, is_demo={prix['is_demo']})",
    )

    print("\nDémonstration réussie : ingestion -> Data Lake -> IA -> KPIs -> prix.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
