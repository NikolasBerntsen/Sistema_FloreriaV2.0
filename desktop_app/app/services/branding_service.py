from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

__all__ = ["BrandingInfo", "get_branding"]

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class BrandingInfo:
    """Información de identidad visual para la interfaz de usuario."""

    name: str
    logo_path: Optional[Path]
    tagline: Optional[str]


_DEFAULT_NAME = "Florería Carlitos"


def _get_from_config(config: Mapping[str, Mapping[str, str]], key: str) -> Optional[str]:
    branding_section = config.get("branding") if isinstance(config, Mapping) else None
    if not branding_section or key not in branding_section:
        return None
    value = branding_section[key]
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def get_branding(config: Mapping[str, Mapping[str, str]]) -> BrandingInfo:
    """Obtiene la información de branding combinando configuración y entorno."""

    name = os.getenv("FLORERIA_BRAND_NAME") or _get_from_config(config, "name") or _DEFAULT_NAME
    tagline = os.getenv("FLORERIA_BRAND_TAGLINE") or _get_from_config(config, "tagline")

    logo_value = os.getenv("FLORERIA_BRAND_LOGO") or _get_from_config(config, "logo")
    logo_path: Optional[Path] = None

    if logo_value:
        candidate = Path(logo_value).expanduser()
        if candidate.exists():
            logo_path = candidate
        else:  # pragma: no cover - depende de archivos externos
            LOGGER.warning("No se encontró el logotipo en la ruta %s", candidate)

    return BrandingInfo(name=name, logo_path=logo_path, tagline=tagline)
