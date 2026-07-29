import logging
import os
import re
from pathlib import Path

import requests
import requests_cache
import yaml
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── Paths ──────────────────────────────────────────────────────────────────
_SRC_DIR = Path(__file__).parent
_CONFIG_DIR = _SRC_DIR.parent / "config"
_REPO_ROOT = _SRC_DIR.parent

# ── Load model name mapping from YAML ─────────────────────────────────────
def _load_model_mapping() -> dict[str, str]:
    """Baca mapping model → nama dari config/models.yaml."""
    yaml_path = _CONFIG_DIR / "models.yaml"
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("model_to_name", {})

MODEL_TO_NAME_MAPPING: dict[str, str] = _load_model_mapping()

MISSING_MODELS: set[str] = set()

# ── Logging ────────────────────────────────────────────────────────────────
def create_logger(provider_name: str) -> logging.Logger:
    logger = logging.getLogger(provider_name)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(f"{provider_name}: %(message)s")
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

# ── Model helpers ──────────────────────────────────────────────────────────
def get_model_name(model_id: str) -> str:
    key = model_id.lower()
    if key in MODEL_TO_NAME_MAPPING:
        return MODEL_TO_NAME_MAPPING[key]
    MISSING_MODELS.add(key)
    return model_id

def env_ready(*keys: str) -> bool:
    """True jika semua env key terisi."""
    return all(os.environ.get(k) for k in keys)

# ── HTTP Session ───────────────────────────────────────────────────────────
def get_session() -> requests.Session:
    """Mengembalikan requests.Session dengan konfigurasi retry otomatis, atau CachedSession jika FLA_USE_CACHE=1."""
    if os.environ.get("FLA_USE_CACHE") == "1":
        cache_path = str(_REPO_ROOT / ".cache")
        session = requests_cache.CachedSession(
            cache_path,
            backend="sqlite",
            expire_after=1800,  # 30 menit
            allowable_methods=("GET", "POST"),
            allowable_codes=(200,),
        )
    else:
        session = requests.Session()

    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

# ── Formatting helpers ────────────────────────────────────────────────────
LIMIT_LABELS_ID: dict[str, str] = {
    "requests/minute": "req/menit",
    "requests/day": "req/hari",
    "requests/month": "req/bulan",
    "requests/hour": "req/jam",
    "tokens/minute": "token/menit",
    "tokens/day": "token/hari",
    "tokens/hour": "token/jam",
    "audio-seconds/minute": "detik-audio/menit",
}

def get_human_limits(model: dict | None, separator: str = "<br>") -> str:
    if not model or "limits" not in model:
        return ""
    limits = {k: v for k, v in model["limits"].items() if v is not None}
    parts: list[str] = []
    for key, value in limits.items():
        label = LIMIT_LABELS_ID.get(key, key)
        if isinstance(value, (int, float)):
            parts.append(f"{value:,} {label}".replace(",", "."))
        else:
            parts.append(f"{value} {label}")
    return separator.join(parts)

def provider_meta(jenis: str = "gratis", batas: str | None = None, catatan: str | None = None) -> str:
    """Blok meta singkat di bawah judul provider (tampil konsisten)."""
    lines = [f"> **Jenis:** {jenis}"]
    if batas:
        lines.append(f"> **Batas:** {batas}")
    if catatan:
        lines.append(f"> **Catatan:** {catatan}")
    return "\n".join(lines) + "\n\n"

def generate_toc(markdown: str) -> str:
    toc_lines: list[str] = []
    headings = re.findall(r"^(#{2,3}) +(.+)", markdown, re.MULTILINE)
    for hashes, title in headings:
        display = re.sub(r"\[(.*?)\]\([^)]*\)", r"\1", title)
        anchor = display.lower()
        anchor = re.sub(r"[^a-z0-9 \-_]", "", anchor)
        anchor = anchor.replace(" ", "-").replace("--", "-").strip("-")
        indent = "  " if len(hashes) == 3 else ""
        toc_lines.append(f"{indent}- [{display}](#{anchor})")
    return "\n".join(toc_lines)
