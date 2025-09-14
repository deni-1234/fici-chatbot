FiCi Chatbot — Paket Siap Deploy (Render)

FUNGSI:
- /api/chat  (POST) : terima { "message": "teks" } dan balas JSON
- /widget.html      : widget chat siap semat (iframe) ke Moodle

KONFIG (dalam app.py):
- COURSE_NAME = "Kursus Katekis"
- COURSE_URL  = "https://program.jaemth.org/course/view.php?id=2"

CARA DEPLOY (Render + GitHub):
1) Buat repo GitHub (mis. fici-chatbot) dan unggah semua file ini.
2) Di dashboard Render: New -> Web Service -> Hubungkan ke repo.
3) Build Command  : pip install -r requirements.txt
4) Start Command  : gunicorn app:app
5) Setelah live, buka https://NAMA-APLIKASI.onrender.com/widget.html
6) Semat ke Moodle via HTML block (iframe):
   <iframe src="https://NAMA-APLIKASI.onrender.com/widget.html" width="300" height="360" style="border:none;"></iframe>

CATATAN:
- Paket ini cocok untuk prototipe awal tanpa database.
- Untuk riset/log percakapan, tambahkan penyimpanan ke DB (MySQL/SQLite) di endpoint /api/chat.
