"""Halaman pengisian kuesioner oleh responden."""

from datetime import date

import streamlit as st

import db
from questions import KOMPETENSI
from scoring import score_answers

MIN_KATA = 20


def reset_form():
    for key in list(st.session_state.keys()):
        if key.startswith("f_") or key == "terkirim":
            del st.session_state[key]


# --- Setelah terkirim: hanya ucapan terima kasih, tanpa skor ---
if st.session_state.get("terkirim"):
    st.title("Terima kasih 🙏")
    st.success("Jawaban Anda telah berhasil dikirim dan tersimpan.")
    st.write("Terima kasih atas kesediaan Anda mengisi kuesioner ini.")
    st.button("Isi kuesioner baru", on_click=reset_form)
    st.stop()


st.title("Kuesioner Kompetensi")
st.caption(
    "Kuesioner ini berisi 5 pertanyaan terbuka yang diisi sendiri oleh responden, "
    "satu pertanyaan untuk setiap kompetensi. Perkiraan waktu pengisian 30–45 menit."
)

with st.expander("📋 Petunjuk Pengisian", expanded=True):
    st.markdown(
        """
1. Bacalah setiap pertanyaan dengan saksama, lalu tuliskan jawaban Anda pada kolom **Jawaban** di bawahnya.
2. Jawablah berdasarkan **pengalaman nyata** yang pernah Anda alami di pekerjaan, organisasi, atau pendidikan, bukan apa yang "seharusnya" atau "biasanya" dilakukan.
3. Gunakan poin panduan di bawah setiap pertanyaan agar jawaban Anda lengkap: situasinya, peran Anda, tindakan yang Anda lakukan, dan hasilnya.
4. Gunakan kata **"saya"** untuk menjelaskan peran pribadi Anda, meskipun pekerjaan tersebut dilakukan bersama tim.
5. Panjang jawaban yang disarankan 1–2 paragraf (sekitar 100–200 kata) per pertanyaan.
6. Tidak ada jawaban benar atau salah. Jawablah dengan jujur dan spesifik.
"""
    )

with st.form("form_kuesioner"):
    st.subheader("Identitas Responden")
    nama = st.text_input("Nama lengkap *", key="f_nama")
    posisi = st.text_input("Posisi / jabatan yang dilamar atau dijabat *", key="f_posisi")
    unit_kerja = st.text_input("Unit kerja / departemen *", key="f_unit")
    c1, c2 = st.columns(2)
    lama_bekerja = c1.number_input(
        "Lama bekerja (tahun) *", min_value=0.0, max_value=60.0, step=0.5, key="f_lama"
    )
    tanggal = c2.date_input("Tanggal pengisian *", value=date.today(), key="f_tanggal",
                            format="DD/MM/YYYY")

    jawaban = {}
    for i, k in enumerate(KOMPETENSI, start=1):
        st.divider()
        st.subheader(f"{k['kode']}. {k['nama']}")
        st.caption(k["definisi"])
        st.markdown(f"**{i}. {k['pertanyaan']}**")
        st.markdown("Dalam jawaban Anda, jelaskan:\n" + "\n".join(f"- {p}" for p in k["panduan"]))
        jawaban[k["kode"]] = st.text_area(
            "Jawaban *", key=f"f_jawab_{k['kode']}", height=220,
            placeholder="Tuliskan pengalaman nyata Anda di sini...",
        )

    st.divider()
    st.subheader("Pernyataan Responden")
    pernyataan = st.checkbox(
        "Dengan ini saya menyatakan bahwa seluruh jawaban di atas saya isi sendiri dengan "
        "jujur dan sesuai dengan pengalaman saya.",
        key="f_pernyataan",
    )
    kirim = st.form_submit_button("Kirim Jawaban", type="primary", width="stretch")


if kirim:
    errors = []
    if not nama.strip():
        errors.append("Nama lengkap wajib diisi.")
    if not posisi.strip():
        errors.append("Posisi / jabatan wajib diisi.")
    if not unit_kerja.strip():
        errors.append("Unit kerja / departemen wajib diisi.")
    for k in KOMPETENSI:
        jumlah = len(jawaban[k["kode"]].split())
        if jumlah < MIN_KATA:
            errors.append(
                f"Jawaban bagian {k['kode']} ({k['nama']}) minimal {MIN_KATA} kata "
                f"(saat ini {jumlah} kata)."
            )
    if not pernyataan:
        errors.append("Mohon centang pernyataan responden sebelum mengirim.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        answers = {kode: teks.strip() for kode, teks in jawaban.items()}
        with st.spinner("Mengirim jawaban Anda, mohon tunggu..."):
            cfg = db.load_config().get("gemini", {})
            scores, _error_ai = score_answers(
                answers, cfg.get("api_key"), cfg.get("model", "gemini-3.1-flash-lite")
            )
            try:
                db.save_submission(
                    {
                        "nama": nama.strip(),
                        "posisi": posisi.strip(),
                        "unit_kerja": unit_kerja.strip(),
                        "lama_bekerja": lama_bekerja,
                        "tanggal_pengisian": tanggal,
                    },
                    answers,
                    scores,
                )
            except Exception as exc:  # noqa: BLE001
                st.error(
                    "Maaf, jawaban gagal disimpan. Jawaban Anda masih ada di formulir, "
                    "silakan coba kirim lagi atau hubungi panitia."
                )
                st.caption(f"Detail teknis: {type(exc).__name__}")
                st.stop()
        st.session_state["terkirim"] = True
        st.rerun()
