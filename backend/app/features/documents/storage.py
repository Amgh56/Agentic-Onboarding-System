import uuid
from pathlib import Path

from app.core import config

UPLOADS_DIR = config.UPLOADS_DIR


def save_file(filename: str, data: bytes) -> str:
    stored_name = f"{uuid.uuid4().hex}{Path(filename).suffix}"
    UPLOADS_DIR.mkdir(exist_ok=True)
    (UPLOADS_DIR / stored_name).write_bytes(data)
    return stored_name


def file_path(stored_name: str) -> Path:
    return UPLOADS_DIR / stored_name


def delete_file(stored_name: str) -> None:
    file_path(stored_name).unlink(missing_ok=True)
