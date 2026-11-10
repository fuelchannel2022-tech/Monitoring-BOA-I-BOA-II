/**
 * Kirim sinyal ke GitHub setiap kali spreadsheet "Report SPBU BOA" berubah,
 * supaya website Monitoring BOA I & BOA II langsung diperbarui.
 *
 * Cara pasang (sekali saja) — lihat README bagian "Update real-time dari spreadsheet":
 *   1. Spreadsheet → Extensions → Apps Script → tempel file ini.
 *   2. Project Settings → Script Properties → tambah GITHUB_TOKEN = <token GitHub>.
 *   3. Jalankan fungsi `pasang` sekali, lalu izinkan aksesnya.
 *
 * Token TIDAK ditulis di file ini dan tidak disimpan di sel spreadsheet.
 */

var REPO = 'fuelchannel2022-tech/Monitoring-BOA-I-BOA-II';
var EVENT = 'sheet-updated';
var JEDA_DETIK = 20;   // tunggu edit berhenti sebentar sebelum mengirim (edit beruntun digabung)

/** Jalankan sekali: membuat trigger "saat berubah" dan pengecek tiap 1 menit. */
function pasang() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    var f = t.getHandlerFunction();
    if (f === 'tandaiBerubah' || f === 'kirimJikaPerlu') ScriptApp.deleteTrigger(t);
  });
  var ss = SpreadsheetApp.getActive();
  ScriptApp.newTrigger('tandaiBerubah').forSpreadsheet(ss).onChange().create();
  ScriptApp.newTrigger('tandaiBerubah').forSpreadsheet(ss).onEdit().create();
  ScriptApp.newTrigger('kirimJikaPerlu').timeBased().everyMinutes(1).create();
  ujiKoneksi();
}

/** Dipanggil otomatis setiap ada edit/perubahan. Hanya mencatat waktu perubahan. */
function tandaiBerubah() {
  PropertiesService.getScriptProperties().setProperty('TERAKHIR_BERUBAH', String(Date.now()));
}

/** Dipanggil tiap 1 menit: jika ada perubahan dan edit sudah berhenti, kirim sinyal ke GitHub. */
function kirimJikaPerlu() {
  var props = PropertiesService.getScriptProperties();
  var berubah = Number(props.getProperty('TERAKHIR_BERUBAH') || 0);
  var terkirim = Number(props.getProperty('TERAKHIR_TERKIRIM') || 0);
  if (!berubah || berubah <= terkirim) return;                // tidak ada perubahan baru
  if (Date.now() - berubah < JEDA_DETIK * 1000) return;       // masih ada yang mengedit
  if (kirimKeGitHub_()) props.setProperty('TERAKHIR_TERKIRIM', String(berubah));
}

/** Kirim sinyal sekarang juga (bisa dijalankan manual dari editor Apps Script). */
function ujiKoneksi() {
  var ok = kirimKeGitHub_();
  Logger.log(ok ? 'Berhasil: GitHub menerima sinyal, website sedang diperbarui.'
                : 'Gagal: cek GITHUB_TOKEN di Script Properties (lihat log di atas).');
  return ok;
}

function kirimKeGitHub_() {
  var token = PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN');
  if (!token) {
    Logger.log('GITHUB_TOKEN belum diisi di Project Settings → Script Properties.');
    return false;
  }
  var res = UrlFetchApp.fetch('https://api.github.com/repos/' + REPO + '/dispatches', {
    method: 'post',
    contentType: 'application/json',
    headers: {
      Authorization: 'Bearer ' + token,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28'
    },
    payload: JSON.stringify({ event_type: EVENT, client_payload: { sumber: 'apps-script' } }),
    muteHttpExceptions: true
  });
  var code = res.getResponseCode();
  if (code === 204) return true;
  Logger.log('GitHub menolak (HTTP ' + code + '): ' + res.getContentText().slice(0, 300));
  return false;
}
