from flask import Flask, request, jsonify, send_from_directory
import json, os
import openai

# set API key dari environment
openai.api_key = os.getenv("OPENAI_API_KEY")

# ---- Flask ----
app = Flask(__name__, static_folder='.', static_url_path='')

# ---- Load rule-based responses ----
with open(os.path.join(os.path.dirname(__file__), 'data', 'responses.json'), 'r', encoding='utf-8') as f:
    RESPONSES = json.load(f)

COURSE_NAME = "FiCi Academy"
COURSE_URL  = "https://program.jaemth.org/course/view.php?id=3"

# ---- (Opsional) konteks kursus untuk LLM ----
CONTEXT_FICI = ""
ctx_path = os.path.join(os.path.dirname(__file__), 'data', 'context_fici.txt')
if os.path.exists(ctx_path):
    with open(ctx_path, 'r', encoding='utf-8') as f:
        CONTEXT_FICI = f.read()

# ---- OpenAI client (env var di Render: OPENAI_API_KEY) ----
from openai import OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = (
    "Anda adalah Chatbot FiCi untuk kursus 'FiCi Academy — Literasi Politik & Kohesi Sosial'. "
    "Jawab ringkas, jelas, dan ramah dalam bahasa Indonesia. "
    "Fokus pada literasi politik etis, nilai interrelasional (kepercayaan, toleransi, inklusivitas, solidaritas, dialog), "
    "dan aktivitas kursus. Jika pertanyaan di luar konteks, jawab umum secara aman lalu arahkan ke modul kursus. "
    "Jika tidak tahu, katakan tidak tahu dan sarankan ketik: bantuan/materi/nilai, atau kunjungi halaman kursus."
)

def ask_llm(user_text: str) -> str:
    """Fallback ke LLM tanpa konteks."""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            temperature=0.4,
            max_tokens=350,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return "Maaf, AI sedang bermasalah. Coba lagi nanti atau ketik: bantuan."

def ask_llm_with_context(user_text: str) -> str:
    """Fallback LLM dengan konteks FiCi (RAG ringan)."""
    if not CONTEXT_FICI:
        return ask_llm(user_text)
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": "Konteks kursus (ringkas):\n" + CONTEXT_FICI},
                {"role": "user", "content": user_text}
            ],
            temperature=0.3,
            max_tokens=380,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return ask_llm(user_text)

@app.get('/')
def root():
    return "FiCi Chatbot is running. Open /widget.html for the chat widget."

@app.post('/api/chat')
def chat():
    try:
        data = request.get_json(silent=True) or {}
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"reply": "Tidak ada pesan yang dikirim."})

        # Kirim pertanyaan user ke OpenAI
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Kamu adalah chatbot pembelajaran untuk FiCi Academy."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=300,
            temperature=0.7
        )

        bot_reply = response.choices[0].message.content.strip()
        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("Error:", e)
        return jsonify({"reply": "Maaf, AI sedang bermasalah. Coba lagi nanti atau ketik: bantuan."})

# Static: widget
@app.get('/widget.html')
def widget():
    return send_from_directory('.', 'widget.html')
