#!/usr/bin/env python3
"""
FLA — Free LLM API
Skrip utama: ambil data dari semua provider, render README.md & api/models.json.

Provider "sederhana" dikonfigurasi lewat config/providers.yaml.
Provider "kompleks" (Groq, Gemini) tetap di-handle lewat fetchers.py.
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

from data import FALLBACK_GEMINI_LIMITS, TRIAL_PROVIDERS_STATIC
from fetchers import (
    fetch_gemini_limits,
    fetch_groq_models,
    fetch_intelligence_scores,
    safe_fetch,
)
from provider_engine import fetch_generic_provider, load_providers_config
from utils import (
    MISSING_MODELS,
    create_logger,
    generate_toc,
    get_human_limits,
    provider_meta,
)

load_dotenv()

_SCRIPT_DIR = Path(__file__).parent
_REPO_ROOT = _SCRIPT_DIR.parent

# Provider yang punya custom handler Python (tidak diambil dari YAML engine)
_CUSTOM_PROVIDERS = {"groq", "gemini"}


# ── Gemini model list ──────────────────────────────────────────────────────
_GEMINI_MODEL_DEFS: list[tuple[str, str, str]] = [
    # (display_id, display_name, quota_key)
    ("gemini-3.6-flash",             "Gemini 3.6 Flash",          "gemini-3.6-flash"),
    ("gemini-3.5-flash",             "Gemini 3.5 Flash",          "gemini-3.5-flash"),
    ("gemini-3-flash-preview",       "Gemini 3 Flash",            "gemini-3-flash"),
    ("gemini-3.5-flash-lite",        "Gemini 3.5 Flash-Lite",     "gemini-3.5-flash-lite"),
    ("gemini-3.1-flash-lite",        "Gemini 3.1 Flash-Lite",     "gemini-3.1-flash-lite"),
    ("gemini-2.5-flash",             "Gemini 2.5 Flash",          "gemini-2.5-flash"),
    ("gemini-2.5-flash-lite",        "Gemini 2.5 Flash-Lite",     "gemini-2.5-flash-lite"),
    ("gemini-3.1-flash-tts-preview", "Gemini 3.1 Flash TTS",      "gemini-3.1-flash-tts"),
    ("gemini-2.5-flash-preview-tts", "Gemini 2.5 Flash TTS",      "gemini-2.5-flash-tts"),
    ("gemini-robotics-er-1.6-preview","Gemini Robotics-ER 1.6",   "gemini-robotics-er-1.6-preview"),
    ("gemini-robotics-er-1.5-preview","Gemini Robotics-ER 1.5",   "gemini-robotics-er-1.5-preview"),
    ("gemma-4-31b-it",               "Gemma 4 31B Instruct",      "gemma-4-31b"),
    ("gemma-4-26b-a4b-it",           "Gemma 4 26B A4B Instruct",  "gemma-4-26b"),
    ("gemma-3-27b-it",               "Gemma 3 27B Instruct",      "gemma-3-27b"),
    ("gemma-3-12b-it",               "Gemma 3 12B Instruct",      "gemma-3-12b"),
    ("gemma-3-4b-it",                "Gemma 3 4B Instruct",       "gemma-3-4b"),
    ("gemma-3-1b-it",                "Gemma 3 1B Instruct",       "gemma-3-1b"),
]


def _build_gemini_models(gemini_data: dict) -> list[dict]:
    return [
        {"id": display_id, "name": name, "limits": gemini_data.get(quota_key, {})}
        for display_id, name, quota_key in _GEMINI_MODEL_DEFS
    ]


def main() -> None:
    logger = create_logger("Main")

    # ── Muat konfigurasi provider dari YAML ───────────────────────────────
    providers_cfg: dict = load_providers_config().get("providers", {})
    yaml_providers = {k: v for k, v in providers_cfg.items() if k not in _CUSTOM_PROVIDERS}

    # ── Buat logger untuk semua provider ──────────────────────────────────
    loggers: dict = {
        key: create_logger(cfg.get("display_name", key.capitalize()))
        for key, cfg in providers_cfg.items()
    }
    loggers["gemini"] = create_logger("Google AI Studio")
    loggers["groq"]   = create_logger("Groq")
    loggers["aa"]     = create_logger("Artificial Analysis")

    # ── Bangun tasks: YAML providers + custom ─────────────────────────────
    def fetch_gemini():
        g = safe_fetch(
            "Google AI Studio",
            fetch_gemini_limits,
            loggers["gemini"],
            default={},
            needed_env=("GCP_PROJECT_ID",),
        )
        if not g:
            loggers["gemini"].warning("Pakai FALLBACK_GEMINI_LIMITS (GCP tidak tersedia)")
            g = dict(FALLBACK_GEMINI_LIMITS)
        return "gemini", g

    tasks: dict = {}

    # Provider dari YAML (generik)
    for key, cfg in yaml_providers.items():
        tasks[key] = lambda k=key, c=cfg: (k, fetch_generic_provider(k, c, loggers[k]))

    # Custom handlers
    tasks["gemini"] = fetch_gemini
    tasks["groq"]   = lambda: ("groq", safe_fetch(
        "Groq", fetch_groq_models, loggers["groq"], needed_env=("GROQ_API_KEY",)
    ))

    # ── Jalankan fetch secara paralel ─────────────────────────────────────
    results: dict = {}
    logger.info("Starting concurrent fetches...")
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        future_to_name = {executor.submit(fn): name for name, fn in tasks.items()}
        for future in as_completed(future_to_name):
            task_name = future_to_name[future]
            try:
                key, data = future.result()
                results[key] = data
            except Exception as exc:
                logger.exception(f"Task '{task_name}' generated an exception: {exc}")

    # ── Fetch Intelligence Scores (serial, setelah semua fetch selesai) ───
    intelligence_scores = safe_fetch(
        "Artificial Analysis",
        fetch_intelligence_scores,
        loggers["aa"],
        default={},
    )

    # ── Build template variables ───────────────────────────────────────────
    gemini_text_models = _build_gemini_models(results.get("gemini", {}))

    if MISSING_MODELS:
        logger.warning("Model tanpa mapping nama di config/models.yaml:")
        logger.warning("\n" + "\n".join(f'  "{m}": "{m}"' for m in sorted(MISSING_MODELS)))

    # ── Render README.md ───────────────────────────────────────────────────
    env = Environment(loader=FileSystemLoader(str(_SCRIPT_DIR)))
    env.globals.update(get_human_limits=get_human_limits, provider_meta=provider_meta)
    template = env.get_template("README_template.md")

    rendered = template.render(
        openrouter_models=results.get("openrouter", []),
        gemini_text_models=gemini_text_models,
        kilo_models=results.get("kilo", []),
        groq_models=results.get("groq", []),
        cohere_models=results.get("cohere", []),
        cloudflare_models=results.get("cloudflare", []),
        trial_providers_static=TRIAL_PROVIDERS_STATIC,
        hyperbolic_models=results.get("hyperbolic", []),
        samba_models=results.get("sambanova", []),
        scaleway_models=results.get("scaleway", []),
    )

    warning_header = """<!--
