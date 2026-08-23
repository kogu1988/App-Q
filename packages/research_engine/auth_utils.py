"""Parola hash'leme ve doğrulama — stdlib PBKDF2 (ek bağımlılık yok).

Format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
Karşılaştırma sabit-zamanlı (hmac.compare_digest) yapılır.
"""
from __future__ import annotations

import hashlib
import hmac
import os

_ITERATIONS = 100_000
_ALGO = "pbkdf2_sha256"


def hash_password(password: str, iterations: int = _ITERATIONS) -> str:
    """Parolayı PBKDF2-SHA256 ile tuzlayıp hash'ler."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{_ALGO}${iterations}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Parolayı saklı hash ile sabit-zamanlı karşılaştırır."""
    try:
        algo, iterations, salt_hex, hash_hex = stored.split("$")
        if algo != _ALGO:
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(dk, expected)
    except (ValueError, TypeError):
        return False
