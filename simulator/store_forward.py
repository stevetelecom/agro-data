"""Tampon local Store-and-Forward (type MicroSD).

Rôle : conserver les mesures hors ligne dans un fichier JSONL persistant et
les renvoyer au retour du réseau (BNF1, BNF8). Le fichier survit à un
redémarrage du processus, comme une vraie MicroSD : les mesures en attente
sont rechargées à l'ouverture du spool.

Usage type::

    spool = StoreForward("data_lake/spool.jsonl")
    spool.buffer(json.dumps(measurement))   # réseau coupé : on tamponne
    ...
    result = spool.flush(send_fn)           # réseau rétabli : on renvoie

`send_fn` est un appelable recevant le payload JSON (chaîne) et levant une
exception en cas d'échec. Les messages rejetés restent dans le tampon pour
une tentative ultérieure ; les doublons côté serveur sont gérés par la
règle (`device_id`, `timestamp`) du contrat §3.4.

Bibliothèque standard uniquement.

Auteur : Sahoda (MOD-C2).
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FlushResult:
    """Bilan d'une tentative de reprise d'envoi.

    :param sent: payloads JSON effectivement acceptés par `send_fn`.
    :param pending: payloads toujours en attente (échec ou `send_fn` absent).
    """

    sent: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)


class StoreForward:
    """File persistante de messages JSON en attente d'envoi.

    Le spool est un fichier JSONL : une ligne par message, chaque ligne
    contenant la chaîne JSON exacte à transmettre. L'écriture est suivie
    d'un `flush`/`fsync` à chaque ajout pour ne pas perdre de mesure en cas
    de coupure. La réécriture après envoi réussi passe par un fichier
    temporaire puis `os.replace` : le tampon n'est jamais tronqué à moitié.

    :param path: chemin du fichier tampon (créé si absent).
    """

    def __init__(self, path: str | os.PathLike) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    @property
    def path(self) -> Path:
        """Chemin du fichier tampon."""
        return self._path

    def buffer(self, payload: str | dict) -> None:
        """Ajoute un message au tampon et le synchronise sur disque.

        :param payload: mesure déjà sérialisée (`str`) ou dictionnaire
            conforme au contrat, sérialisé ici en JSON.
        """
        text = payload if isinstance(payload, str) else json.dumps(payload)
        with self._path.open("a", encoding="utf-8") as spool_file:
            spool_file.write(text + "\n")
            spool_file.flush()
            os.fsync(spool_file.fileno())

    def pending(self) -> list[str]:
        """Retourne les payloads en attente, dans l'ordre d'arrivée."""
        return [line.strip() for line in self._path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def __len__(self) -> int:
        """Nombre de messages en attente."""
        return sum(1 for line in self._path.open("rb") if line.strip())

    def flush(self, send_fn=None) -> FlushResult:
        """Tente de renvoyer tous les messages en attente, du plus ancien au plus récent.

        Pour chaque message, `send_fn(payload)` est appelé ; s'il ne lève
        pas d'exception, le message est considéré envoyé. Les messages en
        échec restent dans le tampon. Si `send_fn` est `None`, aucun envoi
        n'est tenté et tout reste en attente.

        :param send_fn: appelable `str -> None`, ou `None` pour simuler
            l'absence de réseau.
        :return: `FlushResult` avec les payloads envoyés et ceux restés
            en attente.
        """
        messages = self.pending()
        result = FlushResult()
        if send_fn is None:
            result.pending = messages
            return result

        still_pending: list[str] = []
        for payload in messages:
            try:
                send_fn(payload)
            except Exception:
                # Réseau toujours coupé ou serveur indisponible : on garde
                # le message pour la prochaine reprise.
                still_pending.append(payload)
            else:
                result.sent.append(payload)
        result.pending = still_pending
        self._rewrite(still_pending)
        return result

    def _rewrite(self, messages: list[str]) -> None:
        """Réécrit le tampon de façon atomique avec uniquement `messages`."""
        fd, tmp_name = tempfile.mkstemp(dir=self._path.parent, prefix=self._path.name + ".")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                for payload in messages:
                    tmp_file.write(payload + "\n")
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            os.replace(tmp_name, self._path)
        except BaseException:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
