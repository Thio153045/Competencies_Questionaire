# Aplikasi Kuesioner Kompetensi

Aplikasi Streamlit + MySQL untuk mengisi kuesioner 5 kompetensi dan menilai jawaban secara otomatis dengan skala 1–5.

- **Responden** mengisi identitas dan 5 jawaban terbuka. Skor tidak ditampilkan kepada responden.
- **Penilaian hibrida**: Gemini (`gemini-3.1-flash-lite`) dicoba lebih dulu. Jika API key kosong, salah, kuota habis, koneksi gagal, atau hasilnya tidak valid, penilaian otomatis beralih ke aturan kata kunci tanpa AI. Sumber setiap skor (AI/Aturan) tercatat.
- **Admin HR** login terpisah, melihat daftar responden, jawaban, skor, dan alasan penilaian, export laporan PDF, menilai ulang, dan menghapus data.

## Struktur Berkas

```
kuesioner_app/
├── app.py                 # Router halaman (Isi Kuesioner / Admin HR)
├── views/
│   ├── kuesioner.py       # Halaman responden
│   └── admin.py           # Halaman admin HR
├── questions.py           # Pertanyaan, panduan, kata kunci, rubrik
├── scoring.py             # Penilaian Gemini + fallback aturan kata kunci
├── db.py                  # Koneksi & query MySQL
├── pdf_report.py          # Laporan PDF per responden
├── create_admin.py        # Skrip membuat akun admin
├── schema.sql             # Skema database
├── requirements.txt
└── .streamlit/secrets.toml.example
```

## Instalasi

**1. Siapkan Python 3.11 atau lebih baru, lalu install dependensi**

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    |  Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

**2. Buat database MySQL**

```bash
mysql -u root -p < schema.sql
```

**3. Isi konfigurasi**

Salin `.streamlit/secrets.toml.example` menjadi `.streamlit/secrets.toml`, lalu isi data koneksi MySQL dan API key Gemini (dapatkan di https://aistudio.google.com/apikey).

**4. Buat akun admin**

```bash
python create_admin.py
```

**5. Jalankan aplikasi**

```bash
streamlit run app.py
```

Buka http://localhost:8501. Menu **Isi Kuesioner** untuk responden, menu **Admin HR** untuk login admin.

## Cara Kerja Penilaian Aturan (tanpa AI)

Dipakai otomatis saat AI tidak tersedia. Poin dihitung dari (maks 5):

| Unsur | Poin |
| --- | --- |
| Panjang jawaban (≥60 kata = 0,5; ≥120 kata = 1) | 0–1 |
| Unsur cerita: situasi, peran, tindakan, hasil (0,5 per unsur) | 0–2 |
| Peran pribadi (kata "saya" ≥3 kali) | 0–0,5 |
| Detail spesifik (angka, waktu, persen) | 0–0,5 |
| Kata kunci relevan kompetensi (≥2 = 0,5; ≥4 = 1) | 0–1 |

Skor = 1 + poin × 4/5, dibulatkan ke 1–5. Jawaban di bawah 20 kata otomatis bernilai 1. Jawaban hipotetis ("biasanya", "saya akan") tanpa cerita nyata dibatasi maksimal 2.

Kata kunci tiap kompetensi bisa disesuaikan di `questions.py`.

## Catatan

- Jika Gemini mengembalikan model tidak ditemukan, ganti `model` di `secrets.toml` dengan nama model yang tersedia di akun Anda.
- Jawaban yang sempat dinilai dengan aturan (misalnya saat koneksi internet putus) bisa dinilai ulang dengan AI melalui tombol **Nilai ulang** di halaman admin.
- Skor AI dan aturan adalah alat bantu. Keputusan akhir sebaiknya tetap ditinjau asesor.
