#!/usr/bin/env python3

from collections import defaultdict
import logging
import json
import requests
import os
from dotenv import load_dotenv
from google.cloud import cloudquotas_v1
from concurrent.futures import ThreadPoolExecutor
import time
import re

from data import (
    MODEL_TO_NAME_MAPPING,
    HYPERBOLIC_IGNORED_MODELS,
    LAMBDA_IGNORED_MODELS,
    OPENROUTER_IGNORED_MODELS,
)


load_dotenv()
script_dir = os.path.dirname(os.path.abspath(__file__))


def create_logger(provider_name):
    logger = logging.getLogger(provider_name)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(f"{provider_name}: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


MISSING_MODELS = set()

# Label limit ke bahasa Indonesia (lebih gampang dibaca)
LIMIT_LABELS_ID = {
    "requests/minute": "req/menit",
    "requests/day": "req/hari",
    "requests/month": "req/bulan",
    "requests/hour": "req/jam",
    "tokens/minute": "token/menit",
    "tokens/day": "token/hari",
    "tokens/hour": "token/jam",
    "audio-seconds/minute": "detik-audio/menit",
}

# Cadangan limit Gemini kalau GCP Quotas tidak tersedia (dari cek publik terakhir)
FALLBACK_GEMINI_LIMITS = {
    "gemini-3.6-flash": {
        "tokens/minute": 250000,
        "requests/day": 20,
        "requests/minute": 5,
    },
    "gemini-3.5-flash": {
        "tokens/minute": 250000,
        "requests/day": 20,
        "requests/minute": 5,
    },
    "gemini-3-flash": {
        "tokens/minute": 250000,
        "requests/day": 20,
        "requests/minute": 5,
    },
    "gemini-3.5-flash-lite": {
        "tokens/minute": 250000,
        "requests/day": 500,
        "requests/minute": 15,
    },
    "gemini-3.1-flash-lite": {
        "tokens/minute": 250000,
        "requests/day": 500,
        "requests/minute": 15,
    },
    "gemini-2.5-flash": {
        "tokens/minute": 250000,
        "requests/day": 20,
        "requests/minute": 5,
    },
    "gemini-2.5-flash-lite": {
        "tokens/minute": 250000,
        "requests/day": 20,
        "requests/minute": 10,
    },
    "gemini-3.1-flash-tts": {
        "tokens/minute": 10000,
        "requests/day": 10,
        "requests/minute": 3,
    },
    "gemini-2.5-flash-tts": {
        "tokens/minute": 10000,
        "requests/day": 10,
        "requests/minute": 3,
    },
    "gemini-robotics-er-1.6-preview": {
        "tokens/minute": 250000,
        "requests/day": 20,
        "requests/minute": 5,
    },
    "gemini-robotics-er-1.5-preview": {
        "tokens/minute": 250000,
        "requests/day": 20,
        "requests/minute": 10,
    },
    "gemma-4-31b": {
        "tokens/minute": 16000,
        "requests/day": 14400,
        "requests/minute": 30,
    },
    "gemma-4-26b": {
        "tokens/minute": 16000,
        "requests/day": 14400,
        "requests/minute": 30,
    },
    "gemma-3-27b": {
        "tokens/minute": 15000,
        "requests/day": 14400,
        "requests/minute": 30,
    },
    "gemma-3-12b": {
        "tokens/minute": 15000,
        "requests/day": 14400,
        "requests/minute": 30,
    },
    "gemma-3-4b": {
        "tokens/minute": 15000,
        "requests/day": 14400,
        "requests/minute": 30,
    },
    "gemma-3-1b": {
        "tokens/minute": 15000,
        "requests/day": 14400,
        "requests/minute": 30,
    },
}


def get_model_name(id):
    id = id.lower()
    if id in MODEL_TO_NAME_MAPPING:
        return MODEL_TO_NAME_MAPPING[id]
    MISSING_MODELS.add(id)
    return id


def env_ready(*keys):
    """True jika semua env key terisi."""
    return all(os.environ.get(k) for k in keys)


def safe_fetch(name, fn, logger, default=None, needed_env=None):
    """Jalankan fetch; kalau gagal / key kosong, return default (jangan crash total)."""
    if default is None:
        default = []
    if needed_env and not env_ready(*needed_env):
        logger.warning(
            f"Lewati {name}: env belum lengkap ({', '.join(needed_env)})"
        )
        return default
    try:
        return fn(logger)
    except Exception as e:
        logger.error(f"Gagal fetch {name}: {e}")
        return default


def get_groq_limits_for_stt_model(model_id, logger):
    logger.info(f"Getting limits for STT model {model_id}...")
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={
                "Authorization": f'Bearer {os.environ["GROQ_API_KEY"]}',
            },
            data={
                "model": model_id,
            },
            files={
                "file": open(os.path.join(script_dir, "1-second-of-silence.mp3"), "rb"),
            },
        )
    except Exception as e:
        logger.error(f"Failed to get limits for model {model_id}: {e}")
        return {}
    try:
        r.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to get limits for model {model_id}: {e}")
        logger.error(r.text)
        return {}
    # try to get audio-seconds/minute from the headers
    audio_seconds_per_minute = r.headers.get("x-ratelimit-limit-audio-seconds")
    if audio_seconds_per_minute:
        audio_seconds_per_minute = int(audio_seconds_per_minute)
    else:
        audio_seconds_per_minute = None
    rpd = r.headers.get("x-ratelimit-limit-requests")
    if rpd:
        rpd = int(rpd)
    else:
        rpd = None
    return {
        "audio-seconds/minute": audio_seconds_per_minute,
        "requests/day": rpd,
    }


