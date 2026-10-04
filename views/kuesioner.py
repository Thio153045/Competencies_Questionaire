"""Halaman pengisian kuesioner oleh responden, dengan simpan draf otomatis.

Draf disimpan di tabel `draf` dengan token acak yang juga ditaruh di alamat halaman
(?draf=...). Jika koneksi HP terputus dan halaman dimuat ulang, isian dipulihkan dari
draf tersebut.
"""

import re
import secrets
from datetime import date, datetime

import streamlit as st

import db
from questions import KOMPETENSI
from scoring import score_answers

MIN_KATA = 20
POLA_TOKEN = re.compile(r"^[A-Za-z0-9_-]{20,64}$")
KUNCI_ISIAN = (["f_nama", "f_posisi", "f_unit", "f_lama", "f_tanggal", "f_pernyataan"]
               + [f"f_jawab_{k['kode']}" for k in KOMPETENSI])


# ---------------------------------------------------------------------------
# Draf
# ---------------------------------------------------------------------------

def _token_draf() -> str:
    """Ambil token draf dari alamat halaman, atau buat yang baru."""
    token = st.query_params.get("draf", "")
    if not POLA_TOKEN.match(token):
        token = secrets.token_urlsafe(24)
        st.query_params["draf"] = token
        try:
            db.cleanup_drafts()
        except Exception:  # noqa: BLE001 - pembersihan tidak boleh mengganggu pengisian
            pass
    return token


def _pulihkan_draf(token: str) -> None:
    """Isi session_state dari draf di database (sekali per sesi)."""
    if st.session_state.get("draf_dimuat") == token:
        return
    st.session_state["draf_dimuat"] = token
    st.session_state.setdefault("f_lama", 0.0)
    st.session_state.setdefault("f_tanggal", date.today())
    try:
        data = db.load_draft(token)
    except Exception:  # noqa: BLE001
        data = None
    if not data:
        return
    for kunci, nilai in data.items():
        if kunci not in KUNCI_ISIAN or nilai is None:
            continue
        if kunci == "f_tanggal":
            try:
                nilai = date.fromisoformat(str(nilai)[:10])
            except ValueError:
                continue
        elif kunci == "f_lama":
            nilai = float(nilai)
        st.session_state[kunci] = nilai
    st.session_state["draf_dipulihkan"] = True


def simpan_draf() -> None:
    """Dipanggil setiap kali satu isian selesai diubah."""
    token = st.session_state.get("draf_dimuat")
    if not token:
        return
    data = {k: st.session_state.get(k) for k in KUNCI_ISIAN}
    try:
        db.save_draft(token, data)
        st.session_state["draf_waktu"] = datetime.now().strftime("%H:%M")
        st.session_state["draf_gagal"] = False
    except Exception:  # noqa: BLE001
        st.session_state["draf_gagal"] = True


def reset_form():
    for key in list(st.session_state.keys()):
        if key.startswith("f_") or key.startswith("draf_") or key == "terkirim":
            del st.session_state[key]
    st.query_params.clear()


# ---------------------------------------------------------------------------
# Setelah terkirim: hanya ucapan terima kasih, tanpa skor
# ---------------------------------------------------------------------------
if st.session_state.get("terkirim"):
    st.title("Terima kasih 🙏")
    st.success("Jawaban Anda telah berhasil dikirim dan tersimpan.")
    st.write("Terima kasih atas kesediaan Anda mengisi kuesioner ini.")
    st.button("Isi kuesioner baru", on_click=reset_form)
    st.stop()


token = _token_draf()
_pulihkan_draf(token)

st.title("Kuesioner Kompetensi")
st.caption(
    "Kuesioner ini berisi 5 pertanyaan terbuka yang diisi sendiri oleh responden, "
    "satu pertanyaan untuk setiap kompetensi. Perkiraan waktu pengisian 30–45 menit."
)

if st.session_state.pop("draf_dipulihkan", False):
    st.success("✅ Isian Anda sebelumnya berhasil dipulihkan. Silakan lanjutkan.")

