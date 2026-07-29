import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from google.cloud import cloudquotas_v1

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



# ── Artificial Analysis (Intelligence Scores) ──────────────────────────────
def fetch_intelligence_scores(logger) -> dict[str, float]:
    """
    Mengambil skor Intelligence Index dari Artificial Analysis API.
    Return: dict {model_name_lower: intelligence_score}
    API key diambil dari env var ARTIFICIAL_ANALYSIS_API_KEY.
    """
    api_key = os.environ.get("ARTIFICIAL_ANALYSIS_API_KEY", "")
    if not api_key:
        logger.warning("Lewati Artificial Analysis: env belum lengkap (ARTIFICIAL_ANALYSIS_API_KEY)")
        return {}

    logger.info("Fetching Intelligence scores dari Artificial Analysis...")
    try:
        r = session.get(
            "https://artificialanalysis.ai/api/v2/language/models",
            headers={"x-api-key": api_key},
            timeout=20,
        )
        r.raise_for_status()
        scores: dict[str, float] = {}
        for model in r.json().get("data", []):
            name = model.get("name", "")
            score = model.get("intelligence", {})
            if isinstance(score, dict):
                score = score.get("score") or score.get("value") or score.get("index")
            if name and score is not None:
                try:
                    scores[name.lower()] = float(score)
                except (TypeError, ValueError):
                    pass
        logger.info(f"Artificial Analysis: {len(scores)} skor berhasil dimuat.")
        return scores
    except Exception as exc:
        logger.exception(f"Gagal fetch Artificial Analysis: {exc}")
        return {}
