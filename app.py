from flask import Flask, request, jsonify, send_from_directory
import json, os, openai
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__, static_folder='.', static_url_path='')

# ✅ Aktifkan CORS hanya jika di server Render (produksi)
if os.getenv("RENDER"):
    from flask_cors import CORS
    CORS(app, resources={
        r"/*": {"origins": "https://program.jaemth.org"}
    })
    print("✅ CORS aktif untuk https://program.jaemth.org (produksi)")
else:
    print("🚧 CORS nonaktif (mode lokal)")


# Muat konteks kursus (opsional tapi dianjurkan)
CONTEXT_FICI = ""
try:
    with open(os.path.join(os.path.dirname(__file__), 'data', 'context_fici.txt'), 'r', encoding='utf-8') as f:
        CONTEXT_FICI = f.read()
except FileNotFoundError:
    CONTEXT_FICI = ""

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

# ============================
# ROUTES: Root, Health, Chat
# ============================

@app.get("/")
def root():
    return "FiCi Chatbot is running. Open /widget.html for the chat widget."


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200


@app.post("/api/chat")
def chat():
    try:
        # Ambil input user
        data = request.get_json(silent=True) or {}
        raw = data.get("message") or data.get("text") or data.get("query") or ""
        user_text = (raw or "").strip()
        if not user_text:
            return jsonify({"reply": "Pesan kosong. Coba ketik sesuatu."})

        # ---------- normalisasi & sinonim ringan ----------
        norm = user_text.lower()
        aliases = {
            "hai": "halo", "hello": "halo", "hi": "halo",
            "apa itu fici": "fici", "fic": "fici", "fi ci": "fici",
            "quiz": "kuis", "nilai-nilai": "nilai", "nilai fici": "nilai",
            "literasi": "literasi politik", "politik": "literasi politik",
            "kohesi": "kohesi sosial",
        }
        norm = aliases.get(norm, norm)

        # ---------- lookup rule-based dari responses.json ----------
        def lookup(key: str):
            if key in RESPONSES:
                return RESPONSES[key]  # exact match
            for k in RESPONSES.keys():
                if k in key:
                    return RESPONSES[k]  # fuzzy sederhana
            return None

        reply = lookup(norm)
        if reply:
            reply = reply.replace("{course_name}", "FiCi Academy") \
                         .replace("{course_url}", "https://program.jaemth.org/course/view.php?id=3")
            return jsonify({"reply": reply})
