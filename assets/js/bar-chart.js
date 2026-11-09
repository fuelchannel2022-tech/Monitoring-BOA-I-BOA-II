/* Grafik batang berkelompok (SVG), tanpa library eksternal. */
(function () {
  const NS = "http://www.w3.org/2000/svg";

  function el(name, attrs, text) {
    const n = document.createElementNS(NS, name);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (text != null) n.textContent = text;
    return n;
  }

  function niceMax(v) {
    if (v <= 0) return 10;
    const p = Math.pow(10, Math.floor(Math.log10(v)));
    for (const m of [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]) {
      if (m * p >= v * 1.08) return m * p;
    }
    return 10 * p;
  }

  /**
   * container: elemen tujuan
   * categories: ["MOR 1", ...]
   * series: [{ name, color, values: [..] }]
   */
  const MOBILE_MAX = 560; // lebar kontainer (px) di bawah ini -> grafik batang horizontal
  const registry = new Set();

  function isNarrow(container) {
    return (container.clientWidth || window.innerWidth) < MOBILE_MAX;
  }

  function groupedBar(container, categories, series) {
    container._barArgs = [categories, series];
    container._barNarrow = isNarrow(container);
    registry.add(container);
    if (container._barNarrow) return horizontalBar(container, categories, series);
    return verticalBar(container, categories, series);
  }

  function legendEl(series) {
    const legend = document.createElement("div");
    legend.className = "legend";
    series.forEach(s => {
      const sp = document.createElement("span");
      sp.style.setProperty("--c", s.color);
      sp.textContent = s.name;
      legend.appendChild(sp);
    });
    return legend;
  }

  /* Versi HP: kategori ke bawah, batang ke samping, lebar mengikuti layar. */
  function horizontalBar(container, categories, series) {
    const W = Math.max(260, Math.round(container.clientWidth || 320));
    const L = 50, R = 34, bh = 11, bgap = 3, ggap = 14, T = 4;
    const gh = series.length * bh + (series.length - 1) * bgap;
    const H = T + categories.length * (gh + ggap);
    const pw = W - L - R;
    const max = Math.max(1, ...series.flatMap(s => s.values));

    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img",
      "aria-label": "Grafik per MOR: " + series.map(s => s.name).join(", ") });
    categories.forEach((c, ci) => {
      const gy = T + ci * (gh + ggap);
      if (ci > 0) svg.appendChild(el("line", { x1: 0, x2: W, y1: gy - ggap / 2, y2: gy - ggap / 2, stroke: "#eef1f5", "stroke-width": 1 }));
      svg.appendChild(el("text", { x: 0, y: gy + gh / 2 + 4, "font-size": 12.5, "font-weight": 600, fill: "#1f2937" }, c));
      svg.appendChild(el("line", { x1: L, x2: L, y1: gy - 2, y2: gy + gh + 2, stroke: "#c8cfda", "stroke-width": 1 }));
      series.forEach((s, si) => {
        const v = s.values[ci] || 0;
        const w = (v / max) * pw;
        const y = gy + si * (bh + bgap);
        const r = el("rect", { x: L, y, width: Math.max(w, 0), height: bh, fill: s.color, rx: 1.5 });
        r.appendChild(el("title", {}, `${c} · ${s.name}: ${v.toLocaleString("id-ID")}`));
        svg.appendChild(r);
        svg.appendChild(el("text", { x: L + w + 4, y: y + bh - 1.5, "font-size": 10.5, fill: v ? "#1f2937" : "#9aa3af" },
          v.toLocaleString("id-ID")));
      });
    });
    container.innerHTML = "";
    container.appendChild(legendEl(series));
    container.appendChild(svg);
  }

  // gambar ulang saat orientasi/lebar layar berubah melewati batas HP
  let t;
  window.addEventListener("resize", () => {
    clearTimeout(t);
    t = setTimeout(() => {
      registry.forEach(c => {
        if (!c.isConnected) { registry.delete(c); return; }
        const narrow = isNarrow(c);
        if (narrow || narrow !== c._barNarrow) groupedBar(c, ...c._barArgs);
      });
    }, 150);
  });

  function verticalBar(container, categories, series) {
    const W = 760, H = 330, L = 44, R = 8, T = 22, B = 34;
    const pw = W - L - R, ph = H - T - B;
    const max = niceMax(Math.max(...series.flatMap(s => s.values)));
    const ticks = 5;

    const legend = legendEl(series);

    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img",
      "aria-label": "Grafik per MOR: " + series.map(s => s.name).join(", ") });

    for (let i = 0; i <= ticks; i++) {
      const v = (max / ticks) * i;
      const y = T + ph - (v / max) * ph;
      svg.appendChild(el("line", { x1: L, x2: W - R, y1: y, y2: y, stroke: i === 0 ? "#c8cfda" : "#e3e7ee", "stroke-width": 1 }));
      svg.appendChild(el("text", { x: L - 8, y: y + 4, "text-anchor": "end", "font-size": 11, fill: "#5b6778" },
        Math.round(v).toLocaleString("id-ID")));
    }

    const gw = pw / categories.length;
    const inner = gw * 0.78;
    const bw = inner / series.length;
    categories.forEach((c, ci) => {
      const gx = L + ci * gw + (gw - inner) / 2;
      series.forEach((s, si) => {
        const v = s.values[ci] || 0;
        const h = (v / max) * ph;
        const x = gx + si * bw + bw * 0.06;
        const y = T + ph - h;
        const r = el("rect", { x, y, width: bw * 0.88, height: Math.max(h, 0), fill: s.color, rx: 1.5 });
        r.appendChild(el("title", {}, `${c} · ${s.name}: ${v.toLocaleString("id-ID")}`));
        svg.appendChild(r);
        if (v > 0) {
          svg.appendChild(el("text", { x: x + bw * 0.44, y: y - 5, "text-anchor": "middle", "font-size": 10.5, fill: "#1f2937" },
            v.toLocaleString("id-ID")));
        }
      });
      svg.appendChild(el("text", { x: L + ci * gw + gw / 2, y: H - 10, "text-anchor": "middle", "font-size": 12.5, fill: "#1f2937" }, c));
    });

    container.innerHTML = "";
    container.appendChild(legend);
    container.appendChild(svg);
  }

  window.BarChart = { groupedBar };
})();
