Tentu! 📘
Berikut ini adalah isi `README.md` yang siap salin-tempel untuk dokumentasi internal proyek chatbot FiCi Anda:

---

```markdown
# 🤖 FiCi Chatbot

FiCi Chatbot adalah chatbot pembelajaran yang terintegrasi dengan LMS (Moodle) untuk mendukung proyek **FiCi Academy — Literasi Politik & Kohesi Sosial**.  
Chatbot ini dibangun menggunakan **Flask (Python)** dan **OpenAI API**, lalu di-*deploy* melalui **Render.com**.

---

## 📂 Struktur Proyek

```

/ (root)
├── app.py               # Aplikasi utama Flask
├── requirements.txt     # Daftar dependensi Python
├── Procfile              # Konfigurasi Render
├── widget.html           # Antarmuka chatbot yang disematkan di LMS
├── README.md              # Dokumentasi internal proyek
└── /data
├── responses.json       # Respons statis berbasis aturan
└── context\_fici.txt     # (Opsional) Konteks khusus untuk chatbot

```

---

## ⚙️ Konfigurasi Lingkungan

1. Buat API key di [OpenAI Platform](https://platform.openai.com/api-keys).
2. Tambahkan ke Render → **Environment**:

```

KEY:    OPENAI\_API\_KEY
VALUE:  sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

````

---

## 🧠 Inisialisasi OpenAI Client

```python
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
````

> Pastikan `OPENAI_API_KEY` disimpan sebagai environment variable di Render, **jangan disimpan langsung di kode.**

---

## 📥 Memuat Konteks Kursus (Opsional)

```python
CONTEXT_FICI = ""
try:
    with open(os.path.join(os.path.dirname(__file__), 'data', 'context_fici.txt'), 'r', encoding='utf-8') as f:
        CONTEXT_FICI = f.read()
except FileNotFoundError:
    CONTEXT_FICI = ""
```

> File `context_fici.txt` berisi ringkasan materi kursus yang akan dipakai sebagai sistem konteks.

---

## 💬 Endpoint `/api/chat`

```python
@app.post('/api/chat')
def chat():
    user_text = request.json.get('message', '')

    messages = [
        {"role": "system", "content": "Anda adalah asisten pembelajaran FiCi."},
        {"role": "user", "content": user_text}
    ]

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.35,
        max_tokens=380,
    )

    ai_text = (resp.choices[0].message.content or "").strip()
    return jsonify({"reply": ai_text})
```

* `temperature` dapat diatur (0.3–0.4) untuk mengubah kreativitas jawaban.
* `max_tokens` menentukan panjang maksimal jawaban.
* File `responses.json` tetap bisa digunakan sebagai fallback jawaban statis.

---

## 💻 Antarmuka (widget.html)

* File `widget.html` menampilkan tampilan chatbot dan dikaitkan ke endpoint `/api/chat`.
* Pastikan bagian `fetch` di JS mengirim format JSON seperti ini:

```javascript
body: JSON.stringify({ message: text })
```

---

## 📌 Catatan Pengembangan

* Ubah konten di `responses.json` untuk jawaban berbasis aturan.
* Tambahkan `context_fici.txt` agar AI punya pengetahuan awal tentang kursus FiCi.
* Periksa **Logs** di Render jika AI gagal merespons (error handler akan menampilkan `AI error` di console).

---

✍️ *Dibuat untuk proyek FiCi Academy — Literasi Politik & Kohesi Sosial*

```

---

Kalau mau, saya juga bisa buatkan **README versi ringkas (1 layar)** untuk developer lain yang hanya butuh panduan setup cepat.  
Mau dibuatkan juga? (README Quickstart 🌱)
```
