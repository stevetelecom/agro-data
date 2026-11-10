"""
Rôle : limitation de débit simple en mémoire (anti abus).
Auteur : NKWANE Mourad (MOD-A6).
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.config import get_settings

_hits: dict[str, deque[float]] = defaultdict(deque)


def rate_limit_dependency(request: Request) -> None:
    """Rejette si le client dépasse rate_limit_per_minute."""
    settings = get_settings()
    limit = settings.rate_limit_per_minute
    client = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - 60.0
    q = _hits[client]
    while q and q[0] < window_start:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de requêtes — réessayez plus tard",
        )
    q.append(now)


def reset_rate_limits() -> None:
    """Réinitialise les compteurs (tests)."""
    _hits.clear()
