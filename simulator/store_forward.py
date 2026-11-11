"""Tampon local Store-and-Forward (type MicroSD).

Rôle : conserver les mesures produites hors ligne et les renvoyer au retour du
réseau, dans l'ordre et sans doublon (BNF1, BNF8, critère §17.2). Le boîtier
comme le simulateur utilisent la même logique : un fichier JSON Lines local,
une mesure par ligne, réécrit après chaque envoi réussi.

Auteur : NTEINTIE Mounpain (MOD-C2) — implémentation reprise par
MEKONTSO Olivier Steve (SM) après l'absence de livraison du bloc C.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from simulator.generator import (
    DEFAULT_API_BASE,
    DEFAULT_API_KEY,
    PermanentSendError,
    TransientSendError,
    send_measurement,
)


@dataclass
class FlushReport:
    """Bilan d'une tentative de vidage du tampon.

    Attributes:
        sent: mesures acceptées par l'API.
        rejected: mesures refusées définitivement (422, 401) et donc retirées.
        remaining: mesures encore dans le tampon après la tentative.
        error: motif du dernier échec temporaire, vide si le tampon est vide.
    """

    sent: int = 0
    rejected: int = 0
    remaining: int = 0
    error: str = ""
    details: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        """Vrai si plus rien n'attend dans le tampon."""
        return self.remaining == 0 and not self.error


def measurement_key(payload: dict) -> tuple[str, int]:
    """Clé d'unicité d'une mesure : le couple que le backend protège déjà."""
    return (str(payload.get("device_id")), int(payload.get("timestamp", 0)))


class StoreAndForward:
    """File persistante de mesures en attente d'envoi.

    Le fichier survit à une coupure d'alimentation : c'est la MicroSD du
    boîtier. Une mesure n'est retirée qu'une fois acceptée (ou refusée
    définitivement) par l'API, ce qui rend le renvoi sûr : le backend rejette
    les doublons en 422, la reprise ne duplique donc aucune ligne.
    """

    def __init__(
        self,
        path: str | os.PathLike[str],
        sender: Callable[[dict], object] | None = None,
    ) -> None:
        """Ouvre (ou crée) le tampon.

        Args:
            path: fichier JSON Lines du tampon.
            sender: fonction d'envoi ; par défaut ``send_measurement`` vers
                ``127.0.0.1:8000`` avec la clé de démonstration.
        """
        self.path = Path(path)
        self._sender = sender or (lambda payload: send_measurement(payload))

    @classmethod
    def for_api(
        cls,
        path: str | os.PathLike[str],
        *,
        api_base: str = DEFAULT_API_BASE,
        api_key: str = DEFAULT_API_KEY,
        timeout: float = 10.0,
    ) -> "StoreAndForward":
        """Construit un tampon branché sur une API réelle."""
        return cls(
            path,
            sender=lambda payload: send_measurement(
                payload, api_base=api_base, api_key=api_key, timeout=timeout
            ),
        )

    # ------------------------------------------------------------------ lecture

    def pending(self) -> list[dict]:
        """Retourne les mesures en attente, de la plus ancienne à la plus récente.

        Une ligne corrompue (écriture interrompue par une coupure) est ignorée
        plutôt que de bloquer la reprise : perdre une heure vaut mieux que
        perdre tout le tampon.
        """
        if not self.path.exists():
            return []
        mesures: list[dict] = []
        for ligne in self.path.read_text(encoding="utf-8").splitlines():
            ligne = ligne.strip()
            if not ligne:
                continue
            try:
                charge = json.loads(ligne)
            except json.JSONDecodeError:
                continue
            if isinstance(charge, dict) and "device_id" in charge and "timestamp" in charge:
                mesures.append(charge)
        return mesures

    def __len__(self) -> int:
        return len(self.pending())

    # --------------------------------------------------------------- écriture

    def enqueue(self, payload: dict) -> bool:
        """Ajoute une mesure au tampon.

        Returns:
            ``True`` si la mesure a été ajoutée, ``False`` si le couple
            (``device_id``, ``timestamp``) est déjà en attente.
        """
        existantes = {measurement_key(m) for m in self.pending()}
        if measurement_key(payload) in existantes:
            return False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fichier:
            fichier.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        return True

    def enqueue_many(self, payloads: Iterable[dict]) -> int:
        """Ajoute plusieurs mesures et retourne le nombre réellement ajouté."""
        return sum(1 for payload in payloads if self.enqueue(payload))

    def _rewrite(self, payloads: list[dict]) -> None:
        """Réécrit le tampon de façon atomique (fichier temporaire puis renommage)."""
        temporaire = self.path.with_suffix(self.path.suffix + ".tmp")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with temporaire.open("w", encoding="utf-8") as fichier:
            for payload in payloads:
                fichier.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
            fichier.flush()
            os.fsync(fichier.fileno())
        os.replace(temporaire, self.path)

    # ------------------------------------------------------------------ envoi

    def flush(self, sender: Callable[[dict], object] | None = None) -> FlushReport:
        """Envoie les mesures en attente, dans l'ordre, jusqu'au premier échec.

        Un refus définitif (422 : mesure invalide ou doublon déjà persisté)
        retire la mesure du tampon ; un échec temporaire (réseau, 5xx, 429)
        arrête le vidage pour conserver l'ordre chronologique.

        Args:
            sender: fonction d'envoi ponctuelle, prioritaire sur celle du tampon.

        Returns:
            Le bilan de la tentative.
        """
        envoyer = sender or self._sender
        restantes = self.pending()
        rapport = FlushReport()
        a_conserver = list(restantes)

        for index, payload in enumerate(restantes):
            try:
                envoyer(payload)
            except PermanentSendError as erreur:
                rapport.rejected += 1
                rapport.details.append(f"rejeté {measurement_key(payload)} : {erreur}")
                a_conserver = [m for m in a_conserver if measurement_key(m) != measurement_key(payload)]
                continue
            except TransientSendError as erreur:
                rapport.error = str(erreur)
                break
            except Exception as erreur:  # noqa: BLE001 - filet pour un capteur bavard
                rapport.error = f"envoi interrompu : {erreur}"
                break
            else:
                rapport.sent += 1
                a_conserver = [m for m in a_conserver if measurement_key(m) != measurement_key(payload)]

        # Le tampon est réécrit même en cas d'échec : les mesures déjà parties
        # ne doivent pas repartir au prochain démarrage.
        if rapport.sent or rapport.rejected or not restantes:
            self._rewrite(a_conserver)

        rapport.remaining = len(a_conserver)
        if rapport.remaining == 0:
            rapport.error = ""
        return rapport

    def drain(self) -> FlushReport:
        """Vide le tampon tant que des mesures passent.

        Utile quand l'API répond lentement ou refuse ponctuellement : chaque
        passage envoie ce qui peut l'être, et la boucle s'arrête au premier
        échec temporaire.
        """
        total = FlushReport()
        while True:
            rapport = self.flush()
            total.sent += rapport.sent
            total.rejected += rapport.rejected
            total.details.extend(rapport.details)
            total.remaining = rapport.remaining
            if rapport.error or rapport.remaining == 0:
                total.error = rapport.error
                return total
