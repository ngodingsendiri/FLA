# FLA — Peta API LLM Gratis

**FLA** (*Free LLM API*) adalah katalog provider yang menyediakan **akses API model AI secara gratis** atau **kredit percobaan (trial)**.

> Fork berbahasa Indonesia dari [free-llm-api-resources](https://github.com/cheahjs/free-llm-api-resources) oleh [cheahjs](https://github.com/cheahjs). Daftar model di bagian bawah di-update otomatis lewat skrip.

---

## Cara pakai (cepat)

1. Pilih provider di **[Ringkasan](#ringkasan-provider)** atau loncat ke daftar lengkap.
2. Buka link provider → daftar akun → ambil **API key**.
3. Pakai key itu di app / script kamu (OpenAI-compatible, SDK resmi, dsb.).
4. Hormati **batas kuota** — kalau disalahgunakan, free tier bisa hilang untuk semua orang.

| Simbol | Arti |
|--------|------|
| 🟢 **Gratis** | Kuota free berulang (harian/bulan), tanpa harus isi saldo dulu |
| 🟡 **Trial** | Kredit sekali / terbatas waktu, habis ya bayar |
| 📱 | Sering butuh verifikasi nomor HP |
| ⚠️ | Data chat bisa dipakai training / syarat khusus |

---

## Ringkasan provider

### 🟢 Gratis (free tier)

| Provider | Batas kasar | Catatan |
|----------|-------------|---------|
| [OpenRouter](#openrouter) | ~20 req/menit, 50 req/hari | Model bertanda `:free`, kuota bersama |
| [Google AI Studio](#google-ai-studio) | Per model (lihat tabel) | ⚠️ Data training di luar UK/CH/EEA/EU |
| [NVIDIA NIM](#nvidia-nim) | 40 req/menit | 📱 Verifikasi HP; context window sering kecil |
| [Mistral (La Plateforme)](#mistral-la-plateforme) | Per model / org | 📱 + setuju data training (plan Experiment) |
| [Mistral (Codestral)](#mistral-codestral) | 30 req/menit, 2.000 req/hari | 📱 Khusus model Codestral |
| [HuggingFace](#huggingface-inference-providers) | ~$0,10 kredit/bulan | Banyak model open |
| [Vercel AI Gateway](#vercel-ai-gateway) | ~$5/bulan | Subset katalog, limit per model |
| [Kilo Gateway](#kilo-gateway) | 200 req/jam per IP | ⚠️ Prompt free bisa untuk training; tanpa akun pun bisa |
| [OpenCode Zen](#opencode-zen) | Lihat situs | ⚠️ Data free bisa untuk improvement |
| [Cerebras](#cerebras) | 5 req/menit, 1jt token/hari | Sedikit model, limit ketat |
| [Groq](#groq) | Per model (lihat tabel) | Cepat; cocok coba-coba |
| [Cohere](#cohere) | 20 req/menit, 1.000 req/bulan | Kuota bulanan bersama |
| [Cloudflare Workers AI](#cloudflare-workers-ai) | 10.000 neuron/hari | Banyak model text-gen |

### 🟡 Trial (kredit percobaan)

| Provider | Kredit (perkiraan) | Catatan |
|----------|--------------------|---------|
| [Fireworks](#fireworks) | $1 | Model open |
| [Baseten](#baseten) | $30 | Bayar per compute |
| [Nebius](#nebius) | $1 | Model open |
| [Novita](#novita) | $0,5 / 1 tahun | Model open |
| [AI21](#ai21) | $10 / 3 bulan | Family Jamba |
| [Upstage](#upstage) | $10 / 3 bulan | Solar Pro/Mini |
| [NLP Cloud](#nlp-cloud) | $15 | 📱 Verifikasi HP |
| [Alibaba Cloud Model Studio](#alibaba-cloud-international-model-studio) | 1jt token/model (90 hari) | Endpoint Singapore |
| [Modal](#modal) | $30/bulan (Starter) | Bayar per compute |
| [Inference.net](#inferencenet) | $1 (+$25 survei email) | Model open |
| [Hyperbolic](#hyperbolic) | $1 | Daftar model di bawah |
| [SambaNova Cloud](#sambanova-cloud) | $5 / 3 bulan | Daftar model di bawah |
| [Scaleway](#scaleway-generative-apis) | 1jt token + 60 mnt STT | Daftar model di bawah |

---

{{TOC}}

---

## 🟢 Provider gratis

### [OpenRouter](https://openrouter.ai)

{% if openrouter_models %}
{{ provider_meta(
    "🟢 Gratis",
    "[" ~ get_human_limits(openrouter_models[0]) ~ "<br>sampai ~1.000 req/hari jika pernah top-up $10](https://openrouter.ai/docs/api/reference/limits)",
    "Semua model free berbagi kuota yang sama."
) }}
**Model gratis:**

{% for model in openrouter_models %}
- [{{ model.name }}](https://openrouter.ai/{{ model.id }})
{% endfor %}
{% else %}
{{ provider_meta(
    "🟢 Gratis",
    "Lihat docs OpenRouter",
    "Daftar model gagal di-fetch saat generate terakhir."
) }}
{% endif %}

### [Google AI Studio](https://aistudio.google.com)

{{ provider_meta(
    "🟢 Gratis",
    "Beda per model (tabel di bawah)",
    "⚠️ Di luar UK/CH/EEA/EU, data bisa dipakai untuk training."
) }}
<table><thead><tr><th>Model</th><th>Batas</th></tr></thead><tbody>
{% for model in gemini_text_models %}
<tr><td>{{ model.name }}</td><td>{{ get_human_limits(model) or "—" }}</td></tr>
{% endfor %}
</tbody></table>

### [NVIDIA NIM](https://build.nvidia.com/explore/discover)

{{ provider_meta(
    "🟢 Gratis",
    "40 req/menit",
    "📱 Wajib verifikasi HP. Context window model sering terbatas."
) }}
- [Berbagai model open](https://build.nvidia.com/models)

### [Mistral (La Plateforme)](https://console.mistral.ai/)

{{ provider_meta(
    "🟢 Gratis (plan Experiment)",
    "Per model dan organisasi — cek [halaman limits](https://admin.mistral.ai/plateforme/limits)",
    "📱 Verifikasi HP. Free tier biasanya butuh setuju data training. Perkiraan akun baru (Juli 2026): 25rb–20jt token/menit dan 0,03–12,5 req/detik tergantung model."
) }}
- [Model open dan proprietary Mistral](https://docs.mistral.ai/getting-started/models/models_overview/)

### [Mistral (Codestral)](https://codestral.mistral.ai/)

{{ provider_meta(
    "🟢 Gratis",
    "30 req/menit, 2.000 req/hari",
    "📱 Verifikasi HP. Langganan bulanan (tier free)."
) }}
- Codestral

### [HuggingFace Inference Providers](https://huggingface.co/docs/inference-providers/en/index)

{{ provider_meta(
    "🟢 Gratis (kredit kecil)",
    "[~$0,10/bulan](https://huggingface.co/docs/inference-providers/en/pricing)",
    "Serverless biasanya untuk model di bawah 10GB; beberapa model populer tetap didukung meski lebih besar."
) }}
- Berbagai model open di provider yang didukung

### [Vercel AI Gateway](https://vercel.com/docs/ai-gateway)

{{ provider_meta(
    "🟢 Gratis (kredit)",
    "[~$5/bulan](https://vercel.com/docs/ai-gateway/pricing)",
    "Meroute ke banyak provider. Free tier hanya subset katalog, limit per model."
) }}

### [Kilo Gateway](https://kilo.ai/docs/gateway)

{{ provider_meta(
    "🟢 Gratis",
    "[200 req/jam per IP, semua model free berbagi](https://kilo.ai/docs/gateway/usage-and-billing#rate-limiting)",
    "⚠️ Gateway OpenAI-compatible. Model free bisa memakai prompt untuk training. Bisa tanpa akun."
) }}
{% if kilo_models %}
**Model gratis:**

{% for model in kilo_models %}
- {{ model.name }}
{% endfor %}
{% else %}
_Daftar model tidak tersedia saat generate terakhir._
{% endif %}

### [OpenCode Zen](https://opencode.ai/docs/zen/)

{{ provider_meta(
    "🟢 Gratis (sebagian model)",
    "Lihat situs OpenCode Zen",
    "⚠️ Gateway dengan model kurasi. Data model free bisa dipakai improvement."
) }}
**Model free (daftar statis):**

- Big Pickle
- DeepSeek V4 Flash Free
- MiMo-V2.5 Free
- Laguna S 2.1 Free
- Ling-3.0-flash Free
- North Mini Code Free
- Nemotron 3 Ultra Free

### [Cerebras](https://cloud.cerebras.ai/)

{{ provider_meta(
    "🟢 Gratis",
    "5 req/menit · 30.000 token/menit · 1.000.000 token/jam · 1.000.000 token/hari",
    "Limit ketat; cocok untuk uji coba."
) }}
<table><thead><tr><th>Model</th><th>Batas</th></tr></thead><tbody>
{% set cerebras_limits = "5 req/menit<br>30.000 token/menit<br>1.000.000 token/jam<br>1.000.000 token/hari" %}
{% for name in ["gpt-oss-120b", "zai-glm-4.7", "gemma-4-31b"] %}
<tr><td>{{ name }}</td><td>{{ cerebras_limits }}</td></tr>
{% endfor %}
</tbody></table>

### [Groq](https://console.groq.com)

{{ provider_meta(
    "🟢 Gratis",
    "Beda per model (tabel)",
    "Inference cepat. Limit diukur dari header rate-limit API jika key tersedia saat generate."
) }}
{% if groq_models %}
<table><thead><tr><th>Model</th><th>Batas</th></tr></thead><tbody>
{% for model in groq_models %}
<tr><td>{{ model.name }}</td><td>{{ get_human_limits(model) or "—" }}</td></tr>
{% endfor %}
</tbody></table>
{% else %}
_Daftar model Groq tidak di-fetch (butuh `GROQ_API_KEY`)._
{% endif %}

### [Cohere](https://cohere.com)

{{ provider_meta(
    "🟢 Gratis",
    "[20 req/menit · 1.000 req/bulan](https://docs.cohere.com/docs/rate-limits)",
    "Semua model chat berbagi kuota bulanan."
) }}
{% if cohere_models %}
**Model chat:**

{% for model in cohere_models %}
- {{ model.name }}
{% endfor %}
{% else %}
_Daftar model tidak di-fetch (butuh `COHERE_API_KEY`)._
{% endif %}

### [Cloudflare Workers AI](https://developers.cloudflare.com/workers-ai)

{{ provider_meta(
    "🟢 Gratis",
    "[10.000 neuron/hari](https://developers.cloudflare.com/workers-ai/platform/pricing/#free-allocation)",
    "Fokus text generation di daftar otomatis."
) }}
{% if cloudflare_models %}
**Model:**

{% for model in cloudflare_models %}
- {{ model.name }}
{% endfor %}
{% else %}
_Daftar model tidak di-fetch (butuh kredensial Cloudflare)._
{% endif %}

---

## 🟡 Provider dengan kredit trial

{% for provider in trial_providers_static %}
### [{{ provider.name }}]({{ provider.url }})

{{ provider_meta(
    "🟡 Trial",
    provider.credits,
    provider.requirements if provider.requirements else None
) }}
**Model:** {{ provider.models_desc }}

{% endfor %}

### [Hyperbolic](https://app.hyperbolic.ai/)

{% if hyperbolic_models %}
{{ provider_meta(
    "🟡 Trial",
    "Kredit ~$1",
    None
) }}
**Model:**

{% for model in hyperbolic_models %}
- {{ model.name }}
{% endfor %}
{% else %}
{{ provider_meta(
    "🟡 Trial",
    "Kredit ~$1",
    "Daftar model tidak di-fetch (butuh `HYPERBOLIC_API_KEY`)."
) }}
{% endif %}

### [SambaNova Cloud](https://cloud.sambanova.ai/)

{% if samba_models %}
{{ provider_meta(
    "🟡 Trial",
    "Kredit ~$5 selama 3 bulan",
    None
) }}
**Model:**

{% for model in samba_models %}
- {{ model.name }}
{% endfor %}
{% else %}
{{ provider_meta(
    "🟡 Trial",
    "Kredit ~$5 selama 3 bulan",
    "Daftar model tidak di-fetch."
) }}
{% endif %}

### [Scaleway Generative APIs](https://console.scaleway.com/generative-api/models)

{% if scaleway_models %}
{{ provider_meta(
    "🟡 Trial",
    "1.000.000 token gratis + 60 menit transkripsi audio",
    None
) }}
**Model:**

{% for model in scaleway_models %}
- {{ model.name }}
{% endfor %}
{% else %}
{{ provider_meta(
    "🟡 Trial",
    "1.000.000 token gratis + 60 menit transkripsi audio",
    "Daftar model tidak di-fetch (butuh `SCALEWAY_API_KEY`)."
) }}
{% endif %}

---

## Catatan penting

- **Bukan gateway gelap.** Hanya provider resmi yang punya API sah. Reverse-engineer chatbot (Copilot, Claude web, dll.) **tidak** dimasukkan.
- **Jangan abuse.** Rate limit ada karena alasan; spam bisa bikin free tier dicabut.
- **Limit bisa berubah** kapan saja di sisi provider. Angka di sini perkiraan / hasil cek otomatis terakhir.
- File `README.md` ini **di-generate** oleh `src/pull_available_models.py`. Untuk ubah struktur teks, edit `src/README_template.md` atau skripnya — jangan edit README langsung.

### Kontribusi & regenerate

```bash
cd FLA
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r src/requirements.txt
# Salin .env.example → .env, isi key yang kamu punya
python -u src/pull_available_models.py
```

Provider tanpa API key akan di-skip (tidak bikin skrip mati total).

---

<p align="center">
  <sub>
    FLA · katalog API LLM gratis berbahasa Indonesia<br>
    Berasal dari <a href="https://github.com/cheahjs/free-llm-api-resources">cheahjs/free-llm-api-resources</a>
  </sub>
</p>
