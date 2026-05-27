from __future__ import annotations

import os
import secrets

from fastapi import Header, HTTPException, status

from app.services.env_loader import load_dotenv_file

load_dotenv_file()


def require_api_key(x_api_key: str = Header(default="", alias="X-API-Key")) -> None:
    expected_key = os.getenv("APP_API_KEY", "").strip()
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configure APP_API_KEY no ambiente antes de usar a API.",
        )

    provided_key = x_api_key.strip()
    if not provided_key or not secrets.compare_digest(provided_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API inválida.",
        )
