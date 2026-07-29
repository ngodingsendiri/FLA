import json
import os
import requests
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from google.cloud import cloudquotas_v1

from data import HYPERBOLIC_IGNORED_MODELS, LAMBDA_IGNORED_MODELS, OPENROUTER_IGNORED_MODELS
from utils import get_model_name, env_ready

# The directory where the original script is (for finding the 1-second-of-silence.mp3)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

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
                "file": open(os.path.join(SCRIPT_DIR, "1-second-of-silence.mp3"), "rb"),
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
    ret_models = []
    with ThreadPoolExecutor() as executor:
        futures = []
        for model in models:
            future = executor.submit(
                get_groq_limits_for_model, model["id"], SCRIPT_DIR, logger
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
        response = r.json()
        if isinstance(response, dict) and "data" in response:
            models = response["data"]
        else:
            models = response
        
        ret_models = []
        for model in models:
            model_id = model.get("id")
            model_name = model.get("name", model_id)
            if not model_id:
                continue
            ret_models.append({
                "id": model_id,
                "name": model_name,
            })
        ret_models = sorted(ret_models, key=lambda x: x["name"])
        return ret_models
    except Exception as e:
        logger.error(f"Error fetching Kluster models: {e}")
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
    ret_models = []
    for model in models:
        if model["id"] in HYPERBOLIC_IGNORED_MODELS:
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
                    continue
                models[dimension.dimensions.get("model")][
                    f"requests/{quota.refresh_interval}"
                ] = dimension.details.value
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
    ret_models = []
    for model in models:
        if model["id"] in LAMBDA_IGNORED_MODELS:
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
            continue
        endpoints = set(model.get("endpoints") or []) | set(
            model.get("default_endpoints") or []
        )
        if "chat" not in endpoints:
            continue
        ret_models.append(
            {
                "id": model_id,
                "name": get_model_name(model_id),
            }
        )
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

    free_models = []
    for model in models:
        price_info = model.get("current_estimated_price", {})
        if price_info.get("per_million_tokens", {}).get("usd", 1) == 0:
            model_name = model.get("name", "Unknown model")
            free_models.append(
                {
                    "id": model_name,
                    "name": get_model_name(model_name),
                    "description": model.get("tagline", ""),
                }
            )

    return sorted(free_models, key=lambda x: x["name"])


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
    ret_models = sorted(ret_models, key=lambda x: x["name"])
    return ret_models