# ---------- deteksi pertanyaan umum (di luar topik FiCi) ----------
fici_keywords = [
    "fici", "fi ci", "faith-inspired", "literasi politik",
    "kohesi sosial", "nilai", "interrelasional", "solidaritas",
    "toleransi", "inklusivitas", "dialog", "pro-sosial", 
    “martabat manusia”, “kebaikan bersama”, “subsidiaritas”, “hak dan kewajiban warga”, “keberpihakan kepada kaum miskin”, 
“keutuhanciptaan”, “kesejahteraan umum”, “keadilan distributif”, “rekonsiliasi”, “perdamaian sejati”, “persaudaraan sejati”, 
“bonum commune”,
“martabat manusia”, “kebaikan bersama”, “subsidiaritas”, 
“hak dan kewajiban warga”, “keberpihakan kepada kaum miskin”, “keutuhanciptaan”, “kesejahteraan umum”, “keadilan distributif”, “rekonsiliasi”, “perdamaian sejati”
“persaudaraan sejati”, “bonum commune”

“faith-inspired interrelational citizenship”, “kewarganegaraan interrelasional”, “nilai-nilai fici”,
“kepercayaan”, “toleransi”, “solidaritas”, “inklusivitas”, “tanggung jawab sosial”, “kebinekaan”,

”literasi politik”, “kesadaran kritis”, “partisipasi aktif”, “kepedulian sosial”, “keterlibatan komunitas”,
“etika publik”, “kohesi sosial”, “budaya damai”, “moderasi beragama”, “anti-diskriminasi”,

“gotong royong”, “toleran”, “kasih”, “damai”, “tepo seliro”, “tenggang rasa”, “rukun”,
“musyawarah mufakat”, “rasa hormat antaragama”, “harmoni sosial”, “penghormatan leluhur”,
“nilai lokal kontekstual”,

“etika berbasis nilai”, “paradigma kritis transformatif”, “pendidikan berbasis proyek sosial”,
“refleksi iman”,

“spiritualitas kebersamaan”, “spiritualitas pelayanan”, “spiritualitas dialog”, 
“spiritualitas keterlibatan”, “spiritualitas lintas iman”, “iman yang transformatif”, 
“nilai keadilan sosial”, “nilai perdamaian”, “nilai kebersamaan”, “nilai kasih”,

“etika global”, “global citizenship”, “civic responsibility”, “civic engagement”, 
“civic ethics”, “demokrasi partisipatif”, “hak asasi manusia”, “resolusi konflik”, 
“mediasi sosial”, “komunikasi non-kekerasan”, “etika dialog”, 

“empati”, “resiliensi sosial”, “kecerdasan emosional”, “pengelolaan konflik”, 
“kesadaran diri”, “kerja sama tim”, “kepemimpinan etis”, “kolaborasi antarbudaya”, 
“literasi digital etis”, “etika media sosial”, 

“pendidikan karakter”, “pendidikan multikultural”, “pendidikan kontekstual”, 
“pendidikan transformatif”, “pendidikan berbasis komunitas”, “proyek sosial kampus”, 
“proyek interkultural”, “refleksi sosial”, “kesalehan sosial”, 

“habitus kewargaan”, “karakter reflektif”, “karakter dialogis”, 
“karakter solider”, “karakter kolaboratif”, “karakter etis”, “kesadaran ekologis”, 
“kesadaran sosial”, “kesadaran politik”, “kesadaran spiritual”, “

“kebijaksanaan lokal”, “pengetahuan lokal”, “pengetahuan partisipatif”, “pengetahuan reflektif”, 
“pengetahuan praksis”, “pengetahuan sosial”, “pengetahuan dialogis”, “pengetahuan spiritual”, 
“pengetahuan kontekstual”, “pengetahuan transformatif”, “pengetahuan lintas disiplin”, 

“kompetensi dialogal”, “dialog antariman”, “dialog antarbudaya”, “dialog antarwilayah”,
“dialog antaragama”, “dialog antargenerasi”, “ruang aman (safe space)”,
“ruang lintas identitas”, “ruang kolaboratif”, “ruang partisipatif”, "rumah bersama",

“rekayasa sosial berbasis nilai”, “inovasi sosial kampus”, “inovasi pembelajaran”,
“pembelajaran reflektif”, “pembelajaran kolaboratif”, “pembelajaran berbasis masalah”,
“pembelajaran berbasis proyek”, “pembelajaran kontekstual”, “pembelajaran partisipatif”,
“pembelajaran lintas disiplin”

]

# Jika teks tidak mengandung salah satu kata kunci FiCi, jangan teruskan ke GPT
if not any(kw in norm for kw in fici_keywords):
    return jsonify({
        "reply": "Saya chatbot kursus FiCi. Untuk pertanyaan umum silakan cari di sumber lain."
    })

        # ---------- fallback ke AI + konteks kursus ----------
        system_prompt = (
            "Anda adalah Chatbot FiCi untuk kursus 'FiCi Academy — Literasi Politik & Kohesi Sosial'. "
            "Jawab singkat, jelas, ramah, dan aman. Fokus pada literasi politik etis, "
            "nilai interrelasional (kepercayaan, toleransi, inklusivitas, solidaritas, dialog), "
            "dan aktivitas kursus. Jika tidak tahu, katakan tidak tahu dan arahkan ke modul "
            "(ketik: bantuan/materi/nilai) atau ke halaman kursus."
        )

        messages = [{"role": "system", "content": system_prompt}]
        if CONTEXT_FICI:
            messages.append({"role": "system", "content": "Konteks kursus (ringkas):\n" + CONTEXT_FICI})
        messages.append({"role": "user", "content": user_text})

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.35,
            max_tokens=380,
        )

        ai_text = (resp.choices[0].message.content or "").strip()
        return jsonify({"reply": ai_text or "Maaf, saya belum bisa menjawab itu. Coba ketik: bantuan."})

    except Exception as e:
        print("AI error:", e)
        return jsonify({"reply": "Maaf, AI sedang bermasalah. Coba lagi nanti atau ketik: bantuan."})
