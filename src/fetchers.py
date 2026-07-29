import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from google.cloud import cloudquotas_v1

from data import HYPERBOLIC_IGNORED_MODELS, OPENROUTER_IGNORED_MODELS
from utils import env_ready, get_model_name, get_session

# ── HTTP session (shared, with auto-retry) ─────────────────────────────────
session = get_session()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Generic safe wrapper ───────────────────────────────────────────────────
def safe_fetch(
    name: str,
    fn,
    logger,
    default=None,
    needed_env: tuple[str, ...] | None = None,
):
    """Jalankan fetch; kalau gagal / key kosong, return default (jangan crash total)."""
    if default is None:
        default = []
    if needed_env and not env_ready(*needed_env):
        logger.warning(f"Lewati {name}: env belum lengkap ({', '.join(needed_env)})")
        return default
    try:
        return fn(logger)
    except Exception as e:
        logger.exception(f"Gagal fetch {name}: {e}")
        return default


# ── Groq ───────────────────────────────────────────────────────────────────
def get_groq_limits_for_stt_model(model_id: str, logger) -> dict:
    logger.info(f"Getting limits for STT model {model_id}...")
    try:
        with open(os.path.join(SCRIPT_DIR, "1-second-of-silence.mp3"), "rb") as f:
            r = session.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f'Bearer {os.environ["GROQ_API_KEY"]}'},
                data={"model": model_id},
                files={"file": f},
                timeout=15,
            )
    except Exception as e:
        logger.error(f"Failed to get limits for model {model_id}: {e}")
        return {}
    try:
        r.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to get limits for model {model_id}: {e}\n{r.text}")
        return {}
    audio_spm = r.headers.get("x-ratelimit-limit-audio-seconds")
    rpd = r.headers.get("x-ratelimit-limit-requests")
    return {
        "audio-seconds/minute": int(audio_spm) if audio_spm else None,
        "requests/day": int(rpd) if rpd else None,
    }


def get_groq_limits_for_model(model_id: str, script_dir: str, logger) -> dict | None:
    if "whisper" in model_id:
        return get_groq_limits_for_stt_model(model_id, logger)
    if "tts" in model_id:
        return None
    logger.info(f"Getting limits for chat model {model_id}...")
    try:
        r = session.post(
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
            timeout=15,
        )
    except Exception as e:
        logger.error(f"Failed to get limits for model {model_id}: {e}")
        return {}
    try:
        r.raise_for_status()
        return {
            "requests/day": int(r.headers["x-ratelimit-limit-requests"]),
            "tokens/minute": int(r.headers["x-ratelimit-limit-tokens"]),
        }
    except Exception as e:
        logger.error(f"Failed to get limits for model {model_id}: {e}\n{r.text}")
        return {}


def fetch_groq_models(logger) -> list[dict]:
    logger.info("Fetching Groq models...")
    r = session.get(
        "https://api.groq.com/openai/v1/models",
        headers={
            "Authorization": f'Bearer {os.environ["GROQ_API_KEY"]}',
            "Content-Type": "application/json",
        },
        timeout=15,
    )
    r.raise_for_status()
    models = r.json()["data"]
    ret_models: list[dict] = []
    with ThreadPoolExecutor() as executor:
        futures = [
            (model, executor.submit(get_groq_limits_for_model, model["id"], SCRIPT_DIR, logger))
            for model in models
        ]
        for model, future in futures:
            limits = future.result()
            if limits is None:
                continue
            ret_models.append({"id": model["id"], "name": get_model_name(model["id"]), "limits": limits})
    return sorted(ret_models, key=lambda x: x["name"])


