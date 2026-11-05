#!/usr/bin/env python3
"""Ambil rekap BOA I & BOA II dari Google Sheet lalu tulis data.json.

Dijalankan oleh GitHub Actions saat deploy. Data TIDAK disimpan di repository:
data.json hanya ikut ke paket website yang di-deploy ke GitHub Pages.

ID spreadsheet dibaca dari environment variable SHEET_ID (GitHub Secret),
supaya spreadsheet detail per SPBU tidak terbuka di repository publik.

Spreadsheet harus dibagikan "Anyone with the link can view".

Pemakaian:
    SHEET_ID=xxxx python scripts/fetch_data.py _site/data.json
"""
import csv
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# gid (ID tab) — bukan rahasia, tanpa SHEET_ID tidak bisa dipakai.
GID_REKAP = os.environ.get("GID_REKAP", "1381812318")    # tab "Rekap All Region"
GID_DETAIL = os.environ.get("GID_DETAIL", "871452310")   # tab "Data_SPBU_BOA"
RANGE_REKAP = os.environ.get("RANGE_REKAP", "A1:P13")    # blok rekap BOA I & BOA II
MORS = [str(i) for i in range(1, 9)]


def gviz_csv(sheet_id, gid, **params):
    q = {"tqx": "out:csv", "gid": gid, "headers": "0"}
    q.update(params)
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": "boa-dashboard-builder"})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode("utf-8")
    if body.lstrip().startswith("<"):
        raise SystemExit(
            "Spreadsheet tidak bisa dibaca. Pastikan SHEET_ID benar dan spreadsheet "
            "dibagikan 'Anyone with the link can view'."
        )
    return list(csv.reader(io.StringIO(body)))


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


def main():
    sheet_id = os.environ.get("SHEET_ID", "").strip()
    if not sheet_id:
        raise SystemExit("SHEET_ID belum diisi. Tambahkan di Settings > Secrets and variables > Actions.")
    out_path = sys.argv[1] if len(sys.argv) > 1 else "data.json"

    rekap = parse_rekap(gviz_csv(sheet_id, GID_REKAP, range=RANGE_REKAP))

    q_base = "select B, count(B) where A is not null group by B pivot "
    kso = parse_pivot(gviz_csv(sheet_id, GID_DETAIL, tq=q_base + "U"))   # Hasil Nego KSO
    hasil2 = parse_pivot(gviz_csv(sheet_id, GID_DETAIL, tq=q_base + "Z"))  # Hasil Audit BOA II

    periode = ""
    try:
        cell = gviz_csv(sheet_id, GID_DETAIL, range="A1:B2")
        periode = cell[0][0].strip() if cell and cell[0] else ""
    except Exception as e:  # tanggal tidak wajib
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
