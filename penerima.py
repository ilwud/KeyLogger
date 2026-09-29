from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from datetime import datetime
import html
import sqlite3

DB = "pendaftaran.db"

# Buat tabel baru jika database belum ada
with sqlite3.connect(DB) as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS peserta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            nama_panggilan TEXT,
            waktu_daftar TEXT NOT NULL
        )
    """)

    # Tambahkan kolom nama_panggilan jika memakai database dari kode sebelumnya
    kolom = {baris[1] for baris in db.execute("PRAGMA table_info(peserta)")}
    if "nama_panggilan" not in kolom:
        db.execute("ALTER TABLE peserta ADD COLUMN nama_panggilan TEXT")


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

  <label for="nama_panggilan">Nama panggilan</label>
  <input id="nama_panggilan" name="nama_panggilan" required maxlength="50">

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
        nama_panggilan = data.get("nama_panggilan", [""])[0].strip()

        if not nama or "@" not in email or not nama_panggilan:
            self.kirim(
                "<h1>Data belum lengkap</h1><a href='/'>Coba lagi</a>",
                400
            )
            return

        try:
            with sqlite3.connect(DB) as db:
                db.execute(
                    """INSERT INTO peserta
                       (nama, email, nama_panggilan, waktu_daftar)
                       VALUES (?, ?, ?, ?)""",
                    (
                        nama,
                        email,
                        nama_panggilan,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                )
        except sqlite3.IntegrityError:
            self.kirim(
                "<h1>Email sudah terdaftar</h1><a href='/'>Kembali</a>",
                409
            )
            return

        print(
            f"Pendaftaran diterima: {nama} / {nama_panggilan} ({email})",
            flush=True
        )

        self.kirim(
            "<h1>Pendaftaran berhasil!</h1>"
            f"<p>Terima kasih, {html.escape(nama_panggilan)}. "
            "Data kamu telah diterima.</p>"
        )


print("Buka http://localhost:8000")
HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
