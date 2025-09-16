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
    data = request.get_json(silent=True) or {}
    # kompatibel dgn berbagai payload
    raw = data.get('message') or data.get('text') or data.get('query') or ''
    text = (raw or '').strip().lower()

    # ---- sinonim & normalisasi ringan ----
    aliases = {
        'hai': 'halo', 'hello': 'halo', 'hi': 'halo',
        'apa itu fici': 'fici', 'fic': 'fici', 'fi ci': 'fici',
        'quiz': 'kuis', 'nilai fici': 'nilai', 'nilai-nilai': 'nilai',
        'literasi': 'literasi politik', 'politik': 'literasi politik',
        'kohesi': 'kohesi sosial'
    }
    text = aliases.get(text, text)

    # ---- lookup rule-based ----
    def lookup(key):
        if key in RESPONSES:  # exact
            return RESPONSES[key]
        # fuzzy sederhana: cocokkan substring kunci yang ada di input
        for k in RESPONSES.keys():
            if k in key:
                return RESPONSES[k]
        return None

    reply = lookup(text)

    # inject dinamis (jika dipakai di responses.json)
    if reply:
        reply = (reply
                 .replace("{course_name}", COURSE_NAME)
                 .replace("{course_url}", COURSE_URL))

    # ---- fallback LLM bila tidak ketemu ----
    if not reply:
        reply = ask_llm_with_context(raw)

    return jsonify({'reply': reply})

# Static: widget
@app.get('/widget.html')
def widget():
    return send_from_directory('.', 'widget.html')
