# fici-chatbot
Chatbot AI 
# FiCi Chatbot — Dokumentasi Internal

## 📌 Struktur Folder
- `app.py` — backend utama (Flask) untuk chatbot
- `widget.html` — tampilan chatbot untuk disematkan ke LMS Moodle
- `requirements.txt` — daftar dependensi Python (Flask, Gunicorn, OpenAI)
- `/data/responses.json` — basis data rule-based untuk jawaban tetap
- `/data/context_fici.txt` — konteks kursus yang dikirim ke model AI
- `Procfile` — konfigurasi Render deployment

---

## 🤖 Integrasi OpenAI API
- Menggunakan model: `gpt-4o-mini`
- API key disimpan di **Render → Environment** sebagai:
  - `OPENAI_API_KEY = sk-proj-...`

- Inisialisasi di `app.py`:
  ```python
  from openai import OpenAI
  client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

