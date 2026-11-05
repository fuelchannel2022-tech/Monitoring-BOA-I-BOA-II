#!/usr/bin/env python3
"""Bandingkan data.json baru dengan data.json yang sedang tayang di GitHub Pages.

Menulis `changed=true|false` ke GITHUB_OUTPUT. Deploy hanya dijalankan jika
angka di spreadsheet berubah (waktu sinkron `generated_at` diabaikan), atau
jika FORCE=true (push ke main / Run workflow manual).

Pemakaian:
    python scripts/compare_data.py _site/data.json https://<user>.github.io/<repo>/data.json
"""
import json
import os
import sys
import time
import urllib.request

IGNORE = {"generated_at"}


def strip(d):
    return {k: v for k, v in d.items() if k not in IGNORE}


def main():
    new_path, site_url = sys.argv[1], sys.argv[2]
    with open(new_path, encoding="utf-8") as f:
        new = strip(json.load(f))

    force = os.environ.get("FORCE", "").lower() == "true"
    try:
        url = f"{site_url}?t={int(time.time())}"  # lewati cache CDN
        req = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "boa-dashboard-builder"})
        with urllib.request.urlopen(req, timeout=30) as r:
            old = strip(json.loads(r.read().decode("utf-8")))
    except Exception as e:  # situs belum ada / tidak bisa dibaca -> anggap berubah
        print(f"Data yang tayang tidak terbaca ({e.__class__.__name__}); deploy ulang.")
        old = None

    changed = force or old != new
    if force:
        print("Deploy dipaksa (push atau Run workflow manual).")
    elif old is None:
        pass
    elif old == new:
        print("Tidak ada perubahan data di spreadsheet; deploy dilewati.")
    else:
        print("Data spreadsheet berubah; website akan diperbarui.")

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")
    else:
        print(f"changed={'true' if changed else 'false'}")


if __name__ == "__main__":
    main()
