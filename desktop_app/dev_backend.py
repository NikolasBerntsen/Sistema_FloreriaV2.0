"""Servidor FastAPI mínimo para desarrollo con el frontend Electron."""

from __future__ import annotations

import logging
import re
import secrets
from typing import Dict

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

LOGGER = logging.getLogger(__name__)

app = FastAPI(title="Florería Carlitos API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EMAIL_REGEX = re.compile(r"^[\w.+-]+@([\w-]+\.)+[\w-]{2,}$")


class LoginRequest(BaseModel):
    """Representa las credenciales enviadas desde la UI."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Datos devueltos tras una autenticación exitosa."""

    access_token: str
    token_type: str
    full_name: str


_FAKE_USER = {
    "username": "gerencia@floreriacarlitos.com",
    "password": "Flores#2025",
    "full_name": "Gerencia General",
}


@app.get("/health", response_model=Dict[str, str])
def read_health() -> Dict[str, str]:
    """Simple verificación de estado utilizada por el frontend."""
    return {"status": "ok"}


@app.post("/auth/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def authenticate_user(payload: LoginRequest) -> LoginResponse:
    """Valida credenciales simuladas y devuelve un token efímero."""

    username = payload.username.strip().lower()
    password = payload.password

    if not EMAIL_REGEX.match(username) or len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Formato de credenciales inválido.",
        )

    if username != _FAKE_USER["username"] or password != _FAKE_USER["password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )

    access_token = secrets.token_urlsafe(32)
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        full_name=_FAKE_USER["full_name"],
    )


def main() -> None:
    """Punto de entrada para `npm run dev:backend`."""
    LOGGER.info("Iniciando backend de desarrollo en http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
