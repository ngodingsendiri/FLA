"""
FLA — Provider Engine
Mesin fetch generik yang didorong oleh config/providers.yaml.
Tidak perlu edit file ini untuk menambah provider baru.
"""

import os
from pathlib import Path
from typing import Any

import yaml

from data import HYPERBOLIC_IGNORED_MODELS, OPENROUTER_IGNORED_MODELS
from utils import get_model_name, get_session

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "providers.yaml"

# Shared HTTP session (retry otomatis)
session = get_session()


# ── Config Loader ───────────────────────────────────────────────────────────
def load_providers_config() -> dict[str, Any]:
    """Baca config/providers.yaml dan kembalikan sebagai dict."""
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data or {}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


# ── Generic Fetch Engine ────────────────────────────────────────────────────
def fetch_generic_provider(key: str, config: dict, logger) -> list[dict]:
    """
    Fetch model dari provider berdasarkan konfigurasi YAML.
    Mendukung: bearer auth, URL env-var substitution, pagination, dan berbagai filter.
    """
    display_name = config.get("display_name", key)

    # ── Cek env vars yang dibutuhkan ──
    auth_env = config.get("auth_env")
    url_env_vars: list[str] = config.get("url_env_vars", [])
    required_envs = ([auth_env] if auth_env else []) + url_env_vars
    missing = [e for e in required_envs if not os.environ.get(e)]
    if missing:
        logger.warning(f"Lewati {display_name}: env belum lengkap ({', '.join(missing)})")
        return []

    logger.info(f"Fetching {display_name} models...")

    # ── Build URL ──
    url = config["url"]
    for env_var in url_env_vars:
        url = url.replace(f"{{{env_var}}}", os.environ.get(env_var, ""))

    # ── Build Headers ──
    headers: dict = {}
    auth_type = config.get("auth_type", "none")
    if auth_env and auth_type == "bearer":
        headers["Authorization"] = f"Bearer {os.environ.get(auth_env, '')}"

    # ── Fetch (dengan pagination opsional) ──
    all_items: list[dict] = []
    params: dict = {}
    paginated: bool = config.get("paginated", False)
    next_token_field: str | None = config.get("next_page_token_field")
    data_path: str = config.get("data_path", "data")

    while True:
        r = session.get(url, headers=headers, params=params or None, timeout=15)
        r.raise_for_status()
        payload = r.json()
        all_items.extend(payload.get(data_path, []))

        if not paginated:
            break
        next_token = payload.get(next_token_field)
        if not next_token:
            break
        params["page_token"] = next_token

    # ── Terapkan filter ──
    filtered = _apply_filter(all_items, config.get("filter"))

    # ── Bangun hasil ──
    id_field: str = config.get("id_field", "id")
    static_limits: dict | None = config.get("static_limits")

    result: list[dict] = []
    for m in filtered:
        model_id = m.get(id_field, "")
        if not model_id:
            continue
        entry: dict = {"id": model_id, "name": get_model_name(model_id)}
        if static_limits:
            entry["limits"] = dict(static_limits)
        result.append(entry)

    logger.info(f"{display_name}: {len(result)} model ditemukan.")
    return sorted(result, key=lambda x: x["name"])


# ── Filter Engine ───────────────────────────────────────────────────────────
def _apply_filter(models: list[dict], filter_cfg: dict | None) -> list[dict]:
    """Terapkan aturan filter sesuai 'type' yang dideklarasikan di YAML."""
    if not filter_cfg:
        return models

    filter_type = filter_cfg.get("type", "")

    if filter_type == "openrouter_free":
        return [
            m for m in models
            if (
                _safe_float(m.get("pricing", {}).get("completion", "1")) +
                _safe_float(m.get("pricing", {}).get("prompt", "1"))
            ) == 0
            and ":free" in m.get("id", "")
            and m.get("id", "").lower() not in OPENROUTER_IGNORED_MODELS
        ]

    if filter_type == "field_equals":
        field = filter_cfg.get("field", "")
        value = filter_cfg.get("value")
        return [m for m in models if m.get(field) == value]

    if filter_type == "exclude_ignored":
        return [m for m in models if m.get("id") not in HYPERBOLIC_IGNORED_MODELS]

    if filter_type == "cohere_chat":
        return [
            m for m in models
            if m.get("name")
            and not m.get("is_deprecated", False)
            and "chat" in (
                set(m.get("endpoints") or []) |
                set(m.get("default_endpoints") or [])
            )
        ]

    return models


def _safe_float(val: Any, default: float = 1.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default
