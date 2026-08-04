import hashlib


def generate_sha256(data: bytes) -> str:
    """
    Generate SHA-256 hash from file bytes.
    """

    return hashlib.sha256(data).hexdigest()