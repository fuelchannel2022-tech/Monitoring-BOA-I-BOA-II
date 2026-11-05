# Monitoring BOA I & BOA II

Dashboard Monitoring BOA I &amp; BOA II - Channel Development.

Website statis (HTML, CSS, JavaScript tanpa library eksternal) yang dipublikasikan dengan GitHub Pages. Isinya tiga halaman:

- **Dashboard**: ringkasan BOA I dan BOA II, angka utama, grafik per MOR, status Pertare (Hasil Nego KSO) dan SAM.
- **Progres BOA I**: tabel per MOR.
- **Progres BOA II**: tabel per MOR.

## Data dan kerahasiaan

- Repository ini **tidak menyimpan data apa pun**. Angka diambil dari Google Sheet oleh GitHub Actions saat deploy, lalu disimpan sebagai `data.json` di dalam paket website. File itu tidak pernah di-commit (lihat `.gitignore`).
- ID spreadsheet disimpan sebagai **GitHub Secret** `SHEET_ID`, bukan di kode, supaya spreadsheet detail per SPBU tidak bisa ditemukan dari repository.
- Website hanya menampilkan **angka rekap per MOR**. Tidak ada data per SPBU, alamat, omzet, atau nama mitra.
- ⚠️ Website GitHub Pages dari akun gratis **bisa dibuka siapa saja yang tahu alamatnya**. Halaman ini memakai `noindex` agar tidak muncul di mesin pencari, tetapi tetap bukan halaman privat.

## Cara mengaktifkan (sekali saja)

1. **Simpan ID spreadsheet sebagai Secret.** Buka *Settings → Secrets and variables → Actions → New repository secret*.
   - Name: `SHEET_ID`
   - Secret: bagian ID dari link spreadsheet, yaitu teks di antara `/d/` dan `/edit`.
2. **Aktifkan GitHub Pages.** Buka *Settings → Pages → Build and deployment → Source* dan pilih **GitHub Actions**.
3. **Jalankan deploy pertama.** Buka *Actions → Deploy dashboard → Run workflow*.
4. Setelah selesai, website ada di
   `https://fuelchannel2022-tech.github.io/Monitoring-BOA-I-BOA-II/`

Spreadsheet harus dibagikan **"Anyone with the link can view"** agar GitHub Actions bisa membacanya.

## Pembaruan data

- **Otomatis setiap ada perubahan:** setiap 10 menit GitHub Actions membaca spreadsheet dan membandingkannya dengan data yang sedang tayang. Website hanya di-deploy ulang kalau ada angka yang berubah, sekecil apa pun. Kalau tidak ada perubahan, deploy dilewati.
- **Halaman yang sedang terbuka** memeriksa data baru setiap 2 menit (dan saat tab dibuka kembali), lalu memperbarui angka tanpa perlu di-refresh.
- **Manual:** *Actions → Deploy dashboard → Run workflow* (selalu deploy).
- **Saat ada perubahan kode:** setiap push ke branch `main` juga memicu deploy.
- **Jeda:** perubahan di spreadsheet biasanya tampil di website dalam ±10–20 menit. Jadwal GitHub Actions kadang terlambat beberapa menit saat server GitHub sedang sibuk.
- Tanggal **Periode** di judul selalu menampilkan tanggal hari ini (WIB). Tanggal data di spreadsheet dan waktu pembaruan terakhir tampil di bagian bawah halaman.
- GitHub menonaktifkan jadwal otomatis jika repository tidak ada aktivitas selama 60 hari. Jika itu terjadi, aktifkan lagi dari tab *Actions*.

## Tab spreadsheet yang dibaca

| Tab | Isi yang dipakai |
|---|---|
| Rekap All Region (`gid=1381812318`, range `A1:P13`) | Tabel BOA I dan BOA II per MOR |
| Data_SPBU_BOA (`gid=871452310`) | Kolom U (Hasil Nego KSO), kolom Z (Hasil Audit BOA II: Gagal / Pasti Pas), sel A1 (tanggal data) |

Jika susunan tab berubah, sesuaikan nilai `GID_*` atau `RANGE_REKAP` di `scripts/fetch_data.py`.

## Struktur

```
index.html                 halaman utama (3 tampilan: #dashboard, #boa1, #boa2)
assets/css/style.css       desain
assets/js/app.js           tampilan dan navigasi
assets/js/bar-chart.js     grafik batang (SVG)
assets/img/                logo, ikon, background
assets/fonts/              Poppins (SIL Open Font License)
scripts/fetch_data.py      ambil data dari Google Sheet ke data.json
scripts/compare_data.py    cek apakah data berubah dibanding yang sedang tayang
.github/workflows/deploy.yml   build dan deploy ke GitHub Pages
```

## Mencoba di komputer sendiri

```bash
SHEET_ID=<id spreadsheet> python scripts/fetch_data.py data.json
python -m http.server 8000
# buka http://localhost:8000
```

`data.json` sudah masuk `.gitignore`, jadi tidak akan ikut ter-commit.
