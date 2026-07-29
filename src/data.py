"""
Konstanta dan data statis proyek FLA.

Catatan: MODEL_TO_NAME_MAPPING telah dipindah ke config/models.yaml
dan dimuat secara otomatis oleh src/utils.py.
"""

HYPERBOLIC_IGNORED_MODELS: set[str] = {
    "Wifhat",
    "FLUX.1-dev",
    "StableDiffusion",
    "Monad",
    "TTS",
    "deepseek-ai/Janus-Pro-7B",
    "test",
    "SDXL1.0-base",
    # Tidak tersedia di free tier
    "deepseek-ai/DeepSeek-R1",
    "deepseek-ai/DeepSeek-R1-Zero",
}

OPENROUTER_IGNORED_MODELS: set[str] = {
    # Model Gemini experimental — rate limit terlalu ketat untuk dipakai
    "google/gemini-exp-1121:free",
    "google/learnlm-1.5-pro-experimental:free",
    "google/gemini-exp-1114:free",
    "google/gemini-exp-1206:free",
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-2.0-flash-thinking-exp:free",
    "google/gemini-2.0-flash-thinking-exp-1219:free",
    "google/gemini-flash-1.5-exp:free",
    "google/gemini-2.0-pro-exp-02-05:free",
}

# Cadangan limit Gemini kalau GCP Quotas tidak tersedia (dari cek publik terakhir)
FALLBACK_GEMINI_LIMITS: dict[str, dict[str, int]] = {
    "gemini-3.6-flash": {"tokens/minute": 250000, "requests/day": 20, "requests/minute": 5},
    "gemini-3.5-flash": {"tokens/minute": 250000, "requests/day": 20, "requests/minute": 5},
    "gemini-3-flash": {"tokens/minute": 250000, "requests/day": 20, "requests/minute": 5},
    "gemini-3.5-flash-lite": {"tokens/minute": 250000, "requests/day": 500, "requests/minute": 15},
    "gemini-3.1-flash-lite": {"tokens/minute": 250000, "requests/day": 500, "requests/minute": 15},
    "gemini-2.5-flash": {"tokens/minute": 250000, "requests/day": 20, "requests/minute": 5},
    "gemini-2.5-flash-lite": {"tokens/minute": 250000, "requests/day": 20, "requests/minute": 10},
    "gemini-3.1-flash-tts": {"tokens/minute": 10000, "requests/day": 10, "requests/minute": 3},
    "gemini-2.5-flash-tts": {"tokens/minute": 10000, "requests/day": 10, "requests/minute": 3},
    "gemini-robotics-er-1.6-preview": {"tokens/minute": 250000, "requests/day": 20, "requests/minute": 5},
    "gemini-robotics-er-1.5-preview": {"tokens/minute": 250000, "requests/day": 20, "requests/minute": 10},
    "gemma-4-31b": {"tokens/minute": 16000, "requests/day": 14400, "requests/minute": 30},
    "gemma-4-26b": {"tokens/minute": 16000, "requests/day": 14400, "requests/minute": 30},
    "gemma-3-27b": {"tokens/minute": 15000, "requests/day": 14400, "requests/minute": 30},
    "gemma-3-12b": {"tokens/minute": 15000, "requests/day": 14400, "requests/minute": 30},
    "gemma-3-4b": {"tokens/minute": 15000, "requests/day": 14400, "requests/minute": 30},
    "gemma-3-1b": {"tokens/minute": 15000, "requests/day": 14400, "requests/minute": 30},
}

TRIAL_PROVIDERS_STATIC: list[dict[str, str]] = [
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
