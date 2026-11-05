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
  function groupedBar(container, categories, series) {
    const W = 760, H = 330, L = 44, R = 8, T = 22, B = 34;
    const pw = W - L - R, ph = H - T - B;
    const max = niceMax(Math.max(...series.flatMap(s => s.values)));
    const ticks = 5;

    const legend = document.createElement("div");
    legend.className = "legend";
    series.forEach(s => {
      const sp = document.createElement("span");
      sp.style.setProperty("--c", s.color);
      sp.textContent = s.name;
      legend.appendChild(sp);
    });

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
