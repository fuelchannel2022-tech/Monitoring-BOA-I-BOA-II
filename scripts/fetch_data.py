#!/usr/bin/env python3
"""Ambil rekap BOA I & BOA II dari Google Sheet lalu tulis data.json.

Dijalankan oleh GitHub Actions saat deploy. Data TIDAK disimpan di repository:
data.json hanya ikut ke paket website yang di-deploy ke GitHub Pages.

ID spreadsheet dibaca dari environment variable SHEET_ID (GitHub Secret),
supaya spreadsheet detail per SPBU tidak terbuka di repository publik.

Spreadsheet harus dibagikan "Anyone with the link can view".

SHEET_ID boleh berisi ID saja atau link lengkap spreadsheet; ID-nya diambil otomatis.

Pemakaian:
    SHEET_ID=xxxx python scripts/fetch_data.py _site/data.json
"""
import csv
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# gid (ID tab) — bukan rahasia, tanpa SHEET_ID tidak bisa dipakai.
GID_REKAP = os.environ.get("GID_REKAP", "1381812318")    # tab "Rekap All Region"
GID_DETAIL = os.environ.get("GID_DETAIL", "871452310")   # tab "Data_SPBU_BOA"
RANGE_REKAP = os.environ.get("RANGE_REKAP", "A1:P13")    # blok rekap BOA I & BOA II
MORS = [str(i) for i in range(1, 9)]
BASE = "https://docs.google.com/spreadsheets/d/"

# kolom tab Data_SPBU_BOA (0 = kolom A)
COL_NO, COL_MOR, COL_KSO, COL_BOA2 = 0, 1, 20, 25   # A, B, U, Z


class FetchError(Exception):
    pass


def normalize_sheet_id(raw):
    """Terima ID saja atau link lengkap; buang spasi, tanda kutip, dan '/edit...'."""
    text = (raw or "").strip()
    m = re.search(r"/d/([A-Za-z0-9_-]{25,})", "/" + text)   # pola link: .../d/<ID>/edit
    if m:
        s = m.group(1)
    else:  # teks lain: ambil potongan terpanjang yang berbentuk ID spreadsheet
        tokens = re.findall(r"[A-Za-z0-9_-]{25,}", text)
        s = max(tokens, key=len) if tokens else ""
    if not s and re.search(r"github\.io|github\.com", text, re.I):
        raise SystemExit(
            "SHEET_ID berisi alamat GitHub (website/repository), bukan link Google Sheets. "
            "Ganti isi Secret SHEET_ID dengan ID spreadsheet: teks di antara '/d/' dan '/edit' "
            "pada link docs.google.com/spreadsheets/d/.../edit."
        )
    if not s:
        pola = re.sub(r"[A-Za-z0-9_-]{6,}", "<teks>", text)[:80]
        raise SystemExit(
            "SHEET_ID tidak valid. Isi Secret SHEET_ID dengan ID spreadsheet "
            "(teks di antara '/d/' dan '/edit' pada link) atau link lengkapnya. "
            f"(panjang isi Secret: {len(text)} karakter, pola: {pola!r})"
        )
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::add-mask::{s}")  # sembunyikan ID di log Actions
    if s != (raw or "").strip():
        print("Info: SHEET_ID berisi link/teks tambahan; ID spreadsheet diambil otomatis.")
    return s


def http_get(url, what):
    """GET dengan retry. Pesan error tidak mencantumkan URL (berisi ID spreadsheet)."""
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (boa-dashboard-builder)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read().decode("utf-8-sig")
            if body.lstrip().startswith("<"):
                raise FetchError(f"{what}: Google mengembalikan halaman HTML (kemungkinan login), bukan data. "
                                 "Pastikan spreadsheet dibagikan 'Anyone with the link can view'.")
            return body
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            hint = {
                400: "permintaan ditolak (cek GID/range tab)",
                401: "spreadsheet tidak dibagikan publik lewat link",
                403: "akses ditolak (cek setelan berbagi spreadsheet)",
                404: "spreadsheet/tab tidak ditemukan (cek isi Secret SHEET_ID dan GID tab)",
            }.get(e.code, "kesalahan dari server Google")
            last = FetchError(f"{what}: HTTP {e.code} — {hint}.")
            break
        except urllib.error.URLError as e:
            last = FetchError(f"{what}: koneksi gagal ({e.reason}).")
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
    raise last


def gviz_csv(sheet_id, gid, what, **params):
    q = {"tqx": "out:csv", "gid": gid, "headers": "0"}
    q.update(params)
    body = http_get(f"{BASE}{sheet_id}/gviz/tq?" + urllib.parse.urlencode(q), what + " (gviz)")
    return list(csv.reader(io.StringIO(body)))


def export_csv(sheet_id, gid, what, **params):
    q = {"format": "csv", "gid": gid}
    q.update(params)
    body = http_get(f"{BASE}{sheet_id}/export?" + urllib.parse.urlencode(q), what + " (export)")
    return list(csv.reader(io.StringIO(body)))


def fetch(primary, fallback, what):
    """Coba endpoint utama; jika gagal, pakai endpoint cadangan."""
    try:
        return primary()
    except FetchError as e:
        print(f"PERINGATAN: {e} Mencoba endpoint cadangan…", file=sys.stderr)
        try:
            return fallback()
        except FetchError as e2:
            raise SystemExit(f"GAGAL mengambil {what}.\n- {e}\n- {e2}")


def to_int(s):
    s = (s or "").strip()
    if not s:
        return 0
    if re.fullmatch(r"-?\d{1,3}([.,]\d{3})+", s):  # contoh: 1,234 atau 1.234
        return int(re.sub(r"[.,]", "", s))
    try:
        return int(round(float(s.replace(",", "."))))
    except ValueError:
        return 0


