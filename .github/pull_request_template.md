## Panduan menambah provider (FLA)

Sebelum menambah provider baru, cek dulu:

1. **Perusahaan / layanan resmi?** Bukan akun personal random.
2. **API sah?** Bukan reverse-engineer chatbot (Claude web, Copilot, dll.).
3. **Ada model bisnis yang masuk akal?** (free tier / trial / freemium)
4. **Bukan “model komersial gratis mencurigakan”** (indikasi curi kredit API / reverse eng).

### Cara kontribusi teknis

- Jangan edit `README.md` langsung.
- Ubah `src/README_template.md` (teks/struktur) dan tambahkan skrip API provider baru di `src/fetchers.py`.
- Generate ulang: `python -u src/pull_available_models.py`

### Catatan

Free API rawan abuse. Provider yang masuk list ini kemungkinan kena traffic kasar — siapkan rate limit & ToS yang jelas.
