#!/usr/bin/env python3
"""Buat PPT "YYYYMMDD Weekly BOA I & BOA II" dari data.json.

PPT dibuat dari nol (tanpa template berisi data), memakai gambar di assets/img.
Tiga slide: Dashboard BOA I & II, Progres BOA I, Progres BOA II.

Pemakaian:
    python scripts/build_pptx.py _site/data.json _site/unduh/weekly-boa.pptx
"""
import json
import os
import sys
import uuid

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img")
FONT = "Poppins"

NAVY = RGBColor(0x0B, 0x3D, 0x91)
GREEN = RGBColor(0x00, 0x3A, 0x00)
INK = RGBColor(0x1F, 0x29, 0x37)
MUTED = RGBColor(0x5B, 0x67, 0x78)
TILE = RGBColor(0xE6, 0xEE, 0xFB)
HEAD = RGBColor(0xD9, 0xE5, 0xF7)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CALL = RGBColor(0xF5, 0xFB, 0xFD)
RED = RGBColor(0xD7, 0x26, 0x2E)
AMBER = RGBColor(0xE8, 0x9B, 0x0C)
BLUE = RGBColor(0x0E, 0x5C, 0xC4)
GRN = RGBColor(0x2E, 0x9E, 0x44)
LINE = "000000"


# ---------------------------------------------------------------- helpers
def fmt(n):
    return f"{int(n or 0):,}".replace(",", ".")


def pct(a, b, d=1):
    return (f"{a / b * 100:.{d}f}".replace(".", ",") if b else "0") + "%"


def pct0(a, b):
    return f"{round(a / b * 100) if b else 0}%"


def img(name):
    return os.path.join(IMG, name)


def shadow(shape, alpha="22000"):
    spPr = shape._element.spPr
    for e in spPr.findall(qn("a:effectLst")):
        spPr.remove(e)
    eff = etree.SubElement(spPr, qn("a:effectLst"))
    sh = etree.SubElement(eff, qn("a:outerShdw"), blurRad="76200", dist="25400", dir="5400000", algn="t", rotWithShape="0")
    c = etree.SubElement(sh, qn("a:srgbClr"), val="000000")
    etree.SubElement(c, qn("a:alpha"), val=alpha)


def no_effect(shape):
    spPr = shape._element.spPr
    if spPr.find(qn("a:effectLst")) is None:
        etree.SubElement(spPr, qn("a:effectLst"))


def text_shadow(run):
    rPr = run._r.get_or_add_rPr()
    eff = etree.SubElement(rPr, qn("a:effectLst"))
    sh = etree.SubElement(eff, qn("a:outerShdw"), blurRad="38100", dist="38100", dir="2700000", algn="tl")
    c = etree.SubElement(sh, qn("a:srgbClr"), val="000000")
    etree.SubElement(c, qn("a:alpha"), val="43137")
    # effectLst harus sebelum latin/cs: pindahkan ke posisi setelah solidFill
    fill = rPr.find(qn("a:solidFill"))
    rPr.remove(eff)
    if fill is not None:
        fill.addnext(eff)
    else:
        rPr.insert(0, eff)