def get_groq_limits_for_model(model_id, script_dir, logger):
    if "whisper" in model_id:
        return get_groq_limits_for_stt_model(model_id, logger)
    if "tts" in model_id:
        return None
    logger.info(f"Getting limits for chat model {model_id}...")

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f'Bearer {os.environ["GROQ_API_KEY"]}',
                "Content-Type": "application/json",
            },
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": "Hi!"}],
                "max_tokens": 1,
                "stream": True,
            },
            stream=True,
        )
    except Exception as e:
        logger.error(f"Failed to get limits for model {model_id}: {e}")
        return {}
    try:
        r.raise_for_status()
        rpd = int(r.headers["x-ratelimit-limit-requests"])
        tpm = int(r.headers["x-ratelimit-limit-tokens"])
        return {"requests/day": rpd, "tokens/minute": tpm}
    except Exception as e:
        logger.error(f"Failed to get limits for model {model_id}: {e}")
        logger.error(r.text)
        return {}


def fetch_groq_models(logger):
    logger.info("Fetching Groq models...")
    r = requests.get(
        "https://api.groq.com/openai/v1/models",
        headers={
            "Authorization": f'Bearer {os.environ["GROQ_API_KEY"]}',
            "Content-Type": "application/json",
        },
    )
    r.raise_for_status()
    models = r.json()["data"]
    logger.debug(json.dumps(models, indent=4))
    ret_models = []
    with ThreadPoolExecutor() as executor:
        futures = []
        for model in models:
            future = executor.submit(
                get_groq_limits_for_model, model["id"], script_dir, logger
            )
            futures.append((model, future))

        for model, future in futures:
            limits = future.result()
            if limits is None:
                continue
            ret_models.append(
                {
                    "id": model["id"],
                    "name": get_model_name(model["id"]),
                    "limits": limits,
                }
            )
    ret_models = sorted(ret_models, key=lambda x: x["name"])
    return ret_models


