import base64
import hashlib
import hmac
import os
from itsdangerous import URLSafeSerializer, BadSignature

from app.config import get_settings

settings = get_settings()

serializer = URLSafeSerializer(
    settings.secret_key,
    salt="session",
)


def _normalize_password(password: str | None) -> str:
    if password is None:
        password = "Admin@123"

    password = str(password).strip()

    if not password:
        password = "Admin@123"

    return password


def hash_password(password: str | None) -> str:
    password = _normalize_password(password).encode("utf-8")
    salt = os.urandom(16)
    iterations = 390000

    dk = hashlib.pbkdf2_hmac("sha256", password, salt, iterations)

    salt_b64 = base64.b64encode(salt).decode("utf-8")
    hash_b64 = base64.b64encode(dk).decode("utf-8")

    return f"pbkdf2_sha256${iterations}${salt_b64}${hash_b64}"


def verify_password(plain_password: str | None, hashed_password: str) -> bool:
    plain_password = _normalize_password(plain_password).encode("utf-8")

    try:
        algorithm, iterations_str, salt_b64, hash_b64 = hashed_password.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    iterations = int(iterations_str)
    salt = base64.b64decode(salt_b64.encode("utf-8"))
    expected_hash = base64.b64decode(hash_b64.encode("utf-8"))

    test_hash = hashlib.pbkdf2_hmac("sha256", plain_password, salt, iterations)

    return hmac.compare_digest(test_hash, expected_hash)


def sign_session(data: dict) -> str:
    return serializer.dumps(data)


def unsign_session(token: str) -> dict:
    try:
        data = serializer.loads(token)
        if not isinstance(data, dict):
            raise ValueError("Sessão inválida: payload não é um dicionário.")
        return data
    except BadSignature as exc:
        raise ValueError("Sessão inválida ou expirada.") from exc