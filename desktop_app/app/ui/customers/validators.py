"""Validadores y utilitarios compartidos para formularios de clientes."""
from __future__ import annotations

import re
from typing import Mapping

__all__ = [
    "EMAIL_REGEX",
    "PHONE_REGEX",
    "normalise_status",
    "validate_customer_payload",
]

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_REGEX = re.compile(r"^[0-9()+\-\s]{6,}$")


def validate_customer_payload(data: Mapping[str, object]) -> dict[str, str]:
    """Return a sanitised dictionary ensuring required fields are valid."""

    payload = {key: (str(value).strip()) for key, value in data.items() if value is not None}
    first_name = payload.get("first_name") or payload.get("name") or ""
    if not first_name:
        raise ValueError("El nombre es obligatorio")
    payload["first_name"] = first_name

    email = payload.get("email", "")
    if email and not EMAIL_REGEX.match(email):
        raise ValueError("El correo electrónico no tiene un formato válido")

    phone = payload.get("phone", "")
    if phone and not PHONE_REGEX.match(phone):
        raise ValueError("El teléfono no tiene un formato válido")

    if "status" in payload:
        payload["status"] = normalise_status(payload["status"])

    if payload.get("id") == "":
        payload.pop("id")

    return payload


def normalise_status(status: object) -> str:
    """Normalise el estado a los valores esperados por el servicio."""

    value = str(status).strip().lower()
    if value in {"inactive", "inactivo", "0"}:
        return "inactive"
    return "active" if value in {"", "active", "activo", "1"} else value
