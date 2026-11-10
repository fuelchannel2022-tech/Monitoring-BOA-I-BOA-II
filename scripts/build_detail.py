#!/usr/bin/env python3
"""Buat Excel "YYYYMMDD Data_SPBU_BOA.xlsx" dari CSV tab Data_SPBU_BOA.

- Satu baris per SPBU, 35 kolom (A–AI) seperti di spreadsheet.
- Filter dropdown di setiap kolom, judul kolom dan 3 kolom pertama dibekukan.
- Pengaturan cetak (A3 landscape, lebar 1 halaman, judul kolom diulang) dipakai
  LibreOffice saat mengonversi ke PDF.

Pemakaian:
    python scripts/build_detail.py detail.csv _site/unduh/data-spbu-boa.xlsx _site/data.json
"""
import csv
import json
import re
import sys
from datetime import datetime, timedelta, timezone

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.properties import PageSetupProperties

NCOL = 35
# (nama kolom, lebar)
COLUMNS = [
    ("No", 6), ("MOR", 6), ("SPBU", 11), ("Kab/Kota", 18), ("SAM", 14), ("SBM", 20),
    ("Omzet PSO (KL/hari)", 10), ("Omzet NPSO (KL/hari)", 10), ("Total Omzet (KL/hari)", 10),
    ("Kategori", 9), ("Tanggal Audit BOA 1", 18), ("Rencana Audit BOA 2", 18), ("Status SPBU", 12),
    # BOA 1
    ("Hasil Audit BOA 1", 13), ("CI - Hasil BOA 1", 10), ("FCA/SA - Surat Peringatan BOA 1", 30),
    ("Surat Peringatan - Upload", 13), ("SBM - Coaching SBM 1", 30), ("Coaching SBM 1 - Upload", 13),
    ("Pertare - Penawaran KSO 1", 26), ("Hasil Nego KSO", 13), ("Status KSO di Realisasi", 13),
    # BOA 2
    ("Tanggal Audit BOA 2", 18), ("SBM/CO - Surat Kesanggupan Mitra", 26), ("Surat Kesanggupan - Upload", 13),
    ("Hasil Audit BOA 2", 14), ("CI - Hasil BOA 2", 10), ("FCA/SA - Surat Peringatan BOA 2", 30),
    ("Surat Peringatan BOA 2 - Upload", 13), ("SBM - Coaching SBM 2", 26), ("Coaching SBM 2 - Upload", 13),
    ("SAM - Tutup/Pembinaan", 11), ("SAM - KSO Mandatory", 11),
    # status
    ("Status BOA I", 19), ("Status BOA II", 19),
]
GROUPS = [("Data SPBU", 0, 12), ("BOA I", 13, 21), ("BOA II", 22, 32), ("Status Audit", 33, 34)]
NUM_INT = {0, 1}
NUM_DEC = {6, 7, 8}
RESULT_COLS = {14, 26}
UPLOAD_COLS = {16, 18, 24, 28, 30}

NAVY, GREEN_D, INK, MUTED = "0B3D91", "003A00", "1F2937", "5B6778"
HEAD, GROUP, BAND = "D9E5F7", "0B3D91", "F5F8FD"
RED, GRN, AMBER = "C0262D", "1E7B34", "B26B00"
FONT = "Poppins"
BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]


def to_number(s, dec):
    s = (s or "").strip()
    if not s:
        return None
    t = s
    if dec:
        if re.fullmatch(r"-?\d+,\d+", t):
            t = t.replace(",", ".")
        elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+,\d+", t):
            t = t.replace(".", "").replace(",", ".")
        try:
            return float(t)
        except ValueError:
            return s
    try:
        return int(t)
    except ValueError:
        return s


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    header_ok = any(r[:3] == ["No", "Region", "SPBU"] for r in rows[:12] if len(r) >= 3)
    if not header_ok:
        print("PERINGATAN: susunan kolom Data_SPBU_BOA berbeda dari biasanya; periksa nama kolom di Excel.",
              file=sys.stderr)
    data = []
    for r in rows:
        r = (r + [""] * NCOL)[:NCOL]
        if re.fullmatch(r"\d+", r[0].strip()) and r[2].strip():
            data.append(r)
    periode = rows[0][0].strip() if rows and rows[0] else ""
    return data, periode


