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

{{MODEL_LIST}}

---

## 🟡 Provider dengan kredit trial

{{TRIAL_LIST_MARKDOWN}}

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
