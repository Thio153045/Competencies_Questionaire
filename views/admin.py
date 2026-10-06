"""Halaman Admin HR: login, daftar responden, detail jawaban & skor, export PDF."""

from datetime import datetime

import pandas as pd
import streamlit as st

import db
from excel_report import build_excel
from pdf_report import build_pdf, build_zip, nama_file_aman
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
        for key in ("admin", "export_massal"):
            st.session_state.pop(key, None)
        st.rerun()

# ---------------------------------------------------------------------------
# Daftar responden + filter
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
df["tanggal_pengisian"] = pd.to_datetime(df["tanggal_pengisian"]).dt.date

f1, f2 = st.columns([3, 2])
cari = f1.text_input("🔎 Cari nama / posisi / unit kerja")
tgl_min, tgl_max = df["tanggal_pengisian"].min(), df["tanggal_pengisian"].max()
rentang = f2.date_input("📅 Rentang tanggal pengisian", value=(tgl_min, tgl_max),
                        format="DD/MM/YYYY")

if cari:
    mask = (
        df["nama"].str.contains(cari, case=False, na=False, regex=False)
        | df["posisi"].str.contains(cari, case=False, na=False, regex=False)
        | df["unit_kerja"].str.contains(cari, case=False, na=False, regex=False)
    )
    df = df[mask]
if isinstance(rentang, (tuple, list)) and len(rentang) == 2:
    dari, sampai = rentang
    df = df[(df["tanggal_pengisian"] >= dari) & (df["tanggal_pengisian"] <= sampai)]
else:
    dari = sampai = None

tampil = df.rename(columns={
    "nama": "Nama", "posisi": "Posisi", "unit_kerja": "Unit Kerja",
    "tanggal_pengisian": "Tanggal", "skor_total": "Total (maks 25)",
    "rata_rata": "Rata-rata", "jumlah_aturan": "Dinilai Aturan",
})[["Nama", "Posisi", "Unit Kerja", "Tanggal", "Total (maks 25)", "Rata-rata", "Dinilai Aturan"]]
st.dataframe(tampil, hide_index=True, width="stretch")
st.caption(
    f"Menampilkan **{len(df)}** dari {len(rows)} responden. "
    "Kolom *Dinilai Aturan* = jumlah jawaban yang dinilai tanpa AI (fallback)."
)

if df.empty:
    st.stop()

# ---------------------------------------------------------------------------
# Export semua (sesuai filter): Excel atau ZIP berisi PDF per responden
# ---------------------------------------------------------------------------
st.divider()
st.subheader("📦 Export Semua")
st.caption(f"Yang diekspor adalah **{len(df)} responden** sesuai filter di atas.")

PILIHAN_FORMAT = {
    "📊 Excel (rekap + detail jawaban)": "excel",
    "🗂️ ZIP berisi PDF per responden": "zip",
}
label_format = st.radio("Format", list(PILIHAN_FORMAT.keys()), horizontal=True)
jenis_format = PILIHAN_FORMAT[label_format]
if jenis_format == "excel":
    st.caption("Sheet **Rekap** (skor per responden), **Detail Jawaban** "
               "(jawaban, skor, alasan), dan **Keterangan**.")
else:
    st.caption("Satu file PDF laporan lengkap untuk setiap responden, dikemas dalam satu ZIP.")

ids = df["id"].astype(int).tolist()
kunci_export = (tuple(ids), jenis_format)

if st.button("Siapkan file", type="primary"):
    keterangan = []
    if cari:
        keterangan.append(f"Pencarian: '{cari}'")
    if dari and sampai:
        keterangan.append(f"Periode {dari:%d-%m-%Y} s.d. {sampai:%d-%m-%Y}")
    stempel = datetime.now().strftime("%Y%m%d_%H%M")

    with st.spinner(f"Menyiapkan file untuk {len(ids)} responden..."):
        data_responden = db.get_respondents_detail(ids)
        if jenis_format == "excel":
            isi = build_excel(data_responden, " | ".join(keterangan))
            nama = f"rekap_kompetensi_{stempel}.xlsx"
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            isi = build_zip(data_responden)
            nama = f"laporan_pdf_kompetensi_{stempel}.zip"
            mime = "application/zip"

    st.session_state["export_massal"] = {
        "kunci": kunci_export, "isi": isi, "nama": nama, "mime": mime,
    }

hasil = st.session_state.get("export_massal")
if hasil and hasil.get("kunci") == kunci_export:
    st.download_button(f"⬇️ Unduh {hasil['nama']}", data=hasil["isi"],
                       file_name=hasil["nama"], mime=hasil["mime"])
elif hasil:
    st.caption("Filter atau format berubah. Klik **Siapkan file** lagi.")

# ---------------------------------------------------------------------------
# Detail responden
# ---------------------------------------------------------------------------
st.divider()
st.subheader("🔍 Detail Responden")
pilihan = {f"{r['nama']} – {r['posisi']} (ID {r['id']})": int(r["id"]) for _, r in df.iterrows()}
label = st.selectbox("Pilih responden untuk melihat detail", list(pilihan.keys()))
rid = pilihan[label]
r = db.get_respondent(rid)

st.markdown(f"### {r['nama']}")
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
        sumber = (j["sumber"] or "-") + (f" · {j['model']}" if j.get("model") else "")
        st.markdown(f"**Skor:** {j['skor']} – {LABEL_SKOR.get(j['skor'], '-')}  \n"
                    f"**Sumber penilaian:** {sumber}")
        st.markdown(f"**Alasan:** {j['alasan']}")

a1, a2, a3 = st.columns(3)
a1.download_button(
    "📄 Export PDF responden ini",
    data=build_pdf(r),
    file_name=f"laporan_kompetensi_{nama_file_aman(r['nama'])}_{rid}.pdf",
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
    st.session_state.pop("export_massal", None)
    st.session_state["flash"] = (
        ("warning", error_ai) if error_ai else ("success", "Penilaian diperbarui dengan AI.")
    )
    st.rerun()

with a3.popover("🗑️ Hapus", width="stretch"):
    st.write("Hapus responden ini beserta seluruh jawabannya?")
    if st.button("Ya, hapus", type="primary"):
        db.delete_respondent(rid)
        st.session_state.pop("export_massal", None)
        st.rerun()
