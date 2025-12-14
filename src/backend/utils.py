import secrets


def fake_hash_password(password: str):
    return "fakehashed" + password


def compare_digest(a: bytes, b: bytes) -> bool:
    return secrets.compare_digest(a, b)
