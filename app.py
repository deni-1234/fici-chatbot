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
    msg = (data.get('message') or '').lower().strip()

    # Default reply
    reply = "Maaf, saya belum mengerti pertanyaan Anda. Coba ketik: halo, materi, fici, motivasi, bantuan."

    # Simple keyword-based matching
    for key, val in RESPONSES.items():
        if key in msg:
            reply = val
            break

    # Dynamic injections
    reply = reply.replace("{COURSE_NAME}", COURSE_NAME).replace("{COURSE_URL}", COURSE_URL)

    return jsonify({"response": reply})

# Serve widget.html and any static assets from root via static_folder config
# (No extra route needed)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
