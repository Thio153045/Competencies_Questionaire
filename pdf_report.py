"""Pembuatan laporan PDF per responden."""

from __future__ import annotations

import io
import zipfile
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate, Frame, KeepTogether, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

from questions import KOMPETENSI_BY_KODE, LABEL_SKOR

WARNA_UTAMA = colors.HexColor("#1F3A5F")
WARNA_GARIS = colors.HexColor("#C9D3DF")
WARNA_LATAR = colors.HexColor("#F2F5F9")
MARGIN = 2 * cm


# ---------------------------------------------------------------------------
# Gaya & utilitas
# ---------------------------------------------------------------------------

def _styles() -> dict:
    ss = getSampleStyleSheet()
    normal = ParagraphStyle("n", parent=ss["Normal"], fontSize=9.5, leading=13)
    return {
        "judul": ParagraphStyle("judul", parent=ss["Title"], textColor=WARNA_UTAMA, fontSize=16),
        "sub": ParagraphStyle("sub", parent=ss["Normal"], alignment=TA_CENTER,
                              textColor=colors.grey, fontSize=9),
        "h2": ParagraphStyle("h2", parent=ss["Heading2"], textColor=WARNA_UTAMA,
                             fontSize=12, spaceBefore=12, spaceAfter=6),
        "h3": ParagraphStyle("h3", parent=normal, fontName="Helvetica-Bold", fontSize=10.5,
                             textColor=WARNA_UTAMA, spaceBefore=8, spaceAfter=3),
        "normal": normal,
        "kecil": ParagraphStyle("k", parent=normal, fontSize=8.5,
                                textColor=colors.HexColor("#444444")),
        "tebal": ParagraphStyle("b", parent=normal, fontName="Helvetica-Bold"),
        "kotak": ParagraphStyle("kotak", parent=normal, backColor=WARNA_LATAR,
                                borderColor=WARNA_GARIS, borderWidth=0.5, borderPadding=6,
                                leftIndent=6, rightIndent=6, spaceBefore=6, spaceAfter=10),
        "header": ParagraphStyle("sh", parent=normal, fontName="Helvetica-Bold",
                                 textColor=colors.white),
        "sel": ParagraphStyle("sel", parent=normal, fontSize=8.5, leading=11),
        "sel_tengah": ParagraphStyle("selc", parent=normal, fontSize=8.5, leading=11,
                                     alignment=TA_CENTER),
        "header_tengah": ParagraphStyle("shc", parent=normal, fontName="Helvetica-Bold",
                                        textColor=colors.white, fontSize=8.5,
                                        alignment=TA_CENTER),
    }


def _p(teks, style) -> Paragraph:
    """Paragraph aman: escape karakter XML dan pertahankan baris baru."""
    return Paragraph(escape(str(teks if teks is not None else "")).replace("\n", "<br/>"), style)


def _tgl(nilai) -> str:
    return nilai.strftime("%d-%m-%Y") if hasattr(nilai, "strftime") else str(nilai or "-")


def _skor_map(r: dict) -> dict:
    return {j["kode_kompetensi"]: j["skor"] for j in r["jawaban"]}


def _footer(canvas, doc):
    canvas.saveState()
    lebar = canvas._pagesize[0]
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(MARGIN, 1.2 * cm, "Laporan Kuesioner Kompetensi - Rahasia")
    canvas.drawRightString(lebar - MARGIN, 1.2 * cm, f"Halaman {doc.page}")
    canvas.restoreState()


def _doc(buf, judul: str, halaman_awal: str = "portrait") -> BaseDocTemplate:
    """Dokumen dengan dua template halaman: 'portrait' dan 'landscape'.

    Template yang disebut di halaman_awal dipakai untuk halaman pertama.
    """
    doc = BaseDocTemplate(buf, pagesize=A4, title=judul,
                          leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=MARGIN, bottomMargin=MARGIN)
    templates = []
    for nama, ukuran in (("portrait", A4), ("landscape", landscape(A4))):
        frame = Frame(MARGIN, MARGIN, ukuran[0] - 2 * MARGIN, ukuran[1] - 2 * MARGIN, id=nama)
        templates.append(PageTemplate(id=nama, frames=[frame], pagesize=ukuran, onPage=_footer))
    templates.sort(key=lambda t: t.id != halaman_awal)
    doc.addPageTemplates(templates)
    return doc


# ---------------------------------------------------------------------------
# Isi laporan satu responden (dipakai ulang di laporan massal)
# ---------------------------------------------------------------------------

