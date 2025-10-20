"""Servidor FastAPI mínimo para desarrollo con el frontend Electron."""

from __future__ import annotations

import logging
from typing import Dict

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

LOGGER = logging.getLogger(__name__)

app = FastAPI(title="Florería Carlitos API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=Dict[str, str])
def read_health() -> Dict[str, str]:
    """Simple verificación de estado utilizada por el frontend."""
    return {"status": "ok"}


def main() -> None:
    """Punto de entrada para `npm run dev:backend`."""
    LOGGER.info("Iniciando backend de desarrollo en http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
