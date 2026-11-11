"""Point d'entrée du simulateur AGRO-DATA.

Rôle : produire et, au besoin, envoyer des mesures sans écrire de code.
Exemples :

    python -m simulator --scenario sain --hours 72 --dry-run
    python -m simulator --scenario humidite_critique --hours 60
    python -m simulator --scenario coupure_reseau --buffer buffer.jsonl --wait 10

Auteur : NTEINTIE Mounpain (MOD-C1) — implémentation reprise par
MEKONTSO Olivier Steve (SM).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from simulator.generator import (
    DEFAULT_API_BASE,
    DEFAULT_API_KEY,
    DEFAULT_DEVICE_ID,
    PermanentSendError,
    TransientSendError,
    send_measurement,
)
from simulator.scenarios import SCENARIOS, build_scenario, consecutive_hours_above
from simulator.store_forward import StoreAndForward


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Lit les options de la ligne de commande."""
    parser = argparse.ArgumentParser(
        prog="python -m simulator",
        description="Simule le boîtier d'acquisition AGRO-DATA (contrat JSON §3).",
    )
    parser.add_argument("--scenario", choices=SCENARIOS, default="sain", help="situation à simuler")
    parser.add_argument("--hours", type=int, default=72, help="nombre d'heures produites (défaut 72)")
    parser.add_argument("--device-id", default=DEFAULT_DEVICE_ID, help="identifiant de l'appareil")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="URL du backend")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="clé d'API de l'appareil")
    parser.add_argument(
        "--start",
        default=None,
        help="début de la série, ISO 8601 (défaut : heure courante arrondie)",
    )
    parser.add_argument(
        "--buffer",
        default="simulator/buffer.jsonl",
        help="fichier du tampon Store-and-Forward (défaut : simulator/buffer.jsonl)",
    )
    parser.add_argument("--dry-run", action="store_true", help="afficher les messages sans les envoyer")
    parser.add_argument(
        "--send-now",
        action="store_true",
        help="envoyer immédiatement les mesures produites hors ligne (par défaut : attendre --wait)",
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=5.0,
        help="secondes de « coupure » simulée avant de renvoyer le tampon (défaut 5)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Exécute le scénario demandé et retourne un code de sortie."""
    args = parse_args(argv)
    start = datetime.fromisoformat(args.start) if args.start else None
    run = build_scenario(args.scenario, device_id=args.device_id, hours=args.hours, start=start)

    print(f"Scénario : {run.name} — {run.description}")
    print(f"{len(run.measurements)} mesures, appareil {args.device_id}, début {run.measurements[0]['timestamp']}")

    if args.dry_run:
        for payload in run.measurements:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0

    buffer = StoreAndForward.for_api(args.buffer, api_base=args.api_base, api_key=args.api_key)
    hors_ligne = run.offline_measurements()
    if hors_ligne:
        ajoutees = buffer.enqueue_many(hors_ligne)
        print(f"Coupure réseau simulée : {ajoutees} mesures écrites dans {args.buffer}")
        if not args.send_now and args.wait > 0:
            print(f"Réseau indisponible pendant {args.wait:g} s…")
            time.sleep(args.wait)
        rapport = buffer.drain()
        print(
            f"Retour du réseau : {rapport.sent} renvoyées, {rapport.rejected} refusées, "
            f"{rapport.remaining} encore en attente"
        )
        if rapport.error:
            print(f"Tampon conservé ({rapport.error})", file=sys.stderr)

    envoyees = 0
    for payload in run.online_measurements():
        try:
            send_measurement(payload, api_base=args.api_base, api_key=args.api_key)
            envoyees += 1
        except PermanentSendError as erreur:
            print(f"Mesure refusée : {erreur}", file=sys.stderr)
        except TransientSendError as erreur:
            buffer.enqueue(payload)
            print(f"Réseau de nouveau indisponible, mesure mise en attente : {erreur}", file=sys.stderr)
            break

    print(f"{envoyees} mesures envoyées en direct")
    heures_alerte = consecutive_hours_above(run.measurements)
    if heures_alerte > 48:
        print(f"Alerte RM1 : {heures_alerte} h consécutives au-dessus de 85 %")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
