from __future__ import annotations
import os
import streamlit as st
from pathlib import Path

APP_TITLE = "Sentinel Face Lab"
APP_ICON = "🔍"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_FILE = DATA_DIR / "rostros_db.json"
HISTORIAL_FILE = DATA_DIR / "historial.json"

SOCIAL_DOMAINS = [
    "instagram.com",
    "facebook.com",
    "x.com",
    "twitter.com",
    "linkedin.com",
    "tiktok.com",
]


def _get_secret(name: str, default=None):
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)


def external_mode() -> str:
    return str(_get_secret("EXTERNAL_SEARCH_MODE", "assist")).lower()


def lenso_api_key() -> str:
    return str(_get_secret("LENSO_API_KEY", ""))


def google_lens_enabled() -> bool:
    raw = str(_get_secret("ENABLE_GOOGLE_LENS", "false")).lower()
    return raw in {"1", "true", "yes", "on"}


def yandex_enabled() -> bool:
    raw = str(_get_secret("ENABLE_YANDEX_WEB", "true")).lower()
    return raw in {"1", "true", "yes", "on"}
