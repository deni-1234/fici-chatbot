from flask import Flask, request, jsonify, send_from_directory
import json
import os

app = Flask(__name__, static_folder='.', static_url_path='')

# Load responses
with open(os.path.join(os.path.dirname(__file__), 'data', 'responses.json'), 'r', encoding='utf-8') as f:
    RESPONSES = json.load(f)

COURSE_NAME = "FiCi Academy"
COURSE_URL = "https://program.jaemth.org/course/view.php?id=3"

@app.get('/')
def root():
    return "FiCi Chatbot is running. Open /widget.html for the chat widget."

@app.post('/api/chat')
def chat():
    data = request.get_json(silent=True) or {}
    # Terima berbagai nama field agar kompatibel dengan widget lama/baru
    raw = data.get('message') or data.get('text') or data.get('query') or ''
    text = (raw or '').strip().lower()

    # --- sinonim ringan / normalisasi kata ---
    aliases = {
        'hai': 'halo', 'hi': 'halo', 'hello': 'halo',
        'apa itu fici': 'fici', 'fic': 'fici', 'fi ci': 'fici',
        'quiz': 'kuis', 'nilai-nilai': 'nilai', 'nilai fici': 'nilai',
        'literasi': 'literasi politik', 'politik': 'literasi politik',
        'kohesi': 'kohesi sosial'
    }
    text = aliases.get(text, text)

    # Pastikan kunci responses lowercase
    # (jika file sudah lowercase, langkah ini aman-aman saja)
    def lookup(key):
        if key in RESPONSES:
            return RESPONSES[key]
        # cari kunci yang merupakan substring di input
        for k in RESPONSES.keys():
            if k in key:
                return RESPONSES[k]
        return None

    reply = lookup(text) or RESPONSES.get('unknown', 'Maaf, saya belum paham. Coba ketik: bantuan.')
    return jsonify({'reply': reply})

# Serve widget.html and any static assets from root via static_folder config
# (No extra route needed)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