PERINGATAN: JANGAN EDIT FILE INI LANGSUNG.
File di-generate oleh src/pull_available_models.py
Ubah src/README_template.md atau skrip generator-nya.
-->
"""
    final_content = warning_header + rendered
    final_content = final_content.replace("{{TOC}}", generate_toc(final_content))

    readme_path = _REPO_ROOT / "README.md"
    readme_path.write_text(final_content, encoding="utf-8")
    logger.info("README.md berhasil ditulis.")

    # ── Output api/models.json ─────────────────────────────────────────────
    api_dir = _REPO_ROOT / "api"
    api_dir.mkdir(exist_ok=True)

    def inject_scores(models: list[dict]) -> list[dict]:
        """Tambahkan intelligence_score ke setiap model, lalu sort DESC."""
        for m in models:
            name_lower = (m.get("name") or "").lower()
            id_lower   = (m.get("id") or "").lower()
            score = intelligence_scores.get(name_lower) or intelligence_scores.get(id_lower)
            m["intelligence_score"] = score
        return sorted(
            models,
            key=lambda x: (x["intelligence_score"] is None, -(x["intelligence_score"] or 0)),
        )

    # Bangun providers_json secara DINAMIS dari YAML + custom providers
    providers_json: dict = {}

    # Provider dari YAML
    for key, cfg in providers_cfg.items():
        if key in _CUSTOM_PROVIDERS:
            continue
        providers_json[key] = {
            "tier":   cfg.get("tier", "free"),
            "website": cfg.get("website", ""),
            "models": inject_scores(results.get(key, [])),
        }

    # Custom providers
    providers_json["gemini"] = {"tier": "free",  "website": "https://aistudio.google.com/app/apikey", "models": inject_scores(gemini_text_models)}
    providers_json["groq"]   = {"tier": "free",  "website": "https://console.groq.com/keys", "models": inject_scores(results.get("groq", []))}

    models_json: dict = {
        "generated_at": __import__("datetime").datetime.now(
            __import__("datetime").UTC
        ).isoformat().replace("+00:00", "Z"),
        "providers": providers_json,
    }

    json_path = api_dir / "models.json"
    json_path.write_text(json.dumps(models_json, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(p["models"]) for p in models_json["providers"].values())
    logger.info(f"api/models.json berhasil ditulis ({total} model total).")


if __name__ == "__main__":
    main()
