/* Dashboard Monitoring BOA I & BOA II
 * Data dibaca dari data.json yang dibuat GitHub Actions dari Google Sheet saat deploy.
 */
(function () {
  "use strict";

  const C = { red: "#d7262e", amber: "#e89b0c", blue: "#0e5cc4", grn: "#2e9e44", navy: "#0b3d91", muted: "#5b6778" };
  const TITLES = {
    dashboard: ["DASHBOARD", "BOA I & II"],
    boa1: ["PROGRES", "BOA I"],
    boa2: ["PROGRES", "BOA II"],
    toptier: ["PROGRES", "TOP TIER"],
  };
  const app = document.getElementById("app");
  let DATA = null;

  /* ---------- helpers ---------- */
  const fmt = n => Number(n || 0).toLocaleString("id-ID");
  const pct = (a, b, d = 1) => (b ? ((a / b) * 100).toFixed(d).replace(".", ",") : "0") + "%";
  const pctRow = (a, b) => (b ? Math.round((a / b) * 100) : 0) + "%";
  const sum = (arr, f) => arr.reduce((s, x) => s + (f(x) || 0), 0);
  const h = (html) => { const t = document.createElement("template"); t.innerHTML = html.trim(); return t.content; };

  function todayWIB() {
    return new Intl.DateTimeFormat("id-ID", { day: "2-digit", month: "long", year: "numeric", timeZone: "Asia/Jakarta" }).format(new Date());
  }
  function stampWIB(iso) {
    if (!iso) return "";
    return new Intl.DateTimeFormat("id-ID", { day: "2-digit", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "Asia/Jakarta" }).format(new Date(iso)) + " WIB";
  }
  function morRange(list) {
    if (!list.length) return "–";
    const contiguous = list.every((m, i) => i === 0 || m === list[i - 1] + 1);
    if (list.length === 1) return "MOR " + list[0];
    return contiguous ? `MOR ${list[0]}–${list[list.length - 1]}` : "MOR " + list.join(", ");
  }

  /* ---------- views ---------- */
  function kpi(label, value, sub, color) {
    return `<div class="kpi"><p class="lab">${label}</p><p class="val" style="color:${color}">${value}</p><p class="sub">${sub}</p></div>`;
  }
  function mini(value, label, color) {
    return `<div class="mini"><b style="color:${color}">${value}</b><small>${label}</small></div>`;
  }

  function viewDashboard(d) {
    const mor = d.rekap.mor, t = d.rekap.total;
    const cats = mor.map(m => "MOR " + m.mor);
    const ks = d.kso_status || {};
    const ksoGet = (k, fb) => (k in ks ? ks[k] : fb);
    const b2h = d.b2_hasil && d.b2_hasil.total ? d.b2_hasil.total : { gagal: t.b2.gagal, pasti_pas: 0 };
    const hasil2 = b2h.gagal + b2h.pasti_pas;
    const topSbm = mor.reduce((a, b) => (b.b2.sbm > a.b2.sbm ? b : a), mor[0]);
    const samMor = mor.filter(m => m.b2.tutup + m.b2.kso > 0).map(m => m.mor);

    const frag = h(`
      <section class="panels">
        <article class="panel" aria-labelledby="p1">
          <div class="panel-head"><span class="pill navy" id="p1">BOA I</span><p>dari ${fmt(t.total)} SPBU wajib audit, ${mor.length} MOR</p></div>
          <div class="kpis">
            ${kpi("Gagal Audit BOA I", fmt(t.b1.gagal), pct(t.b1.gagal, t.total) + " dari total SPBU", C.red)}
            ${kpi("Surat Peringatan", fmt(t.b1.sp), pct(t.b1.sp, t.b1.gagal) + " sudah upload", C.amber)}
            ${kpi("Coaching SBM", fmt(t.b1.sbm), pct(t.b1.sbm, t.b1.gagal) + " sudah upload", C.blue)}
          </div>
          <div class="chart-block"><h3>Tindak lanjut per MOR</h3><div class="chart" id="chart-b1"></div></div>
          <div class="strip" style="--n:5">
            <div class="name"><b>Pertare</b><small>Hasil Nego KSO</small></div>
            ${mini(fmt(ksoGet("Setuju KSO", t.b1.kso_setuju)), "Setuju KSO", C.grn)}
            ${mini(fmt(ksoGet("Negosiasi", 0)), "Negosiasi", C.amber)}
            ${mini(fmt(ksoGet("Gagal KSO", t.b1.kso_gagal)), "Gagal KSO", C.red)}
            ${mini(fmt(ksoGet("Operasional", t.b1.kso_ops)), "Operasional", C.blue)}
            ${mini(fmt(ksoGet("SPBU Tutup", 0)), "SPBU Tutup", C.muted)}
          </div>
        </article>

        <article class="panel" aria-labelledby="p2">
          <div class="panel-head"><span class="pill green" id="p2">BOA II</span><p>${fmt(hasil2)} hasil audit: ${fmt(b2h.pasti_pas)} Pasti Pas, ${fmt(b2h.gagal)} Gagal</p></div>
          <div class="kpis">
            ${kpi("Gagal Audit BOA II", fmt(t.b2.gagal), (hasil2 ? pct(b2h.gagal, hasil2, 0) + " dari hasil audit" : pct(t.b2.gagal, t.total) + " dari total SPBU"), C.red)}
            ${kpi("Surat Peringatan", fmt(t.b2.sp), pct(t.b2.sp, t.b2.gagal) + " dari SPBU gagal", C.amber)}
            ${kpi("Coaching SBM", fmt(t.b2.sbm), topSbm && topSbm.b2.sbm ? `${fmt(topSbm.b2.sbm)} di antaranya MOR ${topSbm.mor}` : "–", C.blue)}
          </div>
          <div class="chart-block"><h3>Tindak lanjut per MOR</h3><div class="chart" id="chart-b2"></div></div>
          <div class="strip" style="--n:3">
            <div class="name"><b>SAM</b><small>Tindakan lanjutan</small></div>
            ${mini(fmt(t.b2.tutup), "Tutup/Pembinaan", C.amber)}
            ${mini(fmt(t.b2.kso), "KSO Mandatory", C.navy)}
            ${mini(morRange(samMor), "Asal seluruh kasus", C.muted)}
          </div>
        </article>
      </section>`);
    app.replaceChildren(frag);

    BarChart.groupedBar(document.getElementById("chart-b1"), cats, [
      { name: "Gagal", color: C.red, values: mor.map(m => m.b1.gagal) },
      { name: "Surat Peringatan", color: C.amber, values: mor.map(m => m.b1.sp) },
      { name: "Coaching SBM", color: C.blue, values: mor.map(m => m.b1.sbm) },
    ]);
    BarChart.groupedBar(document.getElementById("chart-b2"), cats, [
      { name: "Gagal", color: C.red, values: mor.map(m => m.b2.gagal) },
      { name: "Surat Peringatan", color: C.amber, values: mor.map(m => m.b2.sp) },
      { name: "Coaching SBM", color: C.blue, values: mor.map(m => m.b2.sbm) },
    ]);
  }

  const icon = (name, alt, cls = "") => `<img src="assets/img/icon-${name}.png" alt="${alt}" class="${cls}">`;

  function callout(lines) {
    return `<aside class="callout"><div class="mark" aria-hidden="true"><span>!</span></div><ul>${lines.map(l => `<li>${l}</li>`).join("")}</ul></aside>`;
  }

  function viewBoa1(d) {
    const mor = d.rekap.mor, t = d.rekap.total;
    const row = (m, label, total) => `<tr>
      <td>${label}</td><td>${fmt(m.total)}</td><td>${fmt(m.b1.gagal)}</td><td>${fmt(m.b1.sp)}</td>
      <td>${total ? (m.b1.sp_pct || pct(m.b1.sp, m.b1.gagal, 2)) : pctRow(m.b1.sp, m.b1.gagal)}</td>
      <td>${fmt(m.b1.sbm)}</td><td>${total ? (m.b1.sbm_pct || pctRow(m.b1.sbm, m.b1.gagal)) : pctRow(m.b1.sbm, m.b1.gagal)}</td>
      <td>${fmt(m.b1.kso_setuju)}</td><td>${fmt(m.b1.kso_gagal)}</td><td>${fmt(m.b1.kso_ops)}</td></tr>`;
    app.replaceChildren(h(`
      <section class="card table-card"><div class="table-wrap"><table class="rekap">
        <caption hidden>Progres BOA I per MOR</caption>
        <colgroup>${[9, 11, 10, 10, 12.5, 10, 8.5, 9.5, 9, 10.5].map(w => `<col style="--w:${w}%">`).join("")}</colgroup>
        <thead>
          <tr>
            <th rowspan="3">${icon("mor", "")}MOR</th>
            <th rowspan="3">${icon("spbu", "")}Total SPBU</th>
            <th>${icon("ci", "")}CI</th>
            <th>${icon("fca", "")}FCA/<wbr>SA</th>
            <th rowspan="3">${icon("pct", "Persentase", "pct")}</th>
            <th>${icon("sbm", "")}SBM</th>
            <th rowspan="3">${icon("pct", "Persentase", "pct")}</th>
            <th colspan="3">${icon("kso", "")}Pertare</th>
          </tr>
          <tr><th>Hasil Audit BOA I</th><th>Surat Pering&shy;atan (BOA I)</th><th>Coach&shy;ing SBM (BOA I)</th><th colspan="3">Hasil Nego KSO</th></tr>
          <tr><th>Gagal</th><th>Sudah Up&shy;load</th><th>Sudah Up&shy;load</th><th>Setuju KSO</th><th>Gagal</th><th>Opera&shy;sional</th></tr>
        </thead>
        <tbody>${mor.map(m => row(m, m.mor)).join("")}</tbody>
        <tfoot>${row(t, "Total", true)}</tfoot>
      </table></div></section>
      ${callout([
        `Dari <b>${fmt(t.total)} SPBU</b>, sebanyak <b>${fmt(t.b1.gagal)} SPBU</b> tercatat Gagal <b>Audit BOA I</b>.`,
        `Terdapat <b>${fmt(t.b1.sp)} SPBU (${t.b1.sp_pct || pct(t.b1.sp, t.b1.gagal, 2)})</b> yang memerlukan tindak lanjut <b>FCA/Surat Peringatan</b>.`,
        `Coaching SBM telah dilakukan pada <b>${fmt(t.b1.sbm)} SPBU (${t.b1.sbm_pct || pctRow(t.b1.sbm, t.b1.gagal)})</b> dari total SPBU gagal BOA I.`,
      ])}`));
  }

  function viewBoa2(d) {
    const mor = d.rekap.mor, t = d.rekap.total;
    const row = (m, label) => `<tr><td>${label}</td><td>${fmt(m.total)}</td><td>${fmt(m.b2.lolos)}</td><td>${fmt(m.b2.gagal)}</td>
      <td>${fmt(m.b2.sp)}</td><td>${fmt(m.b2.sbm)}</td><td>${fmt(m.b2.tutup)}</td><td>${fmt(m.b2.kso)}</td></tr>`;
    app.replaceChildren(h(`
      <section class="card table-card"><div class="table-wrap"><table class="rekap">
        <caption hidden>Progres BOA II per MOR</caption>
        <colgroup>${[10, 12, 10.5, 10.5, 15, 15, 13.5, 13.5].map(w => `<col style="--w:${w}%">`).join("")}</colgroup>
        <thead>
          <tr>
            <th rowspan="3">${icon("mor", "")}MOR</th>
            <th rowspan="3">${icon("spbu", "")}Total SPBU</th>
            <th colspan="2">${icon("ci", "")}CI</th>
            <th>${icon("fca", "")}FCA/<wbr>SA</th>
            <th>${icon("sbm", "")}SBM</th>
            <th colspan="2">${icon("sam", "")}SAM</th>
          </tr>
          <tr><th colspan="2">Hasil Audit BOA II</th><th>Surat Pering&shy;atan (BOA II)</th><th>Coach&shy;ing SBM (BOA II)</th>
              <th rowspan="2">Tutup/ Pem&shy;binaan</th><th rowspan="2">KSO Manda&shy;tory</th></tr>
          <tr><th>Lolos</th><th>Gagal</th><th>Sudah Up&shy;load</th><th>Sudah Up&shy;load</th></tr>
        </thead>
        <tbody>${mor.map(m => row(m, m.mor)).join("")}</tbody>
        <tfoot>${row(t, "Total")}</tfoot>
      </table></div></section>
      ${callout([
        `Terdapat <b>${fmt(t.b2.gagal)} SPBU Gagal BOA II</b>; <b>${fmt(t.b2.sp)} SPBU</b> sudah mendapatkan <b>Surat Peringatan/FCA.</b>`,
        `<b>${fmt(t.b2.sbm)} SPBU</b> telah mendapatkan <b>Coaching SBM – BOA II.</b>`,
        `Terdapat <b>${fmt(t.b2.tutup)} SPBU</b> yang melakukan <b>Pembinaan</b> dan <b>${fmt(t.b2.kso)} KSO Mandatory.</b>`,
      ])}`));
  }

  function viewTopTier(d) {
    const tt = d.top_tier;
    if (!tt) { app.replaceChildren(h(`<p class="error">Data Top Tier belum tersedia.</p>`)); return; }
    const mor = tt.mor, t = tt.total;
    const keys = ["total", "belum_web", "verif_pttr", "verif_kso_region", "verif_kso_pusat", "penerbitan_ba", "penerbitan_sp_sh"];
    const row = (m, label) => `<tr><td>${label}</td>${keys.map(k => `<td>${fmt(m[k])}</td>`).join("")}</tr>`;
    const top = mor.reduce((a, b) => (b.total > a.total ? b : a), mor[0]);
    const stages = [["verif_pttr", "Verifikasi PTTR"], ["verif_kso_region", "Verifikasi KSO Region"], ["verif_kso_pusat", "Verifikasi KSO Pusat"],
      ["penerbitan_ba", "Penerbitan BA"], ["penerbitan_sp_sh", "Penerbitan SP SH"]].filter(([k]) => t[k] > 0);
    app.replaceChildren(h(`
      <section class="card table-card"><div class="table-wrap"><table class="rekap">
        <caption hidden>Progres Top Tier per MOR</caption>
        <colgroup>${[8, 13, 13, 13, 14, 14, 12, 13].map(w => `<col style="--w:${w}%">`).join("")}</colgroup>
        <thead>
          <tr>
            <th rowspan="3">${icon("mor", "")}MOR</th>
            <th rowspan="3">${icon("spbu-star", "")}Total SPBU Top Tier</th>
            <th colspan="6">${icon("star", "")}TOP TIER</th>
          </tr>
          <tr><th colspan="6">Progress Web DDMS</th></tr>
          <tr><th>Belum ada di web</th><th>Verifikasi PTTR</th><th>Verifikasi KSO Region</th><th>Verifikasi KSO Pusat</th><th>Penerbitan BA</th><th>Penerbitan SP SH</th></tr>
        </thead>
        <tbody>${mor.map(m => row(m, m.mor)).join("")}</tbody>
        <tfoot>${row(t, "Total")}</tfoot>
      </table></div></section>
      ${callout([
        `Terdapat <b>${fmt(t.total)} SPBU Top Tier</b>, terbanyak di <b>MOR ${top.mor} (${fmt(top.total)} SPBU)</b>.`,
        `<b>${fmt(t.belum_web)} SPBU</b> belum ada di <b>web DDMS</b>.`,
        stages.length
          ? "Sudah berproses: " + stages.map(([k, l]) => `<b>${l} ${fmt(t[k])}</b>`).join(", ") + "."
          : `Belum ada SPBU pada tahap <b>Verifikasi PTTR, Verifikasi KSO, Penerbitan BA</b> maupun <b>Penerbitan SP SH.</b>`,
      ])}`));
  }

  /* ---------- routing ---------- */
  const VIEWS = { dashboard: viewDashboard, boa1: viewBoa1, boa2: viewBoa2, toptier: viewTopTier };

  function route() {
    let v = (location.hash || "#dashboard").slice(1);
    if (!VIEWS[v]) v = "dashboard";
    const [a, b] = TITLES[v];
    const title = document.getElementById("title");
    title.querySelector(".t-navy").textContent = a;
    title.querySelector(".t-green").textContent = b;
    document.title = `${a.charAt(0) + a.slice(1).toLowerCase()} ${b} · Monitoring BOA`;
    document.querySelectorAll(".tabs a").forEach(x => {
      const on = x.dataset.view === v;
      x.classList.toggle("active", on);
      if (on) x.setAttribute("aria-current", "page"); else x.removeAttribute("aria-current");
    });
    if (DATA) VIEWS[v](DATA);
  }

  /* Tombol unduh PPT/PDF: file dibuat GitHub Actions di folder unduh/,
   * nama file saat diunduh: "YYYYMMDD Weekly BOA I & BOA II.pptx/.pdf" */
  async function setupDownloads(d) {
    const box = document.getElementById("downloads");
    const name = d.file_name || "Weekly BOA I & BOA II";
    const v = encodeURIComponent(d.generated_at || "");
    let any = false;
    for (const ext of ["pptx", "pdf"]) {
      const a = document.getElementById("dl-" + ext);
      const url = `unduh/weekly-boa.${ext}?v=${v}`;
      try {
        const r = await fetch(url, { method: "HEAD", cache: "no-store" });
        a.hidden = !r.ok;
        any = any || r.ok;
      } catch (e) { a.hidden = true; }
      a.href = url;
      a.setAttribute("download", `${name}.${ext}`);
      a.title = `${name}.${ext}`;
    }
    box.hidden = !any;
  }

  const REFRESH_MS = 2 * 60 * 1000; // cek data baru setiap 2 menit
  let lastKey = "";

  async function load(first) {
    try {
      const res = await fetch("data.json?t=" + Date.now(), { cache: "no-store" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const next = await res.json();
      const key = JSON.stringify(next);
      if (key === lastKey) return;
      lastKey = key;
      DATA = next;
      const sync = document.getElementById("sync");
      sync.textContent = `Sumber: spreadsheet Report SPBU BOA${DATA.periode_sheet ? " (data " + DATA.periode_sheet + ")" : ""} · diperbarui ${stampWIB(DATA.generated_at)}`;
      document.querySelector('.tabs a[data-view="toptier"]').hidden = !DATA.top_tier;
      route();
      setupDownloads(DATA);
    } catch (e) {
      if (first) {
        app.replaceChildren(h(`<p class="error">Data belum tersedia. Jalankan workflow “Deploy dashboard” di tab Actions GitHub, lalu muat ulang halaman ini.</p>`));
      }
      console.error(e);
    }
  }

  function init() {
    document.getElementById("periode").textContent = todayWIB();
    route();
    load(true);
    setInterval(() => {
      document.getElementById("periode").textContent = todayWIB();
      if (!document.hidden) load(false);
    }, REFRESH_MS);
    document.addEventListener("visibilitychange", () => { if (!document.hidden) load(false); });
  }

  window.addEventListener("hashchange", route);
  init();
})();
