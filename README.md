<!--
PERINGATAN: JANGAN EDIT FILE INI LANGSUNG.
File di-generate oleh src/pull_available_models.py
Ubah src/README_template.md atau skrip generator-nya.
-->
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



---

## 🟢 Provider gratis

### [OpenRouter](https://openrouter.ai)


> **Jenis:** 🟢 Gratis
> **Batas:** [20 req/menit<br>50 req/hari<br>sampai ~1.000 req/hari jika pernah top-up $10](https://openrouter.ai/docs/api/reference/limits)
> **Catatan:** Semua model free berbagi kuota yang sama.


**Model gratis:**


- [Cohere North Mini Code](https://openrouter.ai/cohere/north-mini-code:free)

- [Gemma 4 26B A4B Instruct](https://openrouter.ai/google/gemma-4-26b-a4b-it:free)

- [Gemma 4 31B Instruct](https://openrouter.ai/google/gemma-4-31b-it:free)

- [NVIDIA Nemotron 3 Nano 30B A3B](https://openrouter.ai/nvidia/nemotron-3-nano-30b-a3b:free)

- [NVIDIA Nemotron 3 Nano Omni 30B A3B (Reasoning)](https://openrouter.ai/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free)

- [NVIDIA Nemotron 3 Super 120B A12B](https://openrouter.ai/nvidia/nemotron-3-super-120b-a12b:free)

- [NVIDIA Nemotron 3 Ultra 550B A55B](https://openrouter.ai/nvidia/nemotron-3-ultra-550b-a55b:free)

- [NVIDIA Nemotron 3.5 Content Safety](https://openrouter.ai/nvidia/nemotron-3.5-content-safety:free)

- [NVIDIA Nemotron Nano 12B v2 VL](https://openrouter.ai/nvidia/nemotron-nano-12b-v2-vl:free)

- [NVIDIA Nemotron Nano 9B v2](https://openrouter.ai/nvidia/nemotron-nano-9b-v2:free)

- [OpenAI GPT-OSS 20B](https://openrouter.ai/openai/gpt-oss-20b:free)

- [Poolside Laguna S 2.1](https://openrouter.ai/poolside/laguna-s-2.1:free)

- [Poolside Laguna XS 2.1](https://openrouter.ai/poolside/laguna-xs-2.1:free)

- [inclusionai/ling-3.0-tiny:free](https://openrouter.ai/inclusionai/ling-3.0-tiny:free)



### [Google AI Studio](https://aistudio.google.com)

> **Jenis:** 🟢 Gratis
> **Batas:** Beda per model (tabel di bawah)
> **Catatan:** ⚠️ Di luar UK/CH/EEA/EU, data bisa dipakai untuk training.


<table><thead><tr><th>Model</th><th>Batas</th></tr></thead><tbody>

<tr><td>Gemini 3.6 Flash</td><td>250.000 token/menit<br>20 req/hari<br>5 req/menit</td></tr>

<tr><td>Gemini 3.5 Flash</td><td>250.000 token/menit<br>20 req/hari<br>5 req/menit</td></tr>

<tr><td>Gemini 3 Flash</td><td>250.000 token/menit<br>20 req/hari<br>5 req/menit</td></tr>

<tr><td>Gemini 3.5 Flash-Lite</td><td>250.000 token/menit<br>500 req/hari<br>15 req/menit</td></tr>

<tr><td>Gemini 3.1 Flash-Lite</td><td>250.000 token/menit<br>500 req/hari<br>15 req/menit</td></tr>

<tr><td>Gemini 2.5 Flash</td><td>250.000 token/menit<br>20 req/hari<br>5 req/menit</td></tr>

<tr><td>Gemini 2.5 Flash-Lite</td><td>250.000 token/menit<br>20 req/hari<br>10 req/menit</td></tr>

<tr><td>Gemini 3.1 Flash TTS</td><td>10.000 token/menit<br>10 req/hari<br>3 req/menit</td></tr>

<tr><td>Gemini 2.5 Flash TTS</td><td>10.000 token/menit<br>10 req/hari<br>3 req/menit</td></tr>

<tr><td>Gemini Robotics-ER 1.6</td><td>250.000 token/menit<br>20 req/hari<br>5 req/menit</td></tr>

<tr><td>Gemini Robotics-ER 1.5</td><td>250.000 token/menit<br>20 req/hari<br>10 req/menit</td></tr>

<tr><td>Gemma 4 31B Instruct</td><td>16.000 token/menit<br>14.400 req/hari<br>30 req/menit</td></tr>

<tr><td>Gemma 4 26B A4B Instruct</td><td>16.000 token/menit<br>14.400 req/hari<br>30 req/menit</td></tr>

<tr><td>Gemma 3 27B Instruct</td><td>15.000 token/menit<br>14.400 req/hari<br>30 req/menit</td></tr>

<tr><td>Gemma 3 12B Instruct</td><td>15.000 token/menit<br>14.400 req/hari<br>30 req/menit</td></tr>

<tr><td>Gemma 3 4B Instruct</td><td>15.000 token/menit<br>14.400 req/hari<br>30 req/menit</td></tr>

<tr><td>Gemma 3 1B Instruct</td><td>15.000 token/menit<br>14.400 req/hari<br>30 req/menit</td></tr>

</tbody></table>

### [NVIDIA NIM](https://build.nvidia.com/explore/discover)

> **Jenis:** 🟢 Gratis
> **Batas:** 40 req/menit
> **Catatan:** 📱 Wajib verifikasi HP. Context window model sering terbatas.


- [Berbagai model open](https://build.nvidia.com/models)

### [Mistral (La Plateforme)](https://console.mistral.ai/)

> **Jenis:** 🟢 Gratis (plan Experiment)
> **Batas:** Per model dan organisasi — cek [halaman limits](https://admin.mistral.ai/plateforme/limits)
> **Catatan:** 📱 Verifikasi HP. Free tier biasanya butuh setuju data training. Perkiraan akun baru (Juli 2026): 25rb–20jt token/menit dan 0,03–12,5 req/detik tergantung model.


- [Model open dan proprietary Mistral](https://docs.mistral.ai/getting-started/models/models_overview/)

### [Mistral (Codestral)](https://codestral.mistral.ai/)

> **Jenis:** 🟢 Gratis
> **Batas:** 30 req/menit, 2.000 req/hari
> **Catatan:** 📱 Verifikasi HP. Langganan bulanan (tier free).


- Codestral

### [HuggingFace Inference Providers](https://huggingface.co/docs/inference-providers/en/index)

> **Jenis:** 🟢 Gratis (kredit kecil)
> **Batas:** [~$0,10/bulan](https://huggingface.co/docs/inference-providers/en/pricing)
> **Catatan:** Serverless biasanya untuk model di bawah 10GB; beberapa model populer tetap didukung meski lebih besar.


- Berbagai model open di provider yang didukung

### [Vercel AI Gateway](https://vercel.com/docs/ai-gateway)

> **Jenis:** 🟢 Gratis (kredit)
> **Batas:** [~$5/bulan](https://vercel.com/docs/ai-gateway/pricing)
> **Catatan:** Meroute ke banyak provider. Free tier hanya subset katalog, limit per model.



### [Kilo Gateway](https://kilo.ai/docs/gateway)

> **Jenis:** 🟢 Gratis
> **Batas:** [200 req/jam per IP, semua model free berbagi](https://kilo.ai/docs/gateway/usage-and-billing#rate-limiting)
> **Catatan:** ⚠️ Gateway OpenAI-compatible. Model free bisa memakai prompt untuk training. Bisa tanpa akun.



**Model gratis:**


- Cohere North Mini Code

- Kilo Auto Free (Router)

- NVIDIA Nemotron 3 Nano Omni 30B A3B (Reasoning)

- NVIDIA Nemotron 3 Super 120B A12B

- NVIDIA Nemotron 3 Ultra 550B A55B

- NVIDIA Nemotron 3.5 Content Safety

- OpenRouter Free Models (Router)

- Poolside Laguna S 2.1

- Poolside Laguna XS 2.1

- StepFun Step 3.7 Flash

- inclusionai/ling-3.0-tiny:free

- tencent/hy3:free



### [OpenCode Zen](https://opencode.ai/docs/zen/)

> **Jenis:** 🟢 Gratis (sebagian model)
> **Batas:** Lihat situs OpenCode Zen
> **Catatan:** ⚠️ Gateway dengan model kurasi. Data model free bisa dipakai improvement.


**Model free (daftar statis):**

- Big Pickle
- DeepSeek V4 Flash Free
- MiMo-V2.5 Free
- Laguna S 2.1 Free
- Ling-3.0-flash Free
- North Mini Code Free
- Nemotron 3 Ultra Free

### [Cerebras](https://cloud.cerebras.ai/)

> **Jenis:** 🟢 Gratis
> **Batas:** 5 req/menit · 30.000 token/menit · 1.000.000 token/jam · 1.000.000 token/hari
> **Catatan:** Limit ketat; cocok untuk uji coba.


<table><thead><tr><th>Model</th><th>Batas</th></tr></thead><tbody>


<tr><td>gpt-oss-120b</td><td>5 req/menit<br>30.000 token/menit<br>1.000.000 token/jam<br>1.000.000 token/hari</td></tr>

<tr><td>zai-glm-4.7</td><td>5 req/menit<br>30.000 token/menit<br>1.000.000 token/jam<br>1.000.000 token/hari</td></tr>

<tr><td>gemma-4-31b</td><td>5 req/menit<br>30.000 token/menit<br>1.000.000 token/jam<br>1.000.000 token/hari</td></tr>

</tbody></table>

### [Groq](https://console.groq.com)

> **Jenis:** 🟢 Gratis
> **Batas:** Beda per model (tabel)
> **Catatan:** Inference cepat. Limit diukur dari header rate-limit API jika key tersedia saat generate.



<table><thead><tr><th>Model</th><th>Batas</th></tr></thead><tbody>

<tr><td>Allam 2 7B</td><td>7.000 req/hari<br>6.000 token/menit</td></tr>

<tr><td>Llama 3.1 8B</td><td>14.400 req/hari<br>6.000 token/menit</td></tr>

<tr><td>Llama 3.3 70B</td><td>1.000 req/hari<br>12.000 token/menit</td></tr>

<tr><td>Whisper Large v3</td><td>2.000 req/hari</td></tr>

<tr><td>Whisper Large v3 Turbo</td><td>2.000 req/hari</td></tr>

<tr><td>canopylabs/orpheus-arabic-saudi</td><td>—</td></tr>

<tr><td>canopylabs/orpheus-v1-english</td><td>—</td></tr>

<tr><td>groq/compound</td><td>250 req/hari<br>70.000 token/menit</td></tr>

<tr><td>groq/compound-mini</td><td>250 req/hari<br>70.000 token/menit</td></tr>

<tr><td>meta-llama/llama-prompt-guard-2-22m</td><td>—</td></tr>

<tr><td>meta-llama/llama-prompt-guard-2-86m</td><td>—</td></tr>

<tr><td>openai/gpt-oss-120b</td><td>1.000 req/hari<br>8.000 token/menit</td></tr>

<tr><td>openai/gpt-oss-20b</td><td>1.000 req/hari<br>8.000 token/menit</td></tr>

<tr><td>openai/gpt-oss-safeguard-20b</td><td>1.000 req/hari<br>8.000 token/menit</td></tr>

<tr><td>qwen/qwen3.6-27b</td><td>1.000 req/hari<br>8.000 token/menit</td></tr>

</tbody></table>


### [Cohere](https://cohere.com)

> **Jenis:** 🟢 Gratis
> **Batas:** [20 req/menit · 1.000 req/bulan](https://docs.cohere.com/docs/rate-limits)
> **Catatan:** Semua model chat berbagi kuota bulanan.



**Model chat:**


- c4ai-aya-expanse-32b

- c4ai-aya-vision-32b

- command-a-03-2025

- command-a-plus-05-2026

- command-a-reasoning-08-2025

- command-a-translate-08-2025

- command-a-vision-07-2025

- command-r-08-2024

- command-r-plus-08-2024

- command-r7b-12-2024

- command-r7b-arabic-02-2025



### [Cloudflare Workers AI](https://developers.cloudflare.com/workers-ai)

> **Jenis:** 🟢 Gratis
> **Batas:** [10.000 neuron/hari](https://developers.cloudflare.com/workers-ai/platform/pricing/#free-allocation)
> **Catatan:** Fokus text generation di daftar otomatis.



_Daftar model tidak di-fetch (butuh kredensial Cloudflare)._


---

## 🟡 Provider dengan kredit trial


### [Fireworks](https://fireworks.ai/)

> **Jenis:** 🟡 Trial
> **Batas:** $1


**Model:** [Berbagai model open](https://fireworks.ai/models)


### [Baseten](https://app.baseten.co/)

> **Jenis:** 🟡 Trial
> **Batas:** $30


**Model:** [Model yang didukung — bayar per waktu compute](https://www.baseten.co/library/)


### [Nebius](https://tokenfactory.nebius.com/)

> **Jenis:** 🟡 Trial
> **Batas:** $1


**Model:** [Berbagai model open](https://tokenfactory.nebius.com/models)


### [Novita](https://novita.ai/)

> **Jenis:** 🟡 Trial
> **Batas:** $0,5 selama 1 tahun


**Model:** [Berbagai model open](https://novita.ai/models)


### [AI21](https://studio.ai21.com/)

> **Jenis:** 🟡 Trial
> **Batas:** $10 selama 3 bulan


**Model:** Family model Jamba


### [Upstage](https://console.upstage.ai/)

> **Jenis:** 🟡 Trial
> **Batas:** $10 selama 3 bulan


**Model:** Solar Pro/Mini


### [NLP Cloud](https://nlpcloud.com/home)

> **Jenis:** 🟡 Trial
> **Batas:** $15
> **Catatan:** 📱 Verifikasi nomor HP


**Model:** Berbagai model open


### [Alibaba Cloud (International) Model Studio](https://bailian.console.alibabacloud.com/)

> **Jenis:** 🟡 Trial
> **Batas:** 1 juta token/model, berlaku 90 hari (endpoint Singapore)


**Model:** [Model open dan proprietary Qwen](https://www.alibabacloud.com/en/product/modelstudio)


### [Modal](https://modal.com)

> **Jenis:** 🟡 Trial
> **Batas:** $30/bulan di plan Starter


**Model:** Model yang didukung — bayar per waktu compute


### [Inference.net](https://inference.net)

> **Jenis:** 🟡 Trial
> **Batas:** $1, plus $25 jika mengisi survei email


**Model:** Berbagai model open



### [Hyperbolic](https://app.hyperbolic.ai/)


> **Jenis:** 🟡 Trial
> **Batas:** Kredit ~$1


**Model:**


- DeepSeek V3 0324

- Llama 3.3 70B Instruct

- Qwen/Qwen3-Coder-480B-A35B-Instruct

- deepseek-ai/DeepSeek-R1-0528



### [SambaNova Cloud](https://cloud.sambanova.ai/)


> **Jenis:** 🟡 Trial
> **Batas:** Kredit ~$5 selama 3 bulan


**Model:**


- DeepSeek V3.1

- DeepSeek V3.2

- Gemma 4 31B Instruct

- Llama 3.3 70B Instruct

- MiniMax M2.7

- OpenAI GPT-OSS 120B



### [Scaleway Generative APIs](https://console.scaleway.com/generative-api/models)


> **Jenis:** 🟡 Trial
> **Batas:** 1.000.000 token gratis + 60 menit transkripsi audio


**Model:**


- BGE-Multilingual-Gemma2

- Llama 3.3 70B Instruct

- OpenAI GPT-OSS 120B

- Pixtral 12B (2409)

- Whisper Large v3

- gemma-4-26b-a4b-it

- glm-5.2

- mistral-medium-3.5-128b

- mistral-small-3.2-24b-instruct-2506

- qwen3-235b-a22b-instruct-2507

- qwen3-coder-30b-a3b-instruct

- qwen3-embedding-8b

- qwen3.5-397b-a17b

- qwen3.6-35b-a3b



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