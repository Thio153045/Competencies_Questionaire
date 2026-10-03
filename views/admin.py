"""Halaman Admin HR: login, daftar responden, detail jawaban & skor, export PDF."""

import pandas as pd
import streamlit as st

import db
from pdf_report import build_pdf
from questions import KOMPETENSI_BY_KODE, LABEL_SKOR
from scoring import score_answers

# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
if "admin" not in st.session_state:
    st.title("🔒 Login Admin HR")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        masuk = st.form_submit_button("Masuk", type="primary")
    if masuk:
        try:
            admin = db.verify_admin(username.strip(), password)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Tidak dapat terhubung ke database: {exc}")
            st.stop()
        if admin:
            st.session_state["admin"] = admin
            st.rerun()
        else:
            st.error("Username atau password salah.")
    st.stop()

admin = st.session_state["admin"]
with st.sidebar:
    st.write(f"Masuk sebagai **{admin['nama']}**")
    if st.button("Keluar"):
        del st.session_state["admin"]
        st.rerun()

# ---------------------------------------------------------------------------
# Daftar responden
# ---------------------------------------------------------------------------
st.title("Hasil Kuesioner Kompetensi")

if "flash" in st.session_state:
    jenis, pesan = st.session_state.pop("flash")
    getattr(st, jenis)(pesan)

rows = db.list_respondents()
if not rows:
    st.info("Belum ada responden yang mengisi kuesioner.")
    st.stop()

df = pd.DataFrame(rows)
for kol in ("skor_total", "rata_rata", "jumlah_aturan"):
    df[kol] = pd.to_numeric(df[kol])
cari = st.text_input("🔎 Cari nama / posisi / unit kerja")
if cari:
    mask = (
        df["nama"].str.contains(cari, case=False, na=False)
        | df["posisi"].str.contains(cari, case=False, na=False)
        | df["unit_kerja"].str.contains(cari, case=False, na=False)
    )
    df = df[mask]

tampil = df.rename(columns={
    "nama": "Nama", "posisi": "Posisi", "unit_kerja": "Unit Kerja",
    "tanggal_pengisian": "Tanggal", "skor_total": "Total (maks 25)",
    "rata_rata": "Rata-rata", "jumlah_aturan": "Dinilai Aturan",
})[["Nama", "Posisi", "Unit Kerja", "Tanggal", "Total (maks 25)", "Rata-rata", "Dinilai Aturan"]]
st.dataframe(tampil, hide_index=True, width="stretch")
st.caption("Kolom *Dinilai Aturan* = jumlah jawaban yang dinilai tanpa AI (fallback).")

if df.empty:
    st.stop()

# ---------------------------------------------------------------------------
# Detail responden
# ---------------------------------------------------------------------------
st.divider()
pilihan = {f"{r['nama']} – {r['posisi']} (ID {r['id']})": int(r["id"]) for _, r in df.iterrows()}
label = st.selectbox("Pilih responden untuk melihat detail", list(pilihan.keys()))
rid = pilihan[label]
r = db.get_respondent(rid)

st.subheader(r["nama"])
c1, c2, c3 = st.columns(3)
c1.metric("Posisi", r["posisi"])
c2.metric("Unit kerja", r["unit_kerja"])
c3.metric("Lama bekerja", f"{r['lama_bekerja']} th")

skor_list = [j["skor"] for j in r["jawaban"] if j["skor"] is not None]
if skor_list:
    rata = sum(skor_list) / len(skor_list)
    m1, m2 = st.columns(2)
    m1.metric("Skor total", f"{sum(skor_list)} / 25")
    m2.metric("Rata-rata", f"{rata:.2f}", LABEL_SKOR.get(round(rata)), delta_color="off")

ringkas = pd.DataFrame([
    {
        "Kompetensi": f"{j['kode_kompetensi']}. {KOMPETENSI_BY_KODE[j['kode_kompetensi']]['nama']}",
        "Skor": j["skor"],
        "Level": LABEL_SKOR.get(j["skor"], "-"),
        "Sumber": j["sumber"],
    }
    for j in r["jawaban"]
])
st.dataframe(ringkas, hide_index=True, width="stretch")

for j in r["jawaban"]:
    k = KOMPETENSI_BY_KODE[j["kode_kompetensi"]]
    with st.expander(f"{k['kode']}. {k['nama']} — Skor {j['skor']} ({j['sumber']})"):
        st.markdown(f"**Pertanyaan:** {k['pertanyaan']}")
        st.markdown("**Jawaban:**")
        st.info(j["jawaban"])
        sumber = j["sumber"] + (f" · {j['model']}" if j.get("model") else "")
        st.markdown(f"**Skor:** {j['skor']} – {LABEL_SKOR.get(j['skor'], '-')}  \n"
                    f"**Sumber penilaian:** {sumber}")
        st.markdown(f"**Alasan:** {j['alasan']}")

# ---------------------------------------------------------------------------
# Aksi: export PDF, nilai ulang, hapus
# ---------------------------------------------------------------------------
st.divider()
a1, a2, a3 = st.columns(3)

nama_file = "".join(c if c.isalnum() else "_" for c in r["nama"])
a1.download_button(
    "📄 Export PDF",
    data=build_pdf(r),
    file_name=f"laporan_kompetensi_{nama_file}_{rid}.pdf",
    mime="application/pdf",
    width="stretch",
)

if a2.button("🔄 Nilai ulang", width="stretch",
             help="Menilai ulang semua jawaban (AI dulu, aturan jika AI gagal)."):
    answers = {j["kode_kompetensi"]: j["jawaban"] for j in r["jawaban"]}
    cfg = db.load_config().get("gemini", {})
    with st.spinner("Menilai ulang..."):
        scores, error_ai = score_answers(
            answers, cfg.get("api_key"), cfg.get("model", "gemini-3.1-flash-lite")
        )
        db.update_scores(rid, scores)
    st.session_state["flash"] = ("warning", error_ai) if error_ai else ("success", "Penilaian diperbarui dengan AI.")
    st.rerun()

with a3.popover("🗑️ Hapus", width="stretch"):
    st.write("Hapus responden ini beserta seluruh jawabannya?")
    if st.button("Ya, hapus", type="primary"):
        db.delete_respondent(rid)
        st.rerun()
