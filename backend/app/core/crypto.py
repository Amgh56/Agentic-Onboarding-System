from cryptography.fernet import Fernet

from app.core.config import settings


def encrypt(text: str) -> str:
    return Fernet(settings.encryption_key).encrypt(text.encode()).decode()


def decrypt(token: str) -> str:
    return Fernet(settings.encryption_key).decrypt(token.encode()).decode()
