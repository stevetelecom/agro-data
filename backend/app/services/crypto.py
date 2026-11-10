"""
Rôle : chiffrement AES-256-GCM des données géospatiales (Loi 2010/012).
Auteur : NKWANE Mourad (MOD-A3).
"""

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings


def _aes_key() -> bytes:
    """Décode la clé AES-256 (32 octets) depuis la config base64."""
    raw = base64.b64decode(get_settings().agro_aes_key)
    if len(raw) != 32:
        raise ValueError("AGRO_AES_KEY doit décoder en 32 octets (AES-256)")
    return raw


def encrypt_geo(plaintext: str) -> str:
    """
    Chiffre une charge utile géospatiale en AES-256-GCM.
    Retourne nonce + ciphertext + tag, encodés en base64.
    """
    if plaintext == "":
        return ""
    aesgcm = AESGCM(_aes_key())
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_geo(token: str) -> str:
    """Déchiffre un blob geo_enc produit par encrypt_geo."""
    if token == "":
        return ""
    raw = base64.b64decode(token)
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(_aes_key())
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


def prepare_geo_enc(geo_enc: str) -> str:
    """
    Prépare geo_enc pour la persistance.
    Tout contenu non vide est chiffré AES-256-GCM côté serveur
    afin qu'aucune donnée géospatiale claire ne soit stockée (BNF3).
    """
    if not geo_enc:
        return ""
    return encrypt_geo(geo_enc)
