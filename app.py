from flask import Flask, request, jsonify
import os, json, glob
from openai import OpenAI

# ---------- App & CORS ----------
app = Flask(__name__, static_folder='.', static_url_path='')
if os.getenv("RENDER"):
    from flask_cors import CORS
    CORS(app, resources={r"/*": {"origins": "https://program.jaemth.org"}})
    print("✅ CORS aktif untuk https://program.jaemth.org (produksi)")
else:
    print("🚧 CORS nonaktif (mode lokal)")

# ---------- OpenAI ----------
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ---------- Konstanta kursus ----------
COURSE_NAME = "FiCi Academy"
COURSE_URL  = "https://program.jaemth.org/course/view.php?id=3"

SYSTEM_PROMPT = (
    "Anda adalah Chatbot FiCi untuk kursus 'FiCi Academy — Literasi Politik & Kohesi Sosial'. "
    "Jawab ringkas, jelas, dan ramah dalam bahasa Indonesia. "
    "Fokus pada literasi politik etis, nilai interrelasional (kepercayaan, toleransi, inklusivitas, solidaritas, dialog), "
    "dan aktivitas kursus. Jika di luar konteks, jawab singkat dan arahkan ke modul kursus. "
    "Jika tidak tahu, katakan tidak tahu dan sarankan ketik: bantuan/materi/nilai atau kunjungi halaman kursus."
)

# ---------- Muat konteks (opsional) ----------
CONTEXT_FICI = ""
ctx_path = os.path.join(os.path.dirname(__file__), "data", "context_fici.txt")
if os.path.exists(ctx_path):
    with open(ctx_path, "r", encoding="utf-8") as f:
        CONTEXT_FICI = f.read().strip()

# ---------- Loader modular ----------
def load_keywords():
    base = os.path.join(os.path.dirname(__file__), "data", "keywords")
    kws = set()
    for path in sorted(glob.glob(os.path.join(base, "*.txt"))):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    k = line.strip().lower()
                    if k and not k.startswith("#"):
                        kws.add(k)
        except Exception as e:
            print("⚠️ Gagal baca keywords:", path, e)
    print(f"✅ Keywords loaded: {len(kws)} items")
    return sorted(kws)

def load_responses():
    base = os.path.join(os.path.dirname(__file__), "data", "responses")
    merged = {}
    for path in sorted(glob.glob(os.path.join(base, "*.json"))):
        try:
            with open(path, "r", encoding="utf-8") as f:
                part = json.load(f)
                if isinstance(part, dict):
                    merged.update(part)   # file yang urut akhir override
                    print(f"✅ Merge: {os.path.basename(path)} ({len(part)} keys)")
        except Exception as e:
            print("⚠️ Gagal muat responses:", path, e)
    print(f"✅ Total responses: {len(merged)} keys")
    return merged

FICI_KEYWORDS = load_keywords()
RESPONSES     = load_responses()

# ---------- Helper LLM ----------
def ask_llm(messages, temperature=0.35, max_tokens=380):
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (r.choices[0].message.content or "").strip()
    except Exception as e:
        print("AI error:", e)
        return "Maaf, AI sedang bermasalah. Coba lagi nanti atau ketik: bantuan."

# ---------- Routes ----------
@app.get("/")
def root():
    return "FiCi Chatbot is running. Open /widget.html for the chat widget."

@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200

@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    raw = data.get("message") or data.get("text") or data.get("query") or ""
    user_text = (raw or "").strip()
    if not user_text:
        return jsonify({"reply": "Pesan kosong. Coba ketik sesuatu."})

    # --- normalisasi & sinonim ringan ---
    norm = user_text.lower().strip()
    aliases = {
        "hai": "halo", "hello": "halo", "hi": "halo",
        "apa itu fici": "fici", "fic": "fici", "fi ci": "fici",
        "quiz": "kuis", "nilai-nilai": "nilai", "nilai fici": "nilai",
        "literasi": "literasi politik", "politik": "literasi politik",
        "kohesi": "kohesi sosial",
    }
    norm = aliases.get(norm, norm)

    # --- lookup rule-based exact/fuzzy ---
    def lookup(key: str):
        if key in RESPONSES:
            return RESPONSES[key]
        for k in RESPONSES.keys():
            if k in key:
                return RESPONSES[k]
        return None

    reply = lookup(norm)
    if reply:
        reply = reply.replace("{course_name}", COURSE_NAME).replace("{course_url}", COURSE_URL)
        return jsonify({"reply": reply})

    # --- gatekeeper topik FiCi (dari file keywords) ---
    if not any(kw in norm for kw in FICI_KEYWORDS):
        return jsonify({"reply": "Saya chatbot kursus FiCi. Untuk pertanyaan umum silakan cari di sumber lain."})

    # --- fallback ke LLM (+konteks) ---
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if CONTEXT_FICI:
        messages.append({"role": "system", "content": "Konteks kursus (ringkas):\n" + CONTEXT_FICI})
    messages.append({"role": "user", "content": user_text})

    ai_text = ask_llm(messages, temperature=0.35, max_tokens=380)
    if not ai_text:
        ai_text = "Maaf, saya belum bisa menjawab itu. Coba ketik: bantuan."
    return jsonify({"reply": ai_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
