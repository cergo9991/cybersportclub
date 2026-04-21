"""Функции безопасности для паролей.

Учебная версия использует безопасный хеш SHA-256 с солью.
"""

import hashlib
import hmac
import os


def hash_password(password: str) -> str:
    """Хеширует пароль пользователя."""
    salt = os.urandom(16).hex()
    digest = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return f"sha256${salt}${digest}"


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Проверяет пароль пользователя."""
    try:
        algorithm, salt, digest = password_hash.split("$", maxsplit=2)
    except ValueError:
        return False
    if algorithm != "sha256":
        return False
    candidate = hashlib.sha256(f"{salt}:{plain_password}".encode("utf-8")).hexdigest()
    return hmac.compare_digest(candidate, digest)
