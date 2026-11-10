# Monitoring BOA I & BOA II

Dashboard Monitoring BOA I &amp; BOA II - Channel Development.

Website statis (HTML, CSS, JavaScript tanpa library eksternal) yang dipublikasikan dengan GitHub Pages. Isinya tiga halaman:

- **Dashboard**: ringkasan BOA I dan BOA II, angka utama, grafik per MOR, status Pertare (Hasil Nego KSO) dan SAM.
- **Progres BOA I**: tabel per MOR.
- **Progres BOA II**: tabel per MOR.
- **Progres Top Tier**: tabel Top Tier, Progress Web DDMS per MOR (baris 31–42 tab Rekap All Region).
- Tombol **Unduh PPT** dan **Unduh PDF**: file `YYYYMMDD Weekly BOA I & BOA II.pptx/.pdf` dengan angka terbaru. Dibuat ulang otomatis oleh GitHub Actions setiap kali data berubah (PPT dibuat dari nol oleh `scripts/build_pptx.py`, PDF dikonversi dengan LibreOffice). File ini tidak disimpan di repository.

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

- **Real-time dari spreadsheet (disarankan):** Google Apps Script di spreadsheet mengirim sinyal ke GitHub setiap kali ada edit. Website, PPT, dan PDF diperbarui sekitar **2–4 menit** setelah edit berhenti. Cara memasang ada di bawah.
- **Cadangan otomatis:** jadwal "setiap 10 menit". Pada repository gratis, GitHub biasanya hanya menjalankannya sekitar sekali per jam.
- **Manual:** *Actions → Deploy dashboard → Run workflow* (selalu deploy).
- **Saat ada perubahan kode:** setiap push ke branch `main` juga memicu deploy.
- Deploy hanya dijalankan kalau ada angka yang berubah. Edit yang tidak mengubah angka di dashboard tidak memicu deploy.
- **Halaman yang sedang terbuka** memeriksa data baru setiap 2 menit (dan saat tab dibuka kembali), lalu memperbarui angka tanpa perlu di-refresh.
- Tanggal **Periode** di judul selalu menampilkan tanggal hari ini (WIB). Tanggal data di spreadsheet dan waktu pembaruan terakhir tampil di bagian bawah halaman.

### Update real-time dari spreadsheet (pasang sekali)

1. **Buat token GitHub khusus repository ini.** Buka GitHub → *Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token*.
   - Repository access: *Only select repositories* → `Monitoring-BOA-I-BOA-II`
   - Permissions → Repository permissions → **Contents: Read and write** (yang lain biarkan *No access*)
   - Salin token yang muncul (diawali `github_pat_`).
2. **Pasang script di spreadsheet.** Buka spreadsheet → *Extensions → Apps Script*. Hapus isi editor, lalu tempel isi file [`apps-script/KirimKeGitHub.gs`](apps-script/KirimKeGitHub.gs). Simpan.
3. **Simpan token.** Di editor Apps Script: *Project Settings* (ikon roda gigi) → *Script Properties* → *Add script property*.
   - Property: `GITHUB_TOKEN`
   - Value: token dari langkah 1
4. **Aktifkan.** Kembali ke *Editor*, pilih fungsi **`pasang`** di menu atas, klik *Run*, lalu izinkan akses yang diminta Google.
5. **Cek hasilnya.** Di log harus muncul "Berhasil: GitHub menerima sinyal". Di GitHub tab *Actions* akan muncul run baru dengan keterangan **repository_dispatch**.

Catatan keamanan: token disimpan di Script Properties, tidak di sel spreadsheet atau di repository. Orang yang punya akses **edit** ke spreadsheet bisa membuka editor Apps Script dan melihat token itu. Karena itu token dibatasi hanya untuk repository ini dan hanya izin *Contents*. Jika token bocor, hapus di GitHub lalu buat yang baru.

- GitHub menonaktifkan jadwal otomatis jika repository tidak ada aktivitas selama 60 hari. Sinyal dari spreadsheet tetap berjalan, tetapi jadwal cadangan perlu diaktifkan lagi dari tab *Actions*.

## Tab spreadsheet yang dibaca

| Tab | Isi yang dipakai |
|---|---|
| Rekap All Region (`gid=1381812318`, range `A1:P13`) | Tabel BOA I dan BOA II per MOR |
| Rekap All Region (`gid=1381812318`, range `A31:H42`) | Tabel Top Tier, Progress Web DDMS (slide/tab ke-4) |
| Data_SPBU_BOA (`gid=871452310`) | Kolom U (Hasil Nego KSO), kolom Z (Hasil Audit BOA II: Gagal / Pasti Pas), sel A1 (tanggal data) |

Jika susunan tab berubah, sesuaikan nilai `GID_*`, `RANGE_REKAP`, atau `RANGE_TOPTIER` di `scripts/fetch_data.py`.

## Struktur

```
index.html                 halaman utama (4 tampilan: #dashboard, #boa1, #boa2, #toptier)
assets/css/style.css       desain
assets/js/app.js           tampilan dan navigasi
assets/js/bar-chart.js     grafik batang (SVG)
assets/img/                logo, ikon, background
assets/fonts/              Poppins (SIL Open Font License)
scripts/fetch_data.py      ambil data dari Google Sheet ke data.json
scripts/compare_data.py    cek apakah data berubah dibanding yang sedang tayang
scripts/build_pptx.py      buat PPT 4 slide dari data.json (PDF dikonversi di Actions)
apps-script/KirimKeGitHub.gs   Google Apps Script: kirim sinyal ke GitHub saat spreadsheet diedit
scripts/fonts/             Poppins TTF untuk render PDF
.github/workflows/deploy.yml   build dan deploy ke GitHub Pages
```

## Mencoba di komputer sendiri

```bash
SHEET_ID=<id spreadsheet> python scripts/fetch_data.py data.json
python -m http.server 8000
# buka http://localhost:8000
```

`data.json` sudah masuk `.gitignore`, jadi tidak akan ikut ter-commit.
