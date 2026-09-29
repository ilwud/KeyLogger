from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from datetime import datetime
import hashlib
import html
import os
import sqlite3

DB = "pendaftaran.db"

with sqlite3.connect(DB) as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS peserta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            salt BLOB NOT NULL,
            password_hash BLOB NOT NULL,
            waktu_daftar TEXT NOT NULL
        )
    """)

def halaman(isi):
    return f"""<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pendaftaran Lomba Kampus</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      background: #f1f5f9;
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
    }}
    .kartu {{
      background: white;
      width: min(90%, 380px);
      padding: 28px;
      border-radius: 14px;
      box-shadow: 0 8px 28px #00000015;
    }}
    h1 {{ font-size: 24px; margin-bottom: 6px; }}
    p {{ color: #64748b; line-height: 1.5; }}
    label {{ display: block; margin: 18px 0 6px; font-weight: bold; }}
    input {{
      box-sizing: border-box;
      width: 100%;
      padding: 11px;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      font-size: 15px;
    }}
    button {{
      width: 100%;
      margin-top: 24px;
      padding: 12px;
      border: 0;
      border-radius: 8px;
      background: #2563eb;
      color: white;
      font-size: 16px;
      cursor: pointer;
    }}
    button:hover {{ background: #1d4ed8; }}
  </style>
</head>
<body><main class="kartu">{isi}</main></body>
</html>"""

FORM = """
<h1>Pendaftaran Lomba Kampus</h1>
<p>Isi data berikut untuk mendaftar sebagai peserta.</p>
<form method="post">
  <label for="nama">Nama lengkap</label>
  <input id="nama" name="nama" required maxlength="100">

  <label for="email">Email</label>
  <input id="email" name="email" type="email" required maxlength="150">

  <label for="password">Password</label>
  <input id="password" name="password" type="password"
         required minlength="8" autocomplete="new-password">

  <button type="submit">Daftar Sekarang</button>
</form>
"""

class Handler(BaseHTTPRequestHandler):
    def kirim(self, konten, status=200):
        data = halaman(konten).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.kirim(FORM)

    def do_POST(self):
        panjang = int(self.headers.get("Content-Length", 0))
        if panjang > 10_000:
            self.kirim("<h1>Data terlalu besar</h1>", 413)
            return

        data = parse_qs(self.rfile.read(panjang).decode("utf-8"))
        nama = data.get("nama", [""])[0].strip()
        email = data.get("email", [""])[0].strip().lower()
        password = data.get("password", [""])[0]

        if not nama or "@" not in email or len(password) < 8:
            self.kirim("<h1>Data belum valid</h1><a href='/'>Coba lagi</a>", 400)
            return

        salt = os.urandom(16)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, 600_000
        )

        try:
            with sqlite3.connect(DB) as db:
                db.execute(
                    """INSERT INTO peserta
                       (nama, email, salt, password_hash, waktu_daftar)
                       VALUES (?, ?, ?, ?, ?)""",
                    (nama, email, salt, password_hash,
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
        except sqlite3.IntegrityError:
            self.kirim("<h1>Email sudah terdaftar</h1><a href='/'>Kembali</a>", 409)
            return

        print(f"Pendaftaran diterima: {nama} ({email})", flush=True)
        self.kirim(
            f"<h1>Pendaftaran berhasil!</h1>"
            f"<p>Terima kasih, {html.escape(nama)}. Data kamu telah diterima.</p>"
        )

print("Buka http://localhost:8000")
HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