def fetch_kluster_models(logger):
    logger.info("Fetching Kluster models...")
    try:
        r = requests.get(
            "https://api.kluster.ai/v1/models",
            headers={
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        r.raise_for_status()

        # Parse the JSON response
        response = r.json()

        # Based on the paste-2.txt example, the structure should be:
        # {"object":"list","data":[{model1}, {model2}, ...]}
        if isinstance(response, dict) and "data" in response:
            models = response["data"]
        else:
            models = response

        logger.info(f"Fetched {len(models)} models from Kluster")

        ret_models = []
        for model in models:
            # Extract fields from the model object
            model_id = model.get("id")
            model_name = model.get("name", model_id)

            # Skip models without an ID
            if not model_id:
                continue

            ret_models.append(
                {
                    "id": model_id,
                    "name": model_name,  # Use actual name rather than lookup, as these are official names
                }
            )

        logger.debug(json.dumps(ret_models, indent=4))
        ret_models = sorted(ret_models, key=lambda x: x["name"])
        return ret_models

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Kluster models: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from Kluster API: {e}")
        logger.error(f"Response text: {r.text}")
        return []


def fetch_openrouter_models(logger):
    logger.info("Fetching OpenRouter models...")
    r = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={
            "Content-Type": "application/json",
        },
    )
    r.raise_for_status()
    models = r.json()["data"]
    logger.info(f"Fetched {len(models)} models from OpenRouter")
    ret_models = []
    for model in models:
        pricing = float(model.get("pricing", {}).get("completion", "1")) + float(
            model.get("pricing", {}).get("prompt", "1")
        )
        if pricing != 0:
            continue
        if ":free" not in model["id"]:
            continue
        if model["id"].lower() in OPENROUTER_IGNORED_MODELS:
            logger.debug(f"Ignoring model {model['id']}")
            continue
        ret_models.append(
            {
                "id": model["id"],
                "name": get_model_name(model["id"]),
                "limits": {
                    "requests/minute": 20,
                    "requests/day": 50,
                },
            }
        )
    ret_models = sorted(ret_models, key=lambda x: x["name"])
    return ret_models


def fetch_cloudflare_models(logger):
    logger.info("Fetching Cloudflare models...")
    r = requests.get(
        f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/ai/models/search?search=Text+Generation",
        headers={
            "Authorization": f'Bearer {os.environ["CLOUDFLARE_API_KEY"]}',
            "Content-Type": "application/json",
        },
    )
    r.raise_for_status()
    models = r.json()["result"]
    logger.info(f"Fetched {len(models)} models from Cloudflare")
    ret_models = []
    for model in models:
        ret_models.append(
            {
                "id": model["name"],
                "name": get_model_name(model["name"]),
            }
        )
    ret_models = sorted(ret_models, key=lambda x: x["name"])
    return ret_models


def fetch_ovh_models(logger):
    logger.info("Fetching OVH models...")
    r = requests.get(
        "https://endpoints-backend.ai.cloud.ovh.net/rest/v1/models_v2",
        params={"select": "*", "order": "id.desc", "offset": "0", "limit": "100"},
        headers={
            "accept": "*/*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "accept-profile": "public",
            "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzEwNzE2NDAwLAogICJleHAiOiAxODY4NDgyODAwCn0.Jty_eO4oWqLm4Lx_LfbpRW5WESXYXtT2humbBq2Pal8",
            "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzEwNzE2NDAwLAogICJleHAiOiAxODY4NDgyODAwCn0.Jty_eO4oWqLm4Lx_LfbpRW5WESXYXtT2humbBq2Pal8",
            "priority": "u=1, i",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "x-client-info": "supabase-js-web/2.39.7",
        },
    )
    r.raise_for_status()
    models = list(filter(lambda x: x["available"] and "LLM" in x["category"], r.json()))
    logger.info(f"Fetched {len(models)} models from OVH")
    ret_models = []
    for model in models:
        ret_models.append(
            {
                "id": model["name"],
                "name": get_model_name(model["name"]),
                "limits": {
                    "requests/minute": 12,
                },
            }
        )
    ret_models = sorted(ret_models, key=lambda x: x["name"])
    return ret_models


def fetch_hyperbolic_models(logger):
    logger.info("Fetching Hyperbolic models from API...")
    r = requests.get(
        "https://api.hyperbolic.xyz/v1/models",
        headers={
            "accept": "application/json",
            "authorization": f"Bearer {os.environ['HYPERBOLIC_API_KEY']}",
        },
    )
    r.raise_for_status()
    models = r.json()["data"]
    logger.info(f"Fetched {len(models)} models from Hyperbolic's API")
    ret_models = []
    for model in models:
        if model["id"] in HYPERBOLIC_IGNORED_MODELS:
            logger.debug(f"Ignoring model {model['id']}")
            continue
        ret_models.append(
            {
                "id": model["id"],
                "name": get_model_name(model["id"]),
                "limits": {
                    "requests/minute": 60,
                },
            }
        )
    logger.debug(json.dumps(ret_models, indent=4))
    return sorted(ret_models, key=lambda x: x["name"])


def fetch_gemini_limits(logger):
    logger.info("Fetching Gemini limits...")
    client = cloudquotas_v1.CloudQuotasClient()
    request = cloudquotas_v1.ListQuotaInfosRequest(
        parent=f"projects/{os.environ['GCP_PROJECT_ID']}/locations/global/services/generativelanguage.googleapis.com"
    )
    pager = client.list_quota_infos(request=request)
    models = defaultdict(dict)
    for quota in pager:
        if (
            quota.metric
            == "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
        ):
            for dimension in quota.dimensions_infos:
                if dimension.details.value == -1:
                    # -1 means unlimited
                    continue
                models[dimension.dimensions.get("model")][
                    f"tokens/{quota.refresh_interval}"
                ] = dimension.details.value
        elif (
            quota.metric
            == "generativelanguage.googleapis.com/generate_content_free_tier_requests"
        ):
            for dimension in quota.dimensions_infos:
                if dimension.details.value == -1:
                    # -1 means unlimited
                    continue
                models[dimension.dimensions.get("model")][
                    f"requests/{quota.refresh_interval}"
                ] = dimension.details.value
    logger.debug(json.dumps(models, indent=4))
    return models


def fetch_lambda_models(logger):
    logger.info("Fetching Lambda Labs models...")
    r = requests.get(
        "https://api.lambdalabs.com/v1/models",
        headers={
            "Authorization": f"Bearer {os.environ['LAMBDA_API_KEY']}",
        },
    )
    r.raise_for_status()
    models = r.json()["data"]
    logger.info(f"Fetched {len(models)} models from Lambda Labs")
    ret_models = []
    for model in models:
        if model["id"] in LAMBDA_IGNORED_MODELS:
            logger.debug(f"Ignoring model {model['id']}")
            continue
        ret_models.append(
            {
                "id": model["id"],
                "name": get_model_name(model["id"]),
            }
        )
    ret_models = sorted(ret_models, key=lambda x: x["name"])
    return ret_models


def fetch_samba_models(logger):
    logger.info("Fetching SambaNova models...")
    r = requests.get("https://api.sambanova.ai/v1/models")
    r.raise_for_status()
    models = r.json()["data"]
    logger.info(f"Fetched {len(models)} models from SambaNova")
    ret_models = []
    for model in models:
        ret_models.append(
            {
                "id": model["id"],
                "name": get_model_name(model["id"]),
            }
        )
    ret_models = sorted(ret_models, key=lambda x: x["name"])
    return ret_models


def fetch_scaleway_models(logger):
    logger.info("Fetching Scaleway models...")
    r = requests.get(
        "https://api.scaleway.ai/v1/models",
        headers={"Authorization": f"Bearer {os.environ['SCALEWAY_API_KEY']}"},
    )
    r.raise_for_status()
    models = r.json()["data"]
    logger.info(f"Fetched {len(models)} models from Scaleway")
    ret_models = []
    for model in models:
        ret_models.append(
            {
                "id": model["id"],
                "name": get_model_name(model["id"]),
            }
        )
    ret_models = sorted(ret_models, key=lambda x: x["name"])
    return ret_models


def fetch_cohere_models(logger):
    logger.info("Fetching Cohere models...")
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {os.environ['COHERE_API_KEY']}",
    }
    params = {}
    all_models = []
    page = 1

    try:
        while True:
            response = requests.get(
                "https://api.cohere.com/v1/models",
                headers=headers,
                params=params or None,
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            models = payload.get("models", [])
            logger.info(f"Fetched {len(models)} models from Cohere (page {page})")
            all_models.extend(models)
            next_token = payload.get("next_page_token")
            if not next_token:
                break
            params["page_token"] = next_token
            page += 1
    except requests.exceptions.RequestException as exc:
        logger.error(f"Error fetching Cohere models: {exc}")
        return []
    except json.JSONDecodeError as exc:
        logger.error(f"Error decoding Cohere API response: {exc}")
        return []

    ret_models = []
    for model in all_models:
        model_id = model.get("name")
        if not model_id:
            continue
        if model.get("is_deprecated"):
            logger.debug(f"Skipping deprecated Cohere model {model_id}")
            continue
        endpoints = set(model.get("endpoints") or []) | set(
            model.get("default_endpoints") or []
        )
        if "chat" not in endpoints:
            logger.debug(f"Skipping non-chat Cohere model {model_id}")
            continue
        ret_models.append(
            {
                "id": model_id,
                "name": get_model_name(model_id),
            }
        )

    logger.info(f"Found {len(ret_models)} Cohere chat models")
    return sorted(ret_models, key=lambda x: x["name"])


def fetch_chutes_models(logger):
    logger.info("Fetching Chutes models...")
    r = requests.get(
        "https://api.chutes.ai/chutes/?include_public=true&limit=1000",
        headers={
            "Content-Type": "application/json",
        },
    )
    r.raise_for_status()
    models = r.json()["items"]
    logger.info(f"Fetched {len(models)} models from Chutes")

    # Filter for free models based on per_million_token price
    free_models = []
    for model in models:
        price_info = model.get("current_estimated_price", {})
        # Check if per_million_tokens field exists and is set to 0 for USD
        if price_info.get("per_million_tokens", {}).get("usd", 1) == 0:
            model_name = model.get("name", "Unknown model")
            free_models.append(
                {
                    "id": model_name,
                    "name": get_model_name(model_name),
                    "description": model.get("tagline", ""),
                }
            )

    logger.info(f"Found {len(free_models)} free models from Chutes")
    return sorted(free_models, key=lambda x: x["name"])


def get_human_limits(model, seperator="<br>"):
    if "limits" not in model:
        return ""
    limits = model["limits"]
    # filter None values
    limits = {key: value for key, value in limits.items() if value is not None}
    parts = []
    for key, value in limits.items():
        label = LIMIT_LABELS_ID.get(key, key)
        if isinstance(value, (int, float)):
            parts.append(f"{value:,} {label}".replace(",", "."))
        else:
            parts.append(f"{value} {label}")
    return seperator.join(parts)


def provider_meta(jenis="gratis", batas=None, catatan=None):
    """Blok meta singkat di bawah judul provider (tampil konsisten)."""
    lines = [f"> **Jenis:** {jenis}"]
    if batas:
        lines.append(f"> **Batas:** {batas}")
    if catatan:
        lines.append(f"> **Catatan:** {catatan}")
    return "\n".join(lines) + "\n\n"


def fetch_kilo_models(logger):
    logger.info("Fetching Kilo Gateway models...")
    r = requests.get(
        "https://api.kilo.ai/api/gateway/models",
        headers={
            "Content-Type": "application/json",
        },
        timeout=15,
    )
    r.raise_for_status()
    models = r.json()["data"]
    logger.info(f"Fetched {len(models)} models from Kilo Gateway")
    ret_models = []
    for model in models:
        if not model.get("isFree", False):
            continue
        ret_models.append(
            {
                "id": model["id"],
                "name": get_model_name(model["id"]),
            }
        )
    logger.info(f"Found {len(ret_models)} free models from Kilo Gateway")
    ret_models = sorted(ret_models, key=lambda x: x["name"])
    return ret_models


def generate_toc(markdown):
    toc_lines = []
    # Find all ## and ### headings, but skip the main title (# ...)
    headings = re.findall(r"^(#{2,3}) +(.+)", markdown, re.MULTILINE)
    for hashes, title in headings:
        # Remove markdown links for anchor text, keep display text
        display = re.sub(r"\[(.*?)\]\([^)]*\)", r"\1", title)
        # Build anchor (GitHub style)
        anchor = display.lower()
        anchor = re.sub(r"[^a-z0-9 \-_]", "", anchor)
        anchor = anchor.replace(" ", "-")
        anchor = anchor.replace("--", "-")
        anchor = anchor.strip("-")
        indent = "  " if len(hashes) == 3 else ""
        toc_lines.append(f"{indent}- [{display}](#{anchor})")
    return "\n".join(toc_lines)


def main():
    logger = create_logger("Main")
    groq_logger = create_logger("Groq")
    openrouter_logger = create_logger("OpenRouter")
    google_ai_studio_logger = create_logger("Google AI Studio")
    cloudflare_logger = create_logger("Cloudflare")
    hyperbolic_logger = create_logger("Hyperbolic")
    samba_logger = create_logger("SambaNova")
    scaleway_logger = create_logger("Scaleway")
    cohere_logger = create_logger("Cohere")
    kilo_logger = create_logger("Kilo")

    def run_all_fetches():
        g = safe_fetch(
            "Google AI Studio",
            fetch_gemini_limits,
            google_ai_studio_logger,
            default={},
            needed_env=("GCP_PROJECT_ID",),
        )
        if not g:
            google_ai_studio_logger.warning(
                "Pakai FALLBACK_GEMINI_LIMITS (GCP tidak tersedia)"
            )
            g = dict(FALLBACK_GEMINI_LIMITS)
        return {
            "gemini": g,
            "openrouter": safe_fetch(
                "OpenRouter", fetch_openrouter_models, openrouter_logger, default=[]
            ),
            "hyperbolic": safe_fetch(
                "Hyperbolic",
                fetch_hyperbolic_models,
                hyperbolic_logger,
                default=[],
                needed_env=("HYPERBOLIC_API_KEY",),
            ),
            "cloudflare": safe_fetch(
                "Cloudflare",
                fetch_cloudflare_models,
                cloudflare_logger,
                default=[],
                needed_env=("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_KEY"),
            ),
            "samba": safe_fetch(
                "SambaNova", fetch_samba_models, samba_logger, default=[]
            ),
            "scaleway": safe_fetch(
                "Scaleway",
                fetch_scaleway_models,
                scaleway_logger,
                default=[],
                needed_env=("SCALEWAY_API_KEY",),
            ),
            "cohere": safe_fetch(
                "Cohere",
                fetch_cohere_models,
                cohere_logger,
                default=[],
                needed_env=("COHERE_API_KEY",),
            ),
            "kilo": safe_fetch("Kilo", fetch_kilo_models, kilo_logger, default=[]),
            "groq": safe_fetch(
                "Groq",
                fetch_groq_models,
                groq_logger,
                default=[],
                needed_env=("GROQ_API_KEY",),
            ),
        }

    results = run_all_fetches()
    gemini_models = results["gemini"]
    openrouter_models = results["openrouter"]
    hyperbolic_models = results["hyperbolic"]
    cloudflare_models = results["cloudflare"]
    samba_models = results["samba"]
    scaleway_models = results["scaleway"]
    cohere_models = results["cohere"]
    kilo_models = results["kilo"]
    groq_models = results["groq"]

    model_list_markdown = ""

    # --- OpenRouter ---
    model_list_markdown += "### [OpenRouter](https://openrouter.ai)\n\n"
    if openrouter_models:
        provider_limits = get_human_limits(openrouter_models[0])
        model_list_markdown += provider_meta(
            "🟢 Gratis",
            f"[{provider_limits}<br>sampai ~1.000 req/hari jika pernah top-up $10](https://openrouter.ai/docs/api/reference/limits)",
            "Semua model free berbagi kuota yang sama.",
        )
        model_list_markdown += "**Model gratis:**\n\n"
        for model in openrouter_models:
            model_list_markdown += (
                f"- [{model['name']}](https://openrouter.ai/{model['id']})\n"
            )
    else:
        model_list_markdown += provider_meta(
            "🟢 Gratis",
            "Lihat docs OpenRouter",
            "Daftar model gagal di-fetch saat generate terakhir.",
        )
    model_list_markdown += "\n"

    # --- Google AI Studio ---
    model_list_markdown += "### [Google AI Studio](https://aistudio.google.com)\n\n"
    model_list_markdown += provider_meta(
        "🟢 Gratis",
        "Beda per model (tabel di bawah)",
        "⚠️ Di luar UK/CH/EEA/EU, data bisa dipakai untuk training.",
    )
    model_list_markdown += (
        "<table><thead><tr><th>Model</th><th>Batas</th></tr></thead><tbody>\n"
    )

    gemini_text_models = [
        {
            "id": "gemini-3.6-flash",
            "name": "Gemini 3.6 Flash",
            "limits": gemini_models.get("gemini-3.6-flash", {}),
        },
        {
            "id": "gemini-3.5-flash",
            "name": "Gemini 3.5 Flash",
            "limits": gemini_models.get("gemini-3.5-flash", {}),
        },
        {
            "id": "gemini-3-flash-preview",
            "name": "Gemini 3 Flash",
            "limits": gemini_models.get("gemini-3-flash", {}),
        },
        {
            "id": "gemini-3.5-flash-lite",
            "name": "Gemini 3.5 Flash-Lite",
            "limits": gemini_models.get("gemini-3.5-flash-lite", {}),
        },
        {
            "id": "gemini-3.1-flash-lite",
            "name": "Gemini 3.1 Flash-Lite",
            "limits": gemini_models.get("gemini-3.1-flash-lite", {}),
        },
        {
            "id": "gemini-2.5-flash",
            "name": "Gemini 2.5 Flash",
            "limits": gemini_models.get("gemini-2.5-flash", {}),
        },
        {
            "id": "gemini-2.5-flash-lite",
            "name": "Gemini 2.5 Flash-Lite",
            "limits": gemini_models.get("gemini-2.5-flash-lite", {}),
        },
        {
            "id": "gemini-3.1-flash-tts-preview",
            "name": "Gemini 3.1 Flash TTS",
            "limits": gemini_models.get("gemini-3.1-flash-tts", {}),
        },
        {
            "id": "gemini-2.5-flash-preview-tts",
            "name": "Gemini 2.5 Flash TTS",
            "limits": gemini_models.get("gemini-2.5-flash-tts", {}),
        },
        {
            "id": "gemini-robotics-er-1.6-preview",
            "name": "Gemini Robotics-ER 1.6",
            "limits": gemini_models.get("gemini-robotics-er-1.6-preview", {}),
        },
        {
            "id": "gemini-robotics-er-1.5-preview",
            "name": "Gemini Robotics-ER 1.5",
            "limits": gemini_models.get("gemini-robotics-er-1.5-preview", {}),
        },
        {
            "id": "gemma-4-31b-it",
            "name": "Gemma 4 31B Instruct",
            "limits": gemini_models.get("gemma-4-31b", {}),
        },
        {
            "id": "gemma-4-26b-a4b-it",
            "name": "Gemma 4 26B A4B Instruct",
            "limits": gemini_models.get("gemma-4-26b", {}),
        },
        {
            "id": "gemma-3-27b-it",
            "name": "Gemma 3 27B Instruct",
            "limits": gemini_models.get("gemma-3-27b", {}),
        },
        {
            "id": "gemma-3-12b-it",
            "name": "Gemma 3 12B Instruct",
            "limits": gemini_models.get("gemma-3-12b", {}),
        },
        {
            "id": "gemma-3-4b-it",
            "name": "Gemma 3 4B Instruct",
            "limits": gemini_models.get("gemma-3-4b", {}),
        },
        {
            "id": "gemma-3-1b-it",
            "name": "Gemma 3 1B Instruct",
            "limits": gemini_models.get("gemma-3-1b", {}),
        },
    ]

    for model in gemini_text_models:
        limits_str = get_human_limits(model) or "—"
        model_list_markdown += (
            f"<tr><td>{model['name']}</td><td>{limits_str}</td></tr>\n"
        )

    model_list_markdown += "</tbody></table>\n\n"

    # --- NVIDIA NIM ---
    model_list_markdown += (
        "### [NVIDIA NIM](https://build.nvidia.com/explore/discover)\n\n"
    )
    model_list_markdown += provider_meta(
        "🟢 Gratis",
        "40 req/menit",
        "📱 Wajib verifikasi HP. Context window model sering terbatas.",
    )
    model_list_markdown += "- [Berbagai model open](https://build.nvidia.com/models)\n\n"

    # --- Mistral ---
    model_list_markdown += (
        "### [Mistral (La Plateforme)](https://console.mistral.ai/)\n\n"
    )
    model_list_markdown += provider_meta(
        "🟢 Gratis (plan Experiment)",
        "Per model dan organisasi — cek [halaman limits](https://admin.mistral.ai/plateforme/limits)",
        "📱 Verifikasi HP. Free tier biasanya butuh setuju data training. Perkiraan akun baru (Juli 2026): 25rb–20jt token/menit dan 0,03–12,5 req/detik tergantung model.",
    )
    model_list_markdown += "- [Model open dan proprietary Mistral](https://docs.mistral.ai/getting-started/models/models_overview/)\n\n"

    model_list_markdown += (
        "### [Mistral (Codestral)](https://codestral.mistral.ai/)\n\n"
    )
    model_list_markdown += provider_meta(
        "🟢 Gratis",
        "30 req/menit, 2.000 req/hari",
        "📱 Verifikasi HP. Langganan bulanan (tier free).",
    )
    model_list_markdown += "- Codestral\n\n"

    # --- HF ---
    model_list_markdown += "### [HuggingFace Inference Providers](https://huggingface.co/docs/inference-providers/en/index)\n\n"
    model_list_markdown += provider_meta(
        "🟢 Gratis (kredit kecil)",
        "[~$0,10/bulan](https://huggingface.co/docs/inference-providers/en/pricing)",
        "Serverless biasanya untuk model di bawah 10GB; beberapa model populer tetap didukung meski lebih besar.",
    )
    model_list_markdown += "- Berbagai model open di provider yang didukung\n\n"

    # --- Vercel ---
    model_list_markdown += "### [Vercel AI Gateway](https://vercel.com/docs/ai-gateway)\n\n"
    model_list_markdown += provider_meta(
        "🟢 Gratis (kredit)",
        "[~$5/bulan](https://vercel.com/docs/ai-gateway/pricing)",
        "Meroute ke banyak provider. Free tier hanya subset katalog, limit per model.",
    )

    # --- Kilo ---
    model_list_markdown += "### [Kilo Gateway](https://kilo.ai/docs/gateway)\n\n"
    model_list_markdown += provider_meta(
        "🟢 Gratis",
        "[200 req/jam per IP, semua model free berbagi](https://kilo.ai/docs/gateway/usage-and-billing#rate-limiting)",
        "⚠️ Gateway OpenAI-compatible. Model free bisa memakai prompt untuk training. Bisa tanpa akun.",
    )
    if kilo_models:
        model_list_markdown += "**Model gratis:**\n\n"
        for model in kilo_models:
            model_list_markdown += f"- {model['name']}\n"
    else:
        model_list_markdown += "_Daftar model tidak tersedia saat generate terakhir._\n"
    model_list_markdown += "\n"

    # --- OpenCode Zen ---
    model_list_markdown += "### [OpenCode Zen](https://opencode.ai/docs/zen/)\n\n"
    model_list_markdown += provider_meta(
        "🟢 Gratis (sebagian model)",
        "Lihat situs OpenCode Zen",
        "⚠️ Gateway dengan model kurasi. Data model free bisa dipakai improvement.",
    )
    model_list_markdown += "**Model free (daftar statis):**\n\n"
    for name in (
        "Big Pickle",
        "DeepSeek V4 Flash Free",
        "MiMo-V2.5 Free",
        "Laguna S 2.1 Free",
        "Ling-3.0-flash Free",
        "North Mini Code Free",
        "Nemotron 3 Ultra Free",
    ):
        model_list_markdown += f"- {name}\n"
    model_list_markdown += "\n"

    # --- Cerebras ---
    model_list_markdown += "### [Cerebras](https://cloud.cerebras.ai/)\n\n"
    model_list_markdown += provider_meta(
        "🟢 Gratis",
        "5 req/menit · 30.000 token/menit · 1.000.000 token/jam · 1.000.000 token/hari",
        "Limit ketat; cocok untuk uji coba.",
    )
    model_list_markdown += (
        "<table><thead><tr><th>Model</th><th>Batas</th></tr></thead><tbody>\n"
    )
    cerebras_free_limits = (
        "5 req/menit<br>30.000 token/menit<br>1.000.000 token/jam<br>1.000.000 token/hari"
    )
    for name in ("gpt-oss-120b", "zai-glm-4.7", "gemma-4-31b"):
        model_list_markdown += (
            f"<tr><td>{name}</td><td>{cerebras_free_limits}</td></tr>\n"
        )
    model_list_markdown += "</tbody></table>\n\n"

    # --- Groq ---
    model_list_markdown += "### [Groq](https://console.groq.com)\n\n"
    model_list_markdown += provider_meta(
        "🟢 Gratis",
        "Beda per model (tabel)",
        "Inference cepat. Limit diukur dari header rate-limit API jika key tersedia saat generate.",
    )
    if groq_models:
        model_list_markdown += (
            "<table><thead><tr><th>Model</th><th>Batas</th></tr></thead><tbody>\n"
        )
        for model in groq_models:
            limits_str = get_human_limits(model) or "—"
            model_list_markdown += (
                f"<tr><td>{model['name']}</td><td>{limits_str}</td></tr>\n"
            )
        model_list_markdown += "</tbody></table>\n"
    else:
        model_list_markdown += (
            "_Daftar model Groq tidak di-fetch (butuh `GROQ_API_KEY`)._\n"
        )
    model_list_markdown += "\n"

    # --- Cohere ---
    model_list_markdown += "### [Cohere](https://cohere.com)\n\n"
    model_list_markdown += provider_meta(
        "🟢 Gratis",
        "[20 req/menit · 1.000 req/bulan](https://docs.cohere.com/docs/rate-limits)",
        "Semua model chat berbagi kuota bulanan.",
    )
    if cohere_models:
        model_list_markdown += "**Model chat:**\n\n"
        for model in cohere_models:
            model_list_markdown += f"- {model['name']}\n"
    else:
        model_list_markdown += (
            "_Daftar model tidak di-fetch (butuh `COHERE_API_KEY`)._\n"
        )
    model_list_markdown += "\n"

    # --- Cloudflare ---
    model_list_markdown += (
        "### [Cloudflare Workers AI](https://developers.cloudflare.com/workers-ai)\n\n"
    )
    model_list_markdown += provider_meta(
        "🟢 Gratis",
        "[10.000 neuron/hari](https://developers.cloudflare.com/workers-ai/platform/pricing/#free-allocation)",
        "Fokus text generation di daftar otomatis.",
    )
    if cloudflare_models:
        model_list_markdown += "**Model:**\n\n"
        for model in cloudflare_models:
            model_list_markdown += f"- {model['name']}\n"
    else:
        model_list_markdown += (
            "_Daftar model tidak di-fetch (butuh kredensial Cloudflare)._\n"
        )
    model_list_markdown += "\n"

    # ---------- Trial ----------
    trial_list_markdown = ""
    trial_providers_static = [
        {
            "name": "Fireworks",
            "url": "https://fireworks.ai/",
            "credits": "$1",
            "requirements": "",
            "models_desc": "[Berbagai model open](https://fireworks.ai/models)",
        },
        {
            "name": "Baseten",
            "url": "https://app.baseten.co/",
            "credits": "$30",
            "requirements": "",
            "models_desc": "[Model yang didukung — bayar per waktu compute](https://www.baseten.co/library/)",
        },
        {
            "name": "Nebius",
            "url": "https://tokenfactory.nebius.com/",
            "credits": "$1",
            "requirements": "",
            "models_desc": "[Berbagai model open](https://tokenfactory.nebius.com/models)",
        },
        {
            "name": "Novita",
            "url": "https://novita.ai/",
            "credits": "$0,5 selama 1 tahun",
            "requirements": "",
            "models_desc": "[Berbagai model open](https://novita.ai/models)",
        },
        {
            "name": "AI21",
            "url": "https://studio.ai21.com/",
            "credits": "$10 selama 3 bulan",
            "requirements": "",
            "models_desc": "Family model Jamba",
        },
        {
            "name": "Upstage",
            "url": "https://console.upstage.ai/",
            "credits": "$10 selama 3 bulan",
            "requirements": "",
            "models_desc": "Solar Pro/Mini",
        },
        {
            "name": "NLP Cloud",
            "url": "https://nlpcloud.com/home",
            "credits": "$15",
            "requirements": "📱 Verifikasi nomor HP",
            "models_desc": "Berbagai model open",
        },
        {
            "name": "Alibaba Cloud (International) Model Studio",
            "url": "https://bailian.console.alibabacloud.com/",
            "credits": "1 juta token/model, berlaku 90 hari (endpoint Singapore)",
            "requirements": "",
            "models_desc": "[Model open dan proprietary Qwen](https://www.alibabacloud.com/en/product/modelstudio)",
        },
        {
            "name": "Modal",
            "url": "https://modal.com",
            "credits": "$30/bulan di plan Starter",
            "requirements": "",
            "models_desc": "Model yang didukung — bayar per waktu compute",
        },
        {
            "name": "Inference.net",
            "url": "https://inference.net",
            "credits": "$1, plus $25 jika mengisi survei email",
            "requirements": "",
            "models_desc": "Berbagai model open",
        },
    ]

    for provider in trial_providers_static:
        trial_list_markdown += f"### [{provider['name']}]({provider['url']})\n\n"
        trial_list_markdown += provider_meta(
            "🟡 Trial",
            provider["credits"],
            provider["requirements"] or None,
        )
        trial_list_markdown += f"**Model:** {provider['models_desc']}\n\n"

    if hyperbolic_models:
        trial_list_markdown += "### [Hyperbolic](https://app.hyperbolic.ai/)\n\n"
        trial_list_markdown += provider_meta("🟡 Trial", "Kredit ~$1", None)
        trial_list_markdown += "**Model:**\n\n"
        for model in hyperbolic_models:
            trial_list_markdown += f"- {model['name']}\n"
        trial_list_markdown += "\n"
    else:
        trial_list_markdown += "### [Hyperbolic](https://app.hyperbolic.ai/)\n\n"
        trial_list_markdown += provider_meta(
            "🟡 Trial",
            "Kredit ~$1",
            "Daftar model tidak di-fetch (butuh `HYPERBOLIC_API_KEY`).",
        )

    if samba_models:
        trial_list_markdown += "### [SambaNova Cloud](https://cloud.sambanova.ai/)\n\n"
        trial_list_markdown += provider_meta(
            "🟡 Trial", "Kredit ~$5 selama 3 bulan", None
        )
        trial_list_markdown += "**Model:**\n\n"
        for model in samba_models:
            trial_list_markdown += f"- {model['name']}\n"
        trial_list_markdown += "\n"

    if scaleway_models:
        trial_list_markdown += "### [Scaleway Generative APIs](https://console.scaleway.com/generative-api/models)\n\n"
        trial_list_markdown += provider_meta(
            "🟡 Trial",
            "1.000.000 token gratis + 60 menit transkripsi audio",
            None,
        )
        trial_list_markdown += "**Model:**\n\n"
        for model in scaleway_models:
            trial_list_markdown += f"- {model['name']}\n"
        trial_list_markdown += "\n"
    else:
        trial_list_markdown += "### [Scaleway Generative APIs](https://console.scaleway.com/generative-api/models)\n\n"
        trial_list_markdown += provider_meta(
            "🟡 Trial",
            "1.000.000 token gratis + 60 menit transkripsi audio",
            "Daftar model tidak di-fetch (butuh `SCALEWAY_API_KEY`).",
        )

    if MISSING_MODELS:
        logger.warning("Model tanpa mapping nama di data.py:")
        logger.warning(
            "\n" + "\n".join([f'"{model}": "{model}",' for model in MISSING_MODELS])
        )

    with open(
        os.path.join(script_dir, "README_template.md"), "r", encoding="utf-8"
    ) as f:
        readme = f.read()
    warning = """<!---
PERINGATAN: JANGAN EDIT FILE INI LANGSUNG.
File di-generate oleh src/pull_available_models.py
Ubah src/README_template.md atau skrip generator-nya.
--->
"""
    initial_templated = (
        (warning + readme)
        .replace("{{MODEL_LIST}}", model_list_markdown)
        .replace("{{TRIAL_LIST_MARKDOWN}}", trial_list_markdown)
    )
    toc_markdown = generate_toc(initial_templated)
    with open(
        os.path.join(script_dir, "..", "README.md"), "w", encoding="utf-8"
    ) as f:
        f.write(initial_templated.replace("{{TOC}}", toc_markdown))
    logger.info("README.md berhasil ditulis (bahasa Indonesia / FLA).")


if __name__ == "__main__":
    main()