def _story_responden(r: dict, s: dict) -> list:
    story = [Paragraph("Identitas Responden", s["h2"])]
    identitas = [
        ["Nama lengkap", r["nama"]],
        ["Posisi / jabatan", r["posisi"]],
        ["Unit kerja / departemen", r["unit_kerja"]],
        ["Lama bekerja", f"{r['lama_bekerja']} tahun"],
        ["Tanggal pengisian", _tgl(r["tanggal_pengisian"])],
    ]
    t = Table([[_p(a, s["tebal"]), _p(b, s["normal"])] for a, b in identitas],
              colWidths=[5 * cm, 11.5 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, WARNA_GARIS),
        ("BACKGROUND", (0, 0), (0, -1), WARNA_LATAR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)

    jawaban = r["jawaban"]
    skor_list = [j["skor"] for j in jawaban if j["skor"] is not None]
    story.append(Paragraph("Ringkasan Skor", s["h2"]))
    rows = [[_p("Kompetensi", s["header"]), _p("Skor", s["header"]),
             _p("Level", s["header"]), _p("Sumber", s["header"])]]
    for j in jawaban:
        k = KOMPETENSI_BY_KODE[j["kode_kompetensi"]]
        rows.append([
            _p(f"{k['kode']}. {k['nama']}", s["normal"]),
            _p(j["skor"] if j["skor"] is not None else "-", s["normal"]),
            _p(LABEL_SKOR.get(j["skor"], "-"), s["normal"]),
            _p(j["sumber"] or "-", s["normal"]),
        ])
    if skor_list:
        rata = sum(skor_list) / len(skor_list)
        rows.append([_p("Total / Rata-rata", s["tebal"]),
                     _p(f"{sum(skor_list)} / {rata:.2f}", s["tebal"]),
                     _p(LABEL_SKOR.get(round(rata), "-"), s["tebal"]), _p("", s["normal"])])
    t = Table(rows, colWidths=[8 * cm, 2.4 * cm, 3.6 * cm, 2.5 * cm], repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, WARNA_GARIS),
        ("BACKGROUND", (0, 0), (-1, 0), WARNA_UTAMA),
        ("BACKGROUND", (0, -1), (-1, -1), WARNA_LATAR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Skala: 5 = Sangat kuat, 4 = Kuat, 3 = Memadai, 2 = Kurang, 1 = Sangat kurang. "
        "Sumber 'AI' = dinilai Gemini; 'Aturan' = dinilai aturan kata kunci tanpa AI.",
        s["kecil"],
    ))

    story.append(Paragraph("Detail Jawaban dan Penilaian", s["h2"]))
    for j in jawaban:
        k = KOMPETENSI_BY_KODE[j["kode_kompetensi"]]
        story.append(KeepTogether([
            Paragraph(f"{k['kode']}. {escape(k['nama'])}", s["h3"]),
            _p(f"Pertanyaan: {k['pertanyaan']}", s["kecil"]),
            Spacer(1, 4),
        ]))
        # Paragraf berlatar (bukan tabel) agar jawaban panjang bisa berlanjut ke halaman berikutnya
        story.append(_p(j["jawaban"] or "-", s["kotak"]))
        story.append(Spacer(1, 4))
        sumber = j["sumber"] or "-"
        if j.get("model"):
            sumber += f" ({j['model']})"
        story.append(_p(
            f"Skor: {j['skor']} ({LABEL_SKOR.get(j['skor'], '-')}) | Sumber: {sumber}",
            s["tebal"]))
        story.append(_p(f"Alasan: {j['alasan'] or '-'}", s["normal"]))
    return story


# ---------------------------------------------------------------------------
# API publik
# ---------------------------------------------------------------------------

def build_pdf(responden: dict) -> bytes:
    """Laporan lengkap satu responden."""
    buf = io.BytesIO()
    s = _styles()
    doc = _doc(buf, f"Laporan Kompetensi - {responden['nama']}")
    story = [
        Paragraph("Laporan Hasil Kuesioner Kompetensi", s["judul"]),
        Paragraph(f"Dicetak {datetime.now():%d-%m-%Y %H:%M}", s["sub"]),
        Spacer(1, 12),
    ] + _story_responden(responden, s)
    doc.build(story)
    return buf.getvalue()


def nama_file_aman(teks: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in str(teks)).strip("_")[:60] or "responden"


def build_zip(respondents: list[dict]) -> bytes:
    """ZIP berisi satu PDF laporan untuk setiap responden.

    Jika PDF satu responden gagal dibuat, responden lain tetap dimasukkan dan
    dibuat file keterangan GAGAL_... untuk responden tersebut.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in respondents:
            dasar = f"laporan_kompetensi_{nama_file_aman(r['nama'])}_{r['id']}"
            try:
                zf.writestr(f"{dasar}.pdf", build_pdf(r))
            except Exception as exc:  # noqa: BLE001
                zf.writestr(
                    f"GAGAL_{dasar}.txt",
                    f"PDF untuk responden '{r['nama']}' (ID {r['id']}) gagal dibuat.\n"
                    f"Error: {type(exc).__name__}: {exc}\n"
                    "Gunakan export Excel untuk melihat jawaban responden ini.\n",
                )
    return buf.getvalue()