class Deck:
    def __init__(self, data):
        self.d = data
        self.prs = Presentation()
        self.prs.slide_width = Inches(20)
        self.prs.slide_height = Inches(11.25)
        self.layout = self.prs.slide_layouts[6]  # blank

    # ---- primitives on current slide
    def rrect(self, x, y, w, h, fill, name, radius=0.06, shd=False):
        s = self.s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        s.name = name
        s.adjustments[0] = radius
        s.fill.solid()
        s.fill.fore_color.rgb = fill
        s.line.fill.background()
        shadow(s) if shd else no_effect(s)
        return s

    def text(self, x, y, w, h, runs, name, size=14, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, color=INK, bold=False):
        tb = self.s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tb.name = name
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = anchor
        if isinstance(runs, str):
            runs = [[(runs, {})]]
        for i, line in enumerate(runs):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            for t, o in line:
                r = p.add_run()
                r.text = t
                f = r.font
                f.name = FONT
                f.size = Pt(o.get("size", size))
                f.bold = o.get("bold", bold)
                f.color.rgb = o.get("color", color)
        return tb

    def pic(self, name, x, y, w=None, h=None, alt=""):
        p = self.s.shapes.add_picture(img(name), Inches(x), Inches(y),
                                      Inches(w) if w else None, Inches(h) if h else None)
        p._element.nvPicPr.cNvPr.set("descr", alt)
        return p

    # ---- frame shared by all slides
    def new_slide(self, navy_word, green_word):
        self.s = self.prs.slides.add_slide(self.layout)
        self.pic("bg.jpg", 0, 0, 20, 11.25, alt="Latar")
        self.pic("logo-danantara.png", 0, 0, w=4.4, alt="Danantara Indonesia")
        self.pic("logo-pertamina.png", 15.71, 0, w=4.29, alt="Pertamina Patra Niaga")
        self.pic("energize.png", 15.2, 10.45, w=3.7, alt="Energizing Your Journey")
        self.pic("callcenter-135.png", 19.0, 10.2, w=0.9, alt="Call Center 135")

        tb = self.text(2.9, 0.42, 14.2, 1.1, [[(navy_word, {}), (" ", {}), (green_word, {})]], "Judul",
                       size=60, bold=True, align=PP_ALIGN.CENTER)
        runs = tb.text_frame.paragraphs[0].runs
        runs[0].font.color.rgb = NAVY
        runs[2].font.color.rgb = GREEN
        text_shadow(runs[0]); text_shadow(runs[2])

        per = self.text(3.0, 1.42, 14.0, 0.5, [[("Periode: ", {})]], "Periode", size=24, color=GREEN,
                        align=PP_ALIGN.CENTER)
        p = per.text_frame.paragraphs[0]._p
        r = p.findall(qn("a:r"))[-1]
        rPr = r.find(qn("a:rPr"))
        fld = etree.Element(qn("a:fld"), id="{%s}" % str(uuid.uuid4()).upper(), type="datetime3")
        f_rPr = etree.fromstring(etree.tostring(rPr)); f_rPr.set("lang", "id-ID")
        fld.append(f_rPr)
        etree.SubElement(fld, qn("a:t")).text = self.d.get("_today", "")
        r.addnext(fld)

    # ---------------------------------------------------------- dashboard
    def kpi(self, x, y, w, h, value, label, sub, color, name):
        self.rrect(x, y, w, h, TILE, name + " bg", radius=0.12)
        self.text(x + 0.2, y + 0.12, w - 0.4, 0.3, label, name + " label", size=12, color=MUTED, bold=True)
        self.text(x + 0.2, y + 0.42, w - 0.4, 0.75, value, name + " value", size=36, color=color, bold=True)
        self.text(x + 0.2, y + h - 0.42, w - 0.4, 0.3, sub, name + " sub", size=11, color=MUTED)

    def mini(self, x, y, w, value, label, color, name):
        self.text(x, y, w, 0.5, value, name + " v", size=24, color=color, bold=True, align=PP_ALIGN.CENTER)
        self.text(x, y + 0.5, w, 0.3, label, name + " l", size=11, color=MUTED, align=PP_ALIGN.CENTER)

    def chart(self, x, y, w, h, cats, series, name):
        self.text(x, y, w, 0.35, "Tindak lanjut per MOR", name + " title", size=13, bold=True)
        cd = CategoryChartData()
        cd.categories = cats
        for nm, vals, _ in series:
            cd.add_series(nm, vals)
        gf = self.s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x), Inches(y + 0.35),
                                     Inches(w), Inches(h - 0.35), cd)
        gf.name = name
        ch = gf.chart
        ch.font.name = FONT
        ch.font.size = Pt(10)
        ch.font.color.rgb = MUTED
        ch.has_legend = True
        ch.legend.position = XL_LEGEND_POSITION.TOP
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(11)
        plot = ch.plots[0]
        plot.gap_width = 60
        plot.overlap = -10
        plot.has_data_labels = True
        dl = plot.data_labels
        dl.font.size = Pt(9)
        dl.font.color.rgb = INK
        dl.number_format = "0;-0;;@"
        dl.number_format_is_linked = False
        dl.position = XL_LABEL_POSITION.OUTSIDE_END
        for s, (_, _, col) in zip(plot.series, series):
            s.format.fill.solid()
            s.format.fill.fore_color.rgb = col
        va = ch.value_axis
        va.has_major_gridlines = True
        va.major_gridlines.format.line.color.rgb = RGBColor(0xE3, 0xE7, 0xEE)
        va.major_gridlines.format.line.width = Pt(0.75)
        va.format.line.fill.background()
        va.tick_labels.font.size = Pt(10)
        ca = ch.category_axis
        ca.format.line.color.rgb = RGBColor(0xC8, 0xCF, 0xDA)
        ca.tick_labels.font.size = Pt(11)
        ca.tick_labels.font.color.rgb = INK

    def pill(self, x, y, label, fill, name):
        p = self.rrect(x, y, 1.5, 0.48, fill, name, radius=0.5)
        tf = p.text_frame
        tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        para = tf.paragraphs[0]
        para.alignment = PP_ALIGN.CENTER
        r = para.add_run()
        r.text = label
        r.font.name = FONT; r.font.size = Pt(16); r.font.bold = True; r.font.color.rgb = WHITE

    def slide_dashboard(self):
        d = self.d
        mor, t = d["rekap"]["mor"], d["rekap"]["total"]
        cats = [f"MOR {m['mor']}" for m in mor]
        ks = d.get("kso_status", {})
        b2h = (d.get("b2_hasil") or {}).get("total") or {"gagal": t["b2"]["gagal"], "pasti_pas": 0}
        hasil2 = b2h["gagal"] + b2h["pasti_pas"]
        top = max(mor, key=lambda m: m["b2"]["sbm"])
        sam = [m["mor"] for m in mor if m["b2"]["tutup"] + m["b2"]["kso"] > 0]
        if not sam:
            sam_txt = "–"
        elif len(sam) == 1:
            sam_txt = f"MOR {sam[0]}"
        elif sam == list(range(sam[0], sam[-1] + 1)):
            sam_txt = f"MOR {sam[0]}–{sam[-1]}"
        else:
            sam_txt = "MOR " + ", ".join(map(str, sam))

        self.new_slide("DASHBOARD", "BOA I & II")
        PX, PY, PW, PH, GAP = 0.6, 2.1, 9.25, 8.05, 0.3
        iw = PW - 0.7
        tw = (iw - 0.4) / 3
        ty = PY + 1.0
        sy = PY + PH - 1.45

        # BOA I
        x0 = PX + 0.35
        self.rrect(PX, PY, PW, PH, WHITE, "B1 panel", radius=0.03, shd=True)
        self.pill(x0, PY + 0.3, "BOA I", NAVY, "B1 pill")
        self.text(x0 + 1.7, PY + 0.3, iw - 1.7, 0.48, f"dari {fmt(t['total'])} SPBU wajib audit, {len(mor)} MOR",
                  "B1 caption", size=13, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)
        self.kpi(x0, ty, tw, 1.65, fmt(t["b1"]["gagal"]), "Gagal Audit BOA I", pct(t["b1"]["gagal"], t["total"]) + " dari total SPBU", RED, "B1 k1")
        self.kpi(x0 + tw + 0.2, ty, tw, 1.65, fmt(t["b1"]["sp"]), "Surat Peringatan", pct(t["b1"]["sp"], t["b1"]["gagal"]) + " sudah upload", AMBER, "B1 k2")
        self.kpi(x0 + 2 * (tw + 0.2), ty, tw, 1.65, fmt(t["b1"]["sbm"]), "Coaching SBM", pct(t["b1"]["sbm"], t["b1"]["gagal"]) + " sudah upload", BLUE, "B1 k3")
        self.chart(x0, ty + 1.9, iw, 3.55, cats, [
            ("Gagal", [m["b1"]["gagal"] for m in mor], RED),
            ("Surat Peringatan", [m["b1"]["sp"] for m in mor], AMBER),
            ("Coaching SBM", [m["b1"]["sbm"] for m in mor], BLUE)], "B1 chart")
        self.rrect(x0, sy, iw, 1.15, TILE, "B1 kso bg", radius=0.12)
        self.text(x0 + 0.25, sy, 2.0, 1.15, [[("Pertare", {"bold": True, "size": 14})], [("Hasil Nego KSO", {"size": 11, "color": MUTED})]],
                  "B1 kso label", anchor=MSO_ANCHOR.MIDDLE)
        mw = (iw - 2.3) / 5
        items = [("Setuju KSO", ks.get("Setuju KSO", t["b1"]["kso_setuju"]), GRN),
                 ("Negosiasi", ks.get("Negosiasi", 0), AMBER),
                 ("Gagal KSO", ks.get("Gagal KSO", t["b1"]["kso_gagal"]), RED),
                 ("Operasional", ks.get("Operasional", t["b1"]["kso_ops"]), BLUE),
                 ("SPBU Tutup", ks.get("SPBU Tutup", 0), MUTED)]
        for i, (lab, v, col) in enumerate(items):
            self.mini(x0 + 2.2 + i * mw, sy + 0.15, mw, fmt(v), lab, col, f"B1 m{i + 1}")

        # BOA II
        x0 = PX + PW + GAP + 0.35
        self.rrect(PX + PW + GAP, PY, PW, PH, WHITE, "B2 panel", radius=0.03, shd=True)
        self.pill(x0, PY + 0.3, "BOA II", GREEN, "B2 pill")
        self.text(x0 + 1.7, PY + 0.3, iw - 1.7, 0.48,
                  f"{fmt(hasil2)} hasil audit: {fmt(b2h['pasti_pas'])} Pasti Pas, {fmt(b2h['gagal'])} Gagal",
                  "B2 caption", size=13, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)
        sub1 = pct(b2h["gagal"], hasil2, 0) + " dari hasil audit" if hasil2 else pct(t["b2"]["gagal"], t["total"]) + " dari total SPBU"
        self.kpi(x0, ty, tw, 1.65, fmt(t["b2"]["gagal"]), "Gagal Audit BOA II", sub1, RED, "B2 k1")
        self.kpi(x0 + tw + 0.2, ty, tw, 1.65, fmt(t["b2"]["sp"]), "Surat Peringatan", pct(t["b2"]["sp"], t["b2"]["gagal"]) + " dari SPBU gagal", AMBER, "B2 k2")
        self.kpi(x0 + 2 * (tw + 0.2), ty, tw, 1.65, fmt(t["b2"]["sbm"]), "Coaching SBM",
                 f"{fmt(top['b2']['sbm'])} di antaranya MOR {top['mor']}" if top["b2"]["sbm"] else "–", BLUE, "B2 k3")
        self.chart(x0, ty + 1.9, iw, 3.55, cats, [
            ("Gagal", [m["b2"]["gagal"] for m in mor], RED),
            ("Surat Peringatan", [m["b2"]["sp"] for m in mor], AMBER),
            ("Coaching SBM", [m["b2"]["sbm"] for m in mor], BLUE)], "B2 chart")
        self.rrect(x0, sy, iw, 1.15, TILE, "B2 sam bg", radius=0.12)
        self.text(x0 + 0.25, sy, 2.3, 1.15, [[("SAM", {"bold": True, "size": 14})], [("Tindakan lanjutan", {"size": 11, "color": MUTED})]],
                  "B2 sam label", anchor=MSO_ANCHOR.MIDDLE)
        mw2 = (iw - 2.6) / 3
        self.mini(x0 + 2.5, sy + 0.15, mw2, fmt(t["b2"]["tutup"]), "Tutup/Pembinaan", AMBER, "B2 m1")
        self.mini(x0 + 2.5 + mw2, sy + 0.15, mw2, fmt(t["b2"]["kso"]), "KSO Mandatory", NAVY, "B2 m2")
        self.mini(x0 + 2.5 + 2 * mw2, sy + 0.15, mw2, sam_txt, "Asal seluruh kasus", MUTED, "B2 m3")

    # ---------------------------------------------------------- tables
    def table(self, x, y, col_px, row_h, header, body, foot, merges, icons, name):
        tw = 18.26
        scale = tw / sum(col_px)
        widths = [c * scale for c in col_px]
        rows = len(header) + len(body) + 1
        gf = self.s.shapes.add_table(rows, len(widths), Inches(x), Inches(y), Inches(tw), Inches(sum(row_h)))
        gf.name = name
        tbl = gf.table
        tblPr = tbl._tbl.tblPr
        for a in ("firstRow", "bandRow"):
            tblPr.set(a, "0")
        sid = tblPr.find(qn("a:tableStyleId"))
        if sid is None:
            sid = etree.SubElement(tblPr, qn("a:tableStyleId"))
        sid.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"  # No Style, Table Grid
        for i, w in enumerate(widths):
            tbl.columns[i].width = Inches(w)
        for i, h in enumerate(row_h):
            tbl.rows[i].height = Inches(h)

        def setc(r, c, txt, bold, fill, size, top=0.0, anchor=MSO_ANCHOR.MIDDLE):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = fill
            cell.vertical_anchor = anchor
            cell.margin_left = cell.margin_right = Inches(0.04)
            cell.margin_top = Inches(top)
            cell.margin_bottom = Inches(0.03)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            for ln_i, line in enumerate(str(txt).split("\n")):
                if ln_i:
                    p = tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER
                run = p.add_run()
                run.text = line
                run.font.name = FONT; run.font.size = Pt(size); run.font.bold = bold; run.font.color.rgb = RGBColor(0, 0, 0)
            tcPr = cell._tc.get_or_add_tcPr()
            for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
                ln = etree.SubElement(tcPr, qn(tag), w="12700")
                sf = etree.SubElement(ln, qn("a:solidFill"))
                etree.SubElement(sf, qn("a:srgbClr"), val=LINE)
            # elemen garis harus sebelum fill di tcPr
            fill_el = tcPr.find(qn("a:solidFill"))
            if fill_el is not None:
                tcPr.remove(fill_el); tcPr.append(fill_el)

        for (r0, c0, r1, c1) in merges:
            tbl.cell(r0, c0).merge(tbl.cell(r1, c1))
        for r, row in enumerate(header):
            for c, cell in enumerate(row):
                if cell is None:
                    continue
                txt, top = cell if isinstance(cell, tuple) else (cell, 0.0)
                setc(r, c, txt, True, HEAD, 16, top, MSO_ANCHOR.BOTTOM if top else MSO_ANCHOR.MIDDLE)
        base = len(header)
        for i, row in enumerate(body):
            for c, v in enumerate(row):
                setc(base + i, c, v, False, WHITE, 17)
        for c, v in enumerate(foot):
            setc(rows - 1, c, v, True, HEAD, 17)
        # ikon di header
        xs = [x]
        for w in widths:
            xs.append(xs[-1] + w)
        for (c0, c1, file, ih, iy) in icons:
            cx = (xs[c0] + xs[c1 + 1]) / 2
            p = self.pic(file, 0, y + iy, h=ih)
            p.left = int(Inches(cx) - p.width / 2)

    def callout(self, lines, name):
        box = self.rrect(1.71, 8.95, 16.61, 1.42, CALL, name + " box", radius=0.19, shd=True)
        tear = self.s.shapes.add_shape(MSO_SHAPE.TEAR, Inches(4.25), Inches(9.28), Inches(0.76), Inches(0.78))
        tear.name = name + " mark"
        tear.rotation = 136
        tear.fill.solid(); tear.fill.fore_color.rgb = NAVY
        tear.line.fill.background(); no_effect(tear)
        self.text(4.25, 9.28, 0.76, 0.78, "!", name + " !", size=30, bold=True, color=WHITE,
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        tb = self.text(5.2, 8.95, 12.3, 1.42, lines, name + " text", size=16, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        return box, tb

    def slide_boa1(self):
        mor, t = self.d["rekap"]["mor"], self.d["rekap"]["total"]
        self.new_slide("PROGRES", "BOA I")
        self.rrect(0.67, 2.32, 18.66, 6.42, WHITE, "Kartu tabel", radius=0.03, shd=True)
        header = [
            [("MOR", 0.01), ("Total SPBU", 0.01), ("CI", 0.6), ("FCA/SA", 0.6), None, ("SBM", 0.6), None, ("Pertare", 0.6), None, None],
            [None, None, "Hasil Audit BOA I", "Surat Peringatan (BOA I)", None, "Coaching SBM (BOA I)", None, "Hasil Nego KSO", None, None],
            [None, None, "Gagal", "Sudah Upload", None, "Sudah Upload", None, "Setuju KSO", "Gagal", "Operasional"],
        ]
        # sel kosong untuk kolom % (ikon saja)
        header[0][4] = ""; header[0][6] = ""
        merges = [(0, 0, 2, 0), (0, 1, 2, 1), (0, 4, 2, 4), (0, 6, 2, 6), (0, 7, 0, 9), (1, 7, 1, 9)]
        body = [[m["mor"], fmt(m["total"]), fmt(m["b1"]["gagal"]), fmt(m["b1"]["sp"]), pct0(m["b1"]["sp"], m["b1"]["gagal"]),
                 fmt(m["b1"]["sbm"]), pct0(m["b1"]["sbm"], m["b1"]["gagal"]), fmt(m["b1"]["kso_setuju"]),
                 fmt(m["b1"]["kso_gagal"]), fmt(m["b1"]["kso_ops"])] for m in mor]
        foot = ["Total", fmt(t["total"]), fmt(t["b1"]["gagal"]), fmt(t["b1"]["sp"]),
                t["b1"].get("sp_pct") or pct(t["b1"]["sp"], t["b1"]["gagal"], 2), fmt(t["b1"]["sbm"]),
                t["b1"].get("sbm_pct") or pct0(t["b1"]["sbm"], t["b1"]["gagal"]),
                fmt(t["b1"]["kso_setuju"]), fmt(t["b1"]["kso_gagal"]), fmt(t["b1"]["kso_ops"])]
        icons = [(0, 0, "icon-mor.png", 0.6, 0.12), (1, 1, "icon-spbu.png", 0.6, 0.12), (2, 2, "icon-ci.png", 0.5, 0.07),
                 (3, 3, "icon-fca.png", 0.5, 0.07), (4, 4, "icon-pct.png", 0.85, 0.7), (5, 5, "icon-sbm.png", 0.5, 0.07),
                 (6, 6, "icon-pct.png", 0.85, 0.7), (7, 9, "icon-kso.png", 0.5, 0.07)]
        self.table(0.87, 2.5, [80, 127, 141, 211, 112, 270, 106, 136, 122, 162],
                   [0.95, 0.7, 0.58] + [0.42] * 9, header, body, foot, merges, icons, "Tabel BOA I")
        B = {"bold": True}
        self.callout([
            [("Dari ", {}), (f"{fmt(t['total'])} SPBU", B), (", sebanyak ", {}), (f"{fmt(t['b1']['gagal'])} SPBU", B),
             (" tercatat Gagal ", {}), ("Audit BOA I", B), (".", {})],
            [("Terdapat ", {}), (f"{fmt(t['b1']['sp'])} SPBU ({t['b1'].get('sp_pct') or pct(t['b1']['sp'], t['b1']['gagal'], 2)})", B),
             (" yang memerlukan tindak lanjut ", {}), ("FCA/Surat Peringatan", B), (".", {})],
            [("Coaching SBM telah dilakukan pada ", {}),
             (f"{fmt(t['b1']['sbm'])} SPBU ({t['b1'].get('sbm_pct') or pct0(t['b1']['sbm'], t['b1']['gagal'])})", B),
             (" dari total SPBU gagal BOA I.", {})],
        ], "Keterangan")

    def slide_boa2(self):
        mor, t = self.d["rekap"]["mor"], self.d["rekap"]["total"]
        self.new_slide("PROGRES", "BOA II")
        self.rrect(0.67, 2.32, 18.66, 6.42, WHITE, "Kartu tabel", radius=0.03, shd=True)
        header = [
            [("MOR", 0.01), ("Total SPBU", 0.01), ("CI", 0.6), None, ("FCA/SA", 0.6), ("SBM", 0.6), ("SAM", 0.6), None],
            [None, None, "Hasil Audit BOA II", None, "Surat Peringatan (BOA II)", "Coaching SBM (BOA II)", "Tutup/\nPembinaan", "KSO\nMandatory"],
            [None, None, "Lolos", "Gagal", "Sudah Upload", "Sudah Upload", None, None],
        ]
        merges = [(0, 0, 2, 0), (0, 1, 2, 1), (0, 2, 0, 3), (1, 2, 1, 3), (0, 6, 0, 7), (1, 6, 2, 6), (1, 7, 2, 7)]
        body = [[m["mor"], fmt(m["total"]), fmt(m["b2"]["lolos"]), fmt(m["b2"]["gagal"]), fmt(m["b2"]["sp"]),
                 fmt(m["b2"]["sbm"]), fmt(m["b2"]["tutup"]), fmt(m["b2"]["kso"])] for m in mor]
        foot = ["Total", fmt(t["total"]), fmt(t["b2"]["lolos"]), fmt(t["b2"]["gagal"]), fmt(t["b2"]["sp"]),
                fmt(t["b2"]["sbm"]), fmt(t["b2"]["tutup"]), fmt(t["b2"]["kso"])]
        icons = [(0, 0, "icon-mor.png", 0.6, 0.12), (1, 1, "icon-spbu.png", 0.6, 0.12), (2, 3, "icon-ci.png", 0.5, 0.07),
                 (4, 4, "icon-fca.png", 0.5, 0.07), (5, 5, "icon-sbm.png", 0.5, 0.07), (6, 7, "icon-sam.png", 0.5, 0.07)]
        self.table(0.87, 2.5, [100, 112, 130, 129, 313, 267, 162, 176],
                   [0.95, 0.7, 0.58] + [0.42] * 9, header, body, foot, merges, icons, "Tabel BOA II")
        B = {"bold": True}
        self.callout([
            [("Terdapat ", {}), (f"{fmt(t['b2']['gagal'])} SPBU Gagal BOA II", B), ("; ", {}), (f"{fmt(t['b2']['sp'])} SPBU", B),
             (" sudah mendapatkan ", {}), ("Surat Peringatan/FCA.", B)],
            [(f"{fmt(t['b2']['sbm'])} SPBU", B), (" telah mendapatkan ", {}), ("Coaching SBM – BOA II.", B)],
            [("Terdapat ", {}), (f"{fmt(t['b2']['tutup'])} SPBU", B), (" yang melakukan ", {}), ("Pembinaan", B),
             (" dan ", {}), (f"{fmt(t['b2']['kso'])} KSO Mandatory.", B)],
        ], "Keterangan")

    def slide_top_tier(self):
        tt = self.d.get("top_tier")
        if not tt:
            return False
        mor, t = tt["mor"], tt["total"]
        keys = ["total", "belum_web", "verif_pttr", "verif_kso_region", "verif_kso_pusat", "penerbitan_ba", "penerbitan_sp_sh"]
        self.new_slide("PROGRES", "TOP TIER")
        self.rrect(0.67, 2.32, 18.66, 6.42, WHITE, "Kartu tabel", radius=0.03, shd=True)
        header = [
            [("MOR", 0.01), ("Total SPBU Top Tier", 0.01), ("TOP TIER", 0.6), None, None, None, None, None],
            [None, None, "Progress Web DDMS", None, None, None, None, None],
            [None, None, "Belum ada di web", "Verifikasi PTTR", "Verifikasi KSO Region", "Verifikasi KSO Pusat",
             "Penerbitan BA", "Penerbitan SP SH"],
        ]
        merges = [(0, 0, 2, 0), (0, 1, 2, 1), (0, 2, 0, 7), (1, 2, 1, 7)]
        body = [[m["mor"]] + [fmt(m[k]) for k in keys] for m in mor]
        foot = ["Total"] + [fmt(t[k]) for k in keys]
        icons = [(0, 0, "icon-mor.png", 0.6, 0.12), (1, 1, "icon-spbu.png", 0.6, 0.12), (2, 7, "icon-ci.png", 0.5, 0.07)]
        self.table(0.87, 2.5, [100, 170, 160, 160, 170, 170, 150, 160],
                   [0.95, 0.7, 0.58] + [0.42] * 9, header, body, foot, merges, icons, "Tabel Top Tier")
        B = {"bold": True}
        top = max(mor, key=lambda m: m["total"])
        stages = [("verif_pttr", "Verifikasi PTTR"), ("verif_kso_region", "Verifikasi KSO Region"),
                  ("verif_kso_pusat", "Verifikasi KSO Pusat"), ("penerbitan_ba", "Penerbitan BA"),
                  ("penerbitan_sp_sh", "Penerbitan SP SH")]
        progressed = [(lab, t[k]) for k, lab in stages if t[k]]
        line3 = ([("Belum ada SPBU pada tahap ", {}), ("Verifikasi PTTR, Verifikasi KSO, Penerbitan BA", B),
                  (" maupun ", {}), ("Penerbitan SP SH.", B)] if not progressed else
                 [("Sudah berproses: ", {})] + sum([[(f"{lab} {fmt(v)}", B), (", " if i < len(progressed) - 1 else ".", {})]
                                                     for i, (lab, v) in enumerate(progressed)], []))
        self.callout([
            [("Terdapat ", {}), (f"{fmt(t['total'])} SPBU Top Tier", B), (", terbanyak di ", {}),
             (f"MOR {top['mor']} ({fmt(top['total'])} SPBU)", B), (".", {})],
            [(f"{fmt(t['belum_web'])} SPBU", B), (" belum ada di ", {}), ("web DDMS", B), (".", {})],
            line3,
        ], "Keterangan")
        return True

    def save(self, path, title):
        self.prs.core_properties.title = title
        self.prs.core_properties.author = "Monitoring BOA I & BOA II"
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.prs.save(path)


def main():
    data_path, out = sys.argv[1], sys.argv[2]
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    data["_today"] = data.get("tanggal_build", "")
    deck = Deck(data)
    deck.slide_dashboard()
    deck.slide_boa1()
    deck.slide_boa2()
    deck.slide_top_tier()
    title = data.get("file_name") or "Weekly BOA I & BOA II"
    deck.save(out, title)
    print(f"OK {out} ({title})")


if __name__ == "__main__":
    main()
