#!/usr/bin/env python3

import os
import json
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from jinja2 import Environment, FileSystemLoader

from utils import (
    create_logger,
    get_human_limits,
    provider_meta,
    generate_toc,
    MISSING_MODELS,
)
from data import FALLBACK_GEMINI_LIMITS, TRIAL_PROVIDERS_STATIC
from fetchers import (
    safe_fetch,
    fetch_gemini_limits,
    fetch_openrouter_models,
    fetch_hyperbolic_models,
    fetch_cloudflare_models,
    fetch_samba_models,
    fetch_scaleway_models,
    fetch_cohere_models,
    fetch_kilo_models,
    fetch_groq_models,
)

load_dotenv()
script_dir = os.path.dirname(os.path.abspath(__file__))

def main():
    logger = create_logger("Main")
    
    # Initialize loggers for each provider
    loggers = {
        "gemini": create_logger("Google AI Studio"),
        "openrouter": create_logger("OpenRouter"),
        "hyperbolic": create_logger("Hyperbolic"),
        "cloudflare": create_logger("Cloudflare"),
        "samba": create_logger("SambaNova"),
        "scaleway": create_logger("Scaleway"),
        "cohere": create_logger("Cohere"),
        "kilo": create_logger("Kilo"),
        "groq": create_logger("Groq"),
    }

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

    tasks = [
        fetch_gemini,
        lambda: ("openrouter", safe_fetch("OpenRouter", fetch_openrouter_models, loggers["openrouter"], default=[])),
        lambda: ("hyperbolic", safe_fetch("Hyperbolic", fetch_hyperbolic_models, loggers["hyperbolic"], default=[], needed_env=("HYPERBOLIC_API_KEY",))),
        lambda: ("cloudflare", safe_fetch("Cloudflare", fetch_cloudflare_models, loggers["cloudflare"], default=[], needed_env=("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_KEY"))),
        lambda: ("samba", safe_fetch("SambaNova", fetch_samba_models, loggers["samba"], default=[])),
        lambda: ("scaleway", safe_fetch("Scaleway", fetch_scaleway_models, loggers["scaleway"], default=[], needed_env=("SCALEWAY_API_KEY",))),
        lambda: ("cohere", safe_fetch("Cohere", fetch_cohere_models, loggers["cohere"], default=[], needed_env=("COHERE_API_KEY",))),
        lambda: ("kilo", safe_fetch("Kilo", fetch_kilo_models, loggers["kilo"], default=[])),
        lambda: ("groq", safe_fetch("Groq", fetch_groq_models, loggers["groq"], default=[], needed_env=("GROQ_API_KEY",))),
    ]

    results = {}
    
    # Execute API fetches concurrently
    logger.info("Starting concurrent fetches...")
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        future_to_task = {executor.submit(task): task for task in tasks}
        for future in as_completed(future_to_task):
            try:
                key, data = future.result()
                results[key] = data
            except Exception as exc:
                logger.error(f"Task generated an exception: {exc}")

    # Process gemini models list to pass to template
    gemini_models_data = results.get("gemini", {})
    
    gemini_text_models = [
        {"id": "gemini-3.6-flash", "name": "Gemini 3.6 Flash", "limits": gemini_models_data.get("gemini-3.6-flash", {})},
        {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash", "limits": gemini_models_data.get("gemini-3.5-flash", {})},
        {"id": "gemini-3-flash-preview", "name": "Gemini 3 Flash", "limits": gemini_models_data.get("gemini-3-flash", {})},
        {"id": "gemini-3.5-flash-lite", "name": "Gemini 3.5 Flash-Lite", "limits": gemini_models_data.get("gemini-3.5-flash-lite", {})},
        {"id": "gemini-3.1-flash-lite", "name": "Gemini 3.1 Flash-Lite", "limits": gemini_models_data.get("gemini-3.1-flash-lite", {})},
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "limits": gemini_models_data.get("gemini-2.5-flash", {})},
        {"id": "gemini-2.5-flash-lite", "name": "Gemini 2.5 Flash-Lite", "limits": gemini_models_data.get("gemini-2.5-flash-lite", {})},
        {"id": "gemini-3.1-flash-tts-preview", "name": "Gemini 3.1 Flash TTS", "limits": gemini_models_data.get("gemini-3.1-flash-tts", {})},
        {"id": "gemini-2.5-flash-preview-tts", "name": "Gemini 2.5 Flash TTS", "limits": gemini_models_data.get("gemini-2.5-flash-tts", {})},
        {"id": "gemini-robotics-er-1.6-preview", "name": "Gemini Robotics-ER 1.6", "limits": gemini_models_data.get("gemini-robotics-er-1.6-preview", {})},
        {"id": "gemini-robotics-er-1.5-preview", "name": "Gemini Robotics-ER 1.5", "limits": gemini_models_data.get("gemini-robotics-er-1.5-preview", {})},
        {"id": "gemma-4-31b-it", "name": "Gemma 4 31B Instruct", "limits": gemini_models_data.get("gemma-4-31b", {})},
        {"id": "gemma-4-26b-a4b-it", "name": "Gemma 4 26B A4B Instruct", "limits": gemini_models_data.get("gemma-4-26b", {})},
        {"id": "gemma-3-27b-it", "name": "Gemma 3 27B Instruct", "limits": gemini_models_data.get("gemma-3-27b", {})},
        {"id": "gemma-3-12b-it", "name": "Gemma 3 12B Instruct", "limits": gemini_models_data.get("gemma-3-12b", {})},
        {"id": "gemma-3-4b-it", "name": "Gemma 3 4B Instruct", "limits": gemini_models_data.get("gemma-3-4b", {})},
        {"id": "gemma-3-1b-it", "name": "Gemma 3 1B Instruct", "limits": gemini_models_data.get("gemma-3-1b", {})},
    ]

    if MISSING_MODELS:
        logger.warning("Model tanpa mapping nama di data.py:")
        logger.warning(
            "\n" + "\n".join([f'"{model}": "{model}",' for model in MISSING_MODELS])
        )

    # Set up Jinja environment
    env = Environment(loader=FileSystemLoader(script_dir))
    
    # Expose helper functions to template
    env.globals.update(
        get_human_limits=get_human_limits,
        provider_meta=provider_meta,
    )
    
    template = env.get_template("README_template.md")

    # Render template with variables
    rendered_content = template.render(
        openrouter_models=results.get("openrouter", []),
        gemini_text_models=gemini_text_models,
        kilo_models=results.get("kilo", []),
        groq_models=results.get("groq", []),
        cohere_models=results.get("cohere", []),
        cloudflare_models=results.get("cloudflare", []),
        trial_providers_static=TRIAL_PROVIDERS_STATIC,
        hyperbolic_models=results.get("hyperbolic", []),
        samba_models=results.get("samba", []),
        scaleway_models=results.get("scaleway", []),
    )

    # Add TOC and warnings
    warning = """<!---
PERINGATAN: JANGAN EDIT FILE INI LANGSUNG.
File di-generate oleh src/pull_available_models.py
Ubah src/README_template.md atau skrip generator-nya.
--->
"""
    final_content = warning + rendered_content
    toc_markdown = generate_toc(final_content)
    final_content = final_content.replace("{{TOC}}", toc_markdown)

    with open(os.path.join(script_dir, "..", "README.md"), "w", encoding="utf-8") as f:
        f.write(final_content)
    
    logger.info("README.md berhasil ditulis (bahasa Indonesia / FLA).")

if __name__ == "__main__":
    main()