def pct_text(s):
    s = (s or "").strip()
    return s.replace(".", ",") if s else ""


def parse_rekap(rows):
    mor, total = [], None
    for r in rows:
        r = (r + [""] * 16)[:16]
        a, b = r[0].strip(), r[1].strip()
        if not b or not any(ch.isdigit() for ch in b):
            continue
        rec = {
            "total": to_int(r[1]),
            "b1": {
                "gagal": to_int(r[2]), "sp": to_int(r[3]), "sp_pct": pct_text(r[4]),
                "sbm": to_int(r[5]), "sbm_pct": pct_text(r[6]),
                "kso_setuju": to_int(r[7]), "kso_gagal": to_int(r[8]), "kso_ops": to_int(r[9]),
            },
            "b2": {
                "lolos": to_int(r[10]), "gagal": to_int(r[11]), "sp": to_int(r[12]),
                "sbm": to_int(r[13]), "tutup": to_int(r[14]), "kso": to_int(r[15]),
            },
        }
        if a in MORS:
            rec["mor"] = int(a)
            mor.append(rec)
        elif a == "" or a.lower() == "total":
            total = rec
    if len(mor) != 8 or total is None:
        raise SystemExit(f"Format tab Rekap All Region berubah: ditemukan {len(mor)} baris MOR, total={'ada' if total else 'tidak ada'}.")
    # cek konsistensi
    for key in ("gagal", "sp", "sbm"):
        s = sum(m["b1"][key] for m in mor)
        if s != total["b1"][key]:
            print(f"PERINGATAN: total BOA I {key} = {total['b1'][key]}, jumlah per MOR = {s}", file=sys.stderr)
    return {"mor": sorted(mor, key=lambda m: m["mor"]), "total": total}


def parse_pivot(rows):
    """Hasil query 'select B, count(B) ... group by B pivot X' -> {label: {mor: n}}"""
    if not rows:
        return {}
    header = rows[0]
    out = {}
    for r in rows[1:]:
        if not r or r[0].strip() not in MORS:
            continue
        m = int(r[0])
        for i, label in enumerate(header[2:], start=2):
            label = label.strip()
            if not label:
                continue
            out.setdefault(label, {})[m] = to_int(r[i]) if i < len(r) else 0
    return out


def pivot_from_rows(rows, col):
    """Hitung jumlah per MOR untuk setiap nilai di kolom `col` dari isi tab Data_SPBU_BOA."""
    out = {}
    for r in rows:
        if len(r) <= max(COL_MOR, col) or not r[COL_NO].strip():
            continue
        m = r[COL_MOR].strip()
        label = r[col].strip()
        if m not in MORS or not label:
            continue
        d = out.setdefault(label, {})
        d[int(m)] = d.get(int(m), 0) + 1
    return out


def main():
    raw = os.environ.get("SHEET_ID", "")
    if not raw.strip():
        raise SystemExit("SHEET_ID belum diisi. Tambahkan di Settings > Secrets and variables > Actions.")
    sheet_id = normalize_sheet_id(raw)
    out_path = sys.argv[1] if len(sys.argv) > 1 else "data.json"

    rekap = parse_rekap(fetch(
        lambda: gviz_csv(sheet_id, GID_REKAP, "Rekap All Region", range=RANGE_REKAP),
        lambda: export_csv(sheet_id, GID_REKAP, "Rekap All Region", range=RANGE_REKAP),
        "tab Rekap All Region",
    ))

    q_base = "select B, count(B) where A is not null group by B pivot "
    detail_rows = None

    def detail():
        nonlocal detail_rows
        if detail_rows is None:
            detail_rows = export_csv(sheet_id, GID_DETAIL, "Data_SPBU_BOA")
        return detail_rows

    kso = fetch(  # Hasil Nego KSO (kolom U)
        lambda: parse_pivot(gviz_csv(sheet_id, GID_DETAIL, "Data_SPBU_BOA", tq=q_base + "U")),
        lambda: pivot_from_rows(detail(), COL_KSO),
        "Hasil Nego KSO (Data_SPBU_BOA kolom U)",
    )
    hasil2 = fetch(  # Hasil Audit BOA II (kolom Z)
        lambda: parse_pivot(gviz_csv(sheet_id, GID_DETAIL, "Data_SPBU_BOA", tq=q_base + "Z")),
        lambda: pivot_from_rows(detail(), COL_BOA2),
        "Hasil Audit BOA II (Data_SPBU_BOA kolom Z)",
    )

    periode = ""
    try:
        cell = detail_rows if detail_rows is not None else gviz_csv(sheet_id, GID_DETAIL, "Tanggal data", range="A1:B2")
        periode = cell[0][0].strip() if cell and cell[0] else ""
    except FetchError as e:  # tanggal tidak wajib
        print(f"PERINGATAN: tanggal periode tidak terbaca ({e})", file=sys.stderr)

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "periode_sheet": periode,
        "rekap": rekap,
        "kso_status": {k: sum(v.values()) for k, v in kso.items()},
        "b2_hasil": {
            "per_mor": [
                {"mor": m, "gagal": hasil2.get("Gagal", {}).get(m, 0), "pasti_pas": hasil2.get("Pasti Pas", {}).get(m, 0)}
                for m in range(1, 9)
            ],
        },
    }
    data["b2_hasil"]["total"] = {
        "gagal": sum(x["gagal"] for x in data["b2_hasil"]["per_mor"]),
        "pasti_pas": sum(x["pasti_pas"] for x in data["b2_hasil"]["per_mor"]),
    }
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    t = rekap["total"]
    print(f"OK periode={periode!r} total SPBU={t['total']} gagal BOA I={t['b1']['gagal']} gagal BOA II={t['b2']['gagal']}")


if __name__ == "__main__":
    main()
