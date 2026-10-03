"""Akses database MySQL dan pembacaan konfigurasi."""

from __future__ import annotations

import tomllib
from contextlib import contextmanager
from pathlib import Path

import bcrypt
import pymysql
import pymysql.cursors

SECRETS_PATH = Path(__file__).parent / ".streamlit" / "secrets.toml"


def load_config() -> dict:
    """Baca konfigurasi dari st.secrets (saat di Streamlit) atau file secrets.toml."""
    try:
        import streamlit as st

        if "mysql" in st.secrets:
            return {k: dict(v) if hasattr(v, "keys") else v for k, v in st.secrets.items()}
    except Exception:  # noqa: BLE001 - di luar Streamlit, baca file langsung
        pass
    with open(SECRETS_PATH, "rb") as f:
        return tomllib.load(f)


@contextmanager
def get_conn():
    cfg = load_config()["mysql"]
    conn = pymysql.connect(
        host=cfg.get("db_host", "127.0.0.1"),
        port=int(cfg.get("db_port", 3307)),
        user=cfg["db_user"],
        password=cfg.get("db_password", ""),
        database=cfg["db_name"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_admin(username: str, password: str, nama: str) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO admin (username, password_hash, nama) VALUES (%s, %s, %s)",
            (username, hash_password(password), nama),
        )


def verify_admin(username: str, password: str) -> dict | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM admin WHERE username = %s", (username,))
        row = cur.fetchone()
    if row and bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
        return {"id": row["id"], "username": row["username"], "nama": row["nama"]}
    return None


# ---------------------------------------------------------------------------
# Responden, jawaban, penilaian
# ---------------------------------------------------------------------------

def save_submission(identitas: dict, answers: dict[str, str], scores: dict[str, dict]) -> int:
    """Simpan identitas, jawaban, dan penilaian dalam satu transaksi."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO responden
               (nama, posisi, unit_kerja, lama_bekerja, tanggal_pengisian, pernyataan)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                identitas["nama"], identitas["posisi"], identitas["unit_kerja"],
                identitas["lama_bekerja"], identitas["tanggal_pengisian"], 1,
            ),
        )
        responden_id = cur.lastrowid
        for kode, teks in answers.items():
            cur.execute(
                "INSERT INTO jawaban (responden_id, kode_kompetensi, jawaban) VALUES (%s, %s, %s)",
                (responden_id, kode, teks),
            )
            jawaban_id = cur.lastrowid
            s = scores[kode]
            cur.execute(
                """INSERT INTO penilaian (jawaban_id, skor, alasan, sumber, model)
                   VALUES (%s, %s, %s, %s, %s)""",
                (jawaban_id, s["skor"], s["alasan"], s["sumber"], s.get("model")),
            )
    return responden_id


def list_respondents() -> list[dict]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT r.id, r.nama, r.posisi, r.unit_kerja, r.tanggal_pengisian,
                      SUM(p.skor) AS skor_total,
                      ROUND(AVG(p.skor), 2) AS rata_rata,
                      SUM(p.sumber = 'Aturan') AS jumlah_aturan
               FROM responden r
               LEFT JOIN jawaban j ON j.responden_id = r.id
               LEFT JOIN penilaian p ON p.jawaban_id = j.id
               GROUP BY r.id
               ORDER BY r.created_at DESC"""
        )
        return cur.fetchall()


def get_respondent(responden_id: int) -> dict | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM responden WHERE id = %s", (responden_id,))
        responden = cur.fetchone()
        if not responden:
            return None
        cur.execute(
            """SELECT j.id AS jawaban_id, j.kode_kompetensi, j.jawaban,
                      p.skor, p.alasan, p.sumber, p.model, p.updated_at
               FROM jawaban j
               LEFT JOIN penilaian p ON p.jawaban_id = j.id
               WHERE j.responden_id = %s
               ORDER BY j.kode_kompetensi""",
            (responden_id,),
        )
        responden["jawaban"] = cur.fetchall()
    return responden


def update_scores(responden_id: int, scores: dict[str, dict]) -> None:
    """Perbarui penilaian (dipakai saat admin menilai ulang)."""
    with get_conn() as conn, conn.cursor() as cur:
        for kode, s in scores.items():
            cur.execute(
                """UPDATE penilaian p
                   JOIN jawaban j ON j.id = p.jawaban_id
                   SET p.skor = %s, p.alasan = %s, p.sumber = %s, p.model = %s
                   WHERE j.responden_id = %s AND j.kode_kompetensi = %s""",
                (s["skor"], s["alasan"], s["sumber"], s.get("model"), responden_id, kode),
            )


def delete_respondent(responden_id: int) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM responden WHERE id = %s", (responden_id,))