# ── OpenRouter ─────────────────────────────────────────────────────────────
def fetch_openrouter_models(logger) -> list[dict]:
    logger.info("Fetching OpenRouter models...")
    r = session.get(
        "https://openrouter.ai/api/v1/models",
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    r.raise_for_status()
    ret_models: list[dict] = []
    for model in r.json()["data"]:
        pricing = float(model.get("pricing", {}).get("completion", "1")) + float(
            model.get("pricing", {}).get("prompt", "1")
        )
        if pricing != 0 or ":free" not in model["id"]:
            continue
        if model["id"].lower() in OPENROUTER_IGNORED_MODELS:
            continue
        ret_models.append({
            "id": model["id"],
            "name": get_model_name(model["id"]),
            "limits": {"requests/minute": 20, "requests/day": 50},
        })
    return sorted(ret_models, key=lambda x: x["name"])


# ── Cloudflare ─────────────────────────────────────────────────────────────
def fetch_cloudflare_models(logger) -> list[dict]:
    logger.info("Fetching Cloudflare models...")
    r = session.get(
        f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/ai/models/search?search=Text+Generation",
        headers={
            "Authorization": f'Bearer {os.environ["CLOUDFLARE_API_KEY"]}',
            "Content-Type": "application/json",
        },
        timeout=15,
    )
    r.raise_for_status()
    return sorted(
        [{"id": m["name"], "name": get_model_name(m["name"])} for m in r.json()["result"]],
        key=lambda x: x["name"],
    )


# ── Hyperbolic ─────────────────────────────────────────────────────────────
def fetch_hyperbolic_models(logger) -> list[dict]:
    logger.info("Fetching Hyperbolic models from API...")
    r = session.get(
        "https://api.hyperbolic.xyz/v1/models",
        headers={
            "accept": "application/json",
            "authorization": f"Bearer {os.environ['HYPERBOLIC_API_KEY']}",
        },
        timeout=15,
    )
    r.raise_for_status()
    return sorted(
        [
            {"id": m["id"], "name": get_model_name(m["id"]), "limits": {"requests/minute": 60}}
            for m in r.json()["data"]
            if m["id"] not in HYPERBOLIC_IGNORED_MODELS
        ],
        key=lambda x: x["name"],
    )


# ── Gemini (GCP Quotas) ────────────────────────────────────────────────────
def fetch_gemini_limits(logger) -> dict:
    logger.info("Fetching Gemini limits...")
    client = cloudquotas_v1.CloudQuotasClient()
    request = cloudquotas_v1.ListQuotaInfosRequest(
        parent=f"projects/{os.environ['GCP_PROJECT_ID']}/locations/global/services/generativelanguage.googleapis.com"
    )
    models: dict = defaultdict(dict)
    for quota in client.list_quota_infos(request=request):
        if quota.metric == "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count":
            for dim in quota.dimensions_infos:
                if dim.details.value != -1:
                    models[dim.dimensions.get("model")][f"tokens/{quota.refresh_interval}"] = dim.details.value
        elif quota.metric == "generativelanguage.googleapis.com/generate_content_free_tier_requests":
            for dim in quota.dimensions_infos:
                if dim.details.value != -1:
                    models[dim.dimensions.get("model")][f"requests/{quota.refresh_interval}"] = dim.details.value
    return models


# ── SambaNova ──────────────────────────────────────────────────────────────
def fetch_samba_models(logger) -> list[dict]:
    logger.info("Fetching SambaNova models...")
    r = session.get("https://api.sambanova.ai/v1/models", timeout=15)
    r.raise_for_status()
    return sorted(
        [{"id": m["id"], "name": get_model_name(m["id"])} for m in r.json()["data"]],
        key=lambda x: x["name"],
    )


# ── Scaleway ───────────────────────────────────────────────────────────────
def fetch_scaleway_models(logger) -> list[dict]:
    logger.info("Fetching Scaleway models...")
    r = session.get(
        "https://api.scaleway.ai/v1/models",
        headers={"Authorization": f"Bearer {os.environ['SCALEWAY_API_KEY']}"},
        timeout=15,
    )
    r.raise_for_status()
    return sorted(
        [{"id": m["id"], "name": get_model_name(m["id"])} for m in r.json()["data"]],
        key=lambda x: x["name"],
    )


# ── Cohere ─────────────────────────────────────────────────────────────────
def fetch_cohere_models(logger) -> list[dict]:
    logger.info("Fetching Cohere models...")
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {os.environ['COHERE_API_KEY']}",
    }
    params: dict = {}
    all_models: list[dict] = []
    try:
        while True:
            response = session.get(
                "https://api.cohere.com/v1/models",
                headers=headers,
                params=params or None,
                timeout=15,
            )
            response.raise_for_status()
            payload = response.json()
            all_models.extend(payload.get("models", []))
            next_token = payload.get("next_page_token")
            if not next_token:
                break
            params["page_token"] = next_token
    except Exception as exc:
        logger.exception(f"Error fetching Cohere models: {exc}")
        return []

    return sorted(
        [
            {"id": m["name"], "name": get_model_name(m["name"])}
            for m in all_models
            if m.get("name")
            and not m.get("is_deprecated")
            and "chat" in (set(m.get("endpoints") or []) | set(m.get("default_endpoints") or []))
        ],
        key=lambda x: x["name"],
    )


# ── Kilo ───────────────────────────────────────────────────────────────────
def fetch_kilo_models(logger) -> list[dict]:
    logger.info("Fetching Kilo Gateway models...")
    r = session.get(
        "https://api.kilo.ai/api/gateway/models",
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    r.raise_for_status()
    return sorted(
        [
            {"id": m["id"], "name": get_model_name(m["id"])}
            for m in r.json()["data"]
            if m.get("isFree", False)
        ],
        key=lambda x: x["name"],
    )