def build(rows, periode, out, title):
    wb = Workbook()
    ws = wb.active
    ws.title = "Data_SPBU_BOA"
    thin = Side(style="thin", color="9AA6B8")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    now = datetime.now(timezone(timedelta(hours=7)))

    ws["A1"] = "Data SPBU BOA I & BOA II"
    ws["A1"].font = Font(name=FONT, size=14, bold=True, color=NAVY)
    ws["A2"] = (f"Data per {periode or '-'} · {len(rows):,} SPBU · sumber: spreadsheet Report SPBU BOA "
                f"(tab Data_SPBU_BOA) · dibuat {now.day} {BULAN[now.month]} {now.year} {now:%H.%M} WIB").replace(",", ".")
    ws["A2"].font = Font(name=FONT, size=9, color=MUTED)

    # baris 3: kelompok kolom
    for name, c0, c1 in GROUPS:
        ws.merge_cells(start_row=3, start_column=c0 + 1, end_row=3, end_column=c1 + 1)
        cell = ws.cell(row=3, column=c0 + 1, value=name)
        for c in range(c0 + 1, c1 + 2):
            x = ws.cell(row=3, column=c)
            x.fill = PatternFill("solid", fgColor=GROUP)
            x.border = border
        cell.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    # baris 4: nama kolom (filter dropdown ada di baris ini)
    for i, (name, width) in enumerate(COLUMNS):
        cell = ws.cell(row=4, column=i + 1, value=name)
        cell.font = Font(name=FONT, size=9, bold=True, color=INK)
        cell.fill = PatternFill("solid", fgColor=HEAD)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
        ws.column_dimensions[get_column_letter(i + 1)].width = width
    ws.row_dimensions[3].height = 18
    ws.row_dimensions[4].height = 42

    base = Font(name=FONT, size=8, color=INK)
    fonts = {
        "red": Font(name=FONT, size=8, color=RED, bold=True),
        "grn": Font(name=FONT, size=8, color=GRN, bold=True),
        "amb": Font(name=FONT, size=8, color=AMBER),
        "upl": Font(name=FONT, size=8, color=GRN),
    }
    band = PatternFill("solid", fgColor=BAND)
    center = Alignment(horizontal="center", vertical="center")
    left = Alignment(horizontal="left", vertical="center")
    for ri, r in enumerate(rows):
        row = 5 + ri
        for ci in range(NCOL):
            v = r[ci].strip()
            if ci in NUM_INT:
                v = to_number(v, False)
            elif ci in NUM_DEC:
                v = to_number(v, True)
            cell = ws.cell(row=row, column=ci + 1, value=(v if v != "" else None))
            if isinstance(v, str) and v[:1] in ("=", "+", "-", "@"):
                cell.data_type = "s"   # tampilkan apa adanya, jangan dibaca sebagai rumus
            cell.border = border
            f = base
            if ci in RESULT_COLS and isinstance(v, str):
                f = fonts["red"] if v.lower() == "gagal" else fonts["grn"] if v.lower() in ("lolos", "pasti pas") else base
            elif ci in UPLOAD_COLS and isinstance(v, str):
                f = fonts["upl"] if v.lower() == "sudah upload" else fonts["amb"] if v.lower() == "belum upload" else base
            cell.font = f
            if ci in NUM_DEC and isinstance(v, float):
                cell.number_format = "#,##0.00"
            cell.alignment = left if ci in (3, 4, 5, 15, 17, 19, 23, 27, 29) else center
            if ri % 2:
                cell.fill = band

    last = 4 + len(rows)
    ws.auto_filter.ref = f"A4:{get_column_letter(NCOL)}{max(last, 5)}"
    ws.freeze_panes = "D5"

    # pengaturan cetak / PDF
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A3
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.print_title_rows = "3:4"
    ws.page_margins.left = ws.page_margins.right = 0.3
    ws.page_margins.top = ws.page_margins.bottom = 0.45
    ws.oddFooter.center.text = "Halaman &P dari &N"
    ws.oddFooter.center.size = 8
    ws.oddHeader.left.text = title
    ws.oddHeader.left.size = 8

    wb.properties.title = title
    wb.properties.creator = "Monitoring BOA I & BOA II"
    wb.save(out)


def main():
    src, out = sys.argv[1], sys.argv[2]
    data_json = sys.argv[3] if len(sys.argv) > 3 else None
    rows, periode = read_rows(src)
    if not rows:
        raise SystemExit("Tidak ada baris SPBU di Data_SPBU_BOA.")
    title = "Data_SPBU_BOA"
    if data_json:
        with open(data_json, encoding="utf-8") as f:
            title = json.load(f).get("detail_file_name") or title
    build(rows, periode, out, title)
    print(f"OK {out}: {len(rows)} SPBU, {NCOL} kolom, data per {periode!r}")


if __name__ == "__main__":
    main()
