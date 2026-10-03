"""Pembuatan laporan PDF hasil kuesioner per responden."""

from __future__ import annotations

import io
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from questions import KOMPETENSI_BY_KODE, LABEL_SKOR

WARNA_UTAMA = colors.HexColor("#1F3A5F")
WARNA_GARIS = colors.HexColor("#C9D3DF")
WARNA_LATAR = colors.HexColor("#F2F5F9")


def _p(teks, style) -> Paragraph:
    """Paragraph aman: escape karakter XML dan pertahankan baris baru."""
    return Paragraph(escape(str(teks or "")).replace("\n", "<br/>"), style)


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2 * cm, 1.2 * cm, "Laporan Kuesioner Kompetensi - Rahasia")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Halaman {doc.page}")
    canvas.restoreState()


def build_pdf(responden: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title=f"Laporan Kompetensi - {responden['nama']}",
    )
    ss = getSampleStyleSheet()
    judul = ParagraphStyle("judul", parent=ss["Title"], textColor=WARNA_UTAMA, fontSize=16)
    sub = ParagraphStyle("sub", parent=ss["Normal"], alignment=TA_CENTER,
                         textColor=colors.grey, fontSize=9)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=WARNA_UTAMA,
                        fontSize=12, spaceBefore=12, spaceAfter=6)
    normal = ParagraphStyle("n", parent=ss["Normal"], fontSize=9.5, leading=13)
    kecil = ParagraphStyle("k", parent=normal, fontSize=8.5, textColor=colors.HexColor("#444444"))
    tebal = ParagraphStyle("b", parent=normal, fontName="Helvetica-Bold")
    sel_header = ParagraphStyle("sh", parent=normal, fontName="Helvetica-Bold",
                                textColor=colors.white)

    story = [
        Paragraph("Laporan Hasil Kuesioner Kompetensi", judul),
        Paragraph(f"Dicetak {datetime.now():%d-%m-%Y %H:%M}", sub),
        Spacer(1, 12),
    ]

    # Identitas
    story.append(Paragraph("Identitas Responden", h2))
    identitas = [
        ["Nama lengkap", responden["nama"]],
        ["Posisi / jabatan", responden["posisi"]],
        ["Unit kerja / departemen", responden["unit_kerja"]],
        ["Lama bekerja", f"{responden['lama_bekerja']} tahun"],
        ["Tanggal pengisian", f"{responden['tanggal_pengisian']:%d-%m-%Y}"
         if hasattr(responden["tanggal_pengisian"], "strftime")
         else str(responden["tanggal_pengisian"])],
    ]
    t = Table([[_p(a, tebal), _p(b, normal)] for a, b in identitas],
              colWidths=[5 * cm, 12 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, WARNA_GARIS),
        ("BACKGROUND", (0, 0), (0, -1), WARNA_LATAR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)

    # Ringkasan skor
    jawaban = responden["jawaban"]
    skor_list = [j["skor"] for j in jawaban if j["skor"] is not None]
    story.append(Paragraph("Ringkasan Skor", h2))
    rows = [[_p("Kompetensi", sel_header), _p("Skor", sel_header),
             _p("Level", sel_header), _p("Sumber", sel_header)]]
    for j in jawaban:
        k = KOMPETENSI_BY_KODE[j["kode_kompetensi"]]
        rows.append([
            _p(f"{k['kode']}. {k['nama']}", normal),
            _p(j["skor"] if j["skor"] is not None else "-", normal),
            _p(LABEL_SKOR.get(j["skor"], "-"), normal),
            _p(j["sumber"] or "-", normal),
        ])
    if skor_list:
        rata = sum(skor_list) / len(skor_list)
        rows.append([_p("Total / Rata-rata", tebal),
                     _p(f"{sum(skor_list)} / {rata:.2f}", tebal),
                     _p(LABEL_SKOR.get(round(rata), "-"), tebal), _p("", normal)])
    t = Table(rows, colWidths=[8.5 * cm, 2.5 * cm, 3.5 * cm, 2.5 * cm], repeatRows=1)
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
        kecil,
    ))

    # Detail jawaban
    story.append(Paragraph("Detail Jawaban dan Penilaian", h2))
    for j in jawaban:
        k = KOMPETENSI_BY_KODE[j["kode_kompetensi"]]
        blok = [
            Paragraph(f"{k['kode']}. {escape(k['nama'])}",
                      ParagraphStyle("h3", parent=tebal, fontSize=10.5, textColor=WARNA_UTAMA,
                                     spaceBefore=8, spaceAfter=3)),
            _p(f"Pertanyaan: {k['pertanyaan']}", kecil),
            Spacer(1, 4),
        ]
        story.append(KeepTogether(blok))
        kotak = Table([[_p(j["jawaban"], normal)]], colWidths=[17 * cm])
        kotak.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, WARNA_GARIS),
            ("BACKGROUND", (0, 0), (-1, -1), WARNA_LATAR),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(kotak)
        story.append(Spacer(1, 4))
        sumber = j["sumber"] or "-"
        if j.get("model"):
            sumber += f" ({j['model']})"
        story.append(_p(
            f"Skor: {j['skor']} ({LABEL_SKOR.get(j['skor'], '-')}) | Sumber: {sumber}", tebal))
        story.append(_p(f"Alasan: {j['alasan'] or '-'}", normal))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