st.info(
    "💾 **Jawaban tersimpan otomatis** setiap kali Anda selesai mengisi satu kotak "
    "(saat menyentuh area lain di layar). Jika halaman terputus, buka kembali halaman ini "
    "dari riwayat browser untuk melanjutkan. Mohon **jangan bagikan alamat halaman ini** "
    "kepada orang lain, karena berisi draf jawaban Anda."
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

# ---------------------------------------------------------------------------
# Formulir (tanpa st.form agar setiap isian bisa langsung disimpan sebagai draf)
# ---------------------------------------------------------------------------
st.subheader("Identitas Responden")
st.text_input("Nama lengkap *", key="f_nama", on_change=simpan_draf)
st.text_input("Posisi / jabatan yang dilamar atau dijabat *", key="f_posisi",
              on_change=simpan_draf)
st.text_input("Unit kerja / departemen *", key="f_unit", on_change=simpan_draf)
c1, c2 = st.columns(2)
c1.number_input("Lama bekerja (tahun) *", min_value=0.0, max_value=60.0, step=0.5,
                key="f_lama", on_change=simpan_draf)
c2.date_input("Tanggal pengisian *", key="f_tanggal", format="DD/MM/YYYY",
              on_change=simpan_draf)

for i, k in enumerate(KOMPETENSI, start=1):
    st.divider()
    # st.subheader(f"{k['kode']}. {k['nama']}")
    # st.caption(k["definisi"])
    st.markdown(f"**{i}. {k['pertanyaan']}**")
    st.markdown("Dalam jawaban Anda, jelaskan:\n" + "\n".join(f"- {p}" for p in k["panduan"]))
    st.text_area(
        "Jawaban *", key=f"f_jawab_{k['kode']}", height=220, on_change=simpan_draf,
        placeholder="Tuliskan pengalaman nyata Anda di sini...",
    )
    jumlah_kata = len(st.session_state.get(f"f_jawab_{k['kode']}", "").split())
    st.caption(f"{jumlah_kata} kata (minimal {MIN_KATA})")

st.divider()
st.subheader("Pernyataan Responden")
st.checkbox(
    "Dengan ini saya menyatakan bahwa seluruh jawaban di atas saya isi sendiri" 
    " dengan jujur tanpa bantuan siapapun termasuk AI dan sesuai dengan pengalaman saya."
    "Jika terindikasi adanya bantuan AI maka saya bersedia jawaban saya ditolak dan dianggap gagal.",
    key="f_pernyataan", on_change=simpan_draf,
)

if st.session_state.get("draf_gagal"):
    st.warning("Draf tidak dapat disimpan saat ini. Jawaban tetap bisa dikirim seperti biasa.")
elif st.session_state.get("draf_waktu"):
    st.caption(f"💾 Draf terakhir tersimpan pukul {st.session_state['draf_waktu']}")

kirim = st.button("Kirim Jawaban", type="primary", width="stretch")


# ---------------------------------------------------------------------------
# Validasi & pengiriman
# ---------------------------------------------------------------------------
if kirim:
    ss = st.session_state
    nama = ss.get("f_nama", "").strip()
    posisi = ss.get("f_posisi", "").strip()
    unit_kerja = ss.get("f_unit", "").strip()
    jawaban = {k["kode"]: ss.get(f"f_jawab_{k['kode']}", "") for k in KOMPETENSI}

    errors = []
    if not nama:
        errors.append("Nama lengkap wajib diisi.")
    if not posisi:
        errors.append("Posisi / jabatan wajib diisi.")
    if not unit_kerja:
        errors.append("Unit kerja / departemen wajib diisi.")
    for k in KOMPETENSI:
        jumlah = len(jawaban[k["kode"]].split())
        if jumlah < MIN_KATA:
            errors.append(
                f"Jawaban bagian {k['kode']} ({k['nama']}) minimal {MIN_KATA} kata "
                f"(saat ini {jumlah} kata)."
            )
    if not ss.get("f_pernyataan"):
        errors.append("Mohon centang pernyataan responden sebelum mengirim.")

    if errors:
        simpan_draf()
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
                        "nama": nama,
                        "posisi": posisi,
                        "unit_kerja": unit_kerja,
                        "lama_bekerja": ss.get("f_lama", 0.0),
                        "tanggal_pengisian": ss.get("f_tanggal", date.today()),
                    },
                    answers,
                    scores,
                )
            except Exception as exc:  # noqa: BLE001
                simpan_draf()
                st.error(
                    "Maaf, jawaban gagal disimpan. Jawaban Anda masih ada di formulir dan "
                    "tersimpan sebagai draf, silakan coba kirim lagi atau hubungi panitia."
                )
                st.caption(f"Detail teknis: {type(exc).__name__}")
                st.stop()

        try:
            db.delete_draft(token)
        except Exception:  # noqa: BLE001 - draf lama akan terhapus otomatis setelah 14 hari
            pass
        for key in [k for k in st.session_state.keys()
                    if k.startswith("f_") or k.startswith("draf_")]:
            del st.session_state[key]
        st.query_params.clear()
        st.session_state["terkirim"] = True
        st.rerun()
