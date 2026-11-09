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
  const MOBILE_MAX = 560; // lebar kontainer (px) di bawah ini -> grafik ringkas untuk HP
  const registry = new Set();

  function isNarrow(container) {
    // di HP halaman memakai layout laptop yang diperkecil -> grafik selalu versi laptop
    if (document.documentElement.classList.contains("scaled")) return false;
    return (container.clientWidth || window.innerWidth) < MOBILE_MAX;
  }

  function groupedBar(container, categories, series) {
    container._barArgs = [categories, series];
    container._barNarrow = isNarrow(container);
    registry.add(container);
    return verticalBar(container, categories, series, container._barNarrow);
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

  /* compact = versi HP: bentuk grafik sama, ukuran mengikuti lebar layar,
   * angka di atas batang diputar tegak agar tidak saling tumpuk. */
  function verticalBar(container, categories, series, compact) {
    const W = compact ? Math.max(260, Math.round(container.clientWidth || 320)) : 760;
    const H = compact ? 250 : 330, L = compact ? 30 : 44, R = compact ? 2 : 8, T = compact ? 30 : 22, B = compact ? 24 : 34;
    const fs = compact ? { tick: 9, val: 9, cat: 10 } : { tick: 11, val: 10.5, cat: 12.5 };
    const pw = W - L - R, ph = H - T - B;
    const max = niceMax(Math.max(...series.flatMap(s => s.values)));
    const ticks = 5;

    const legend = legendEl(series);

    const svg = el("svg", Object.assign({ viewBox: `0 0 ${W} ${H}`, role: "img",
      "aria-label": "Grafik per MOR: " + series.map(s => s.name).join(", ") }, compact ? { width: W, height: H } : {}));

    for (let i = 0; i <= ticks; i++) {
      const v = (max / ticks) * i;
      const y = T + ph - (v / max) * ph;
      svg.appendChild(el("line", { x1: L, x2: W - R, y1: y, y2: y, stroke: i === 0 ? "#c8cfda" : "#e3e7ee", "stroke-width": 1 }));
      svg.appendChild(el("text", { x: L - 8, y: y + 4, "text-anchor": "end", "font-size": fs.tick, fill: "#5b6778" },
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
          const cx = x + bw * 0.44;
          svg.appendChild(compact
            ? el("text", { x: cx + 3, y: y - 3, "font-size": fs.val, fill: "#1f2937", transform: `rotate(-90 ${cx + 3} ${y - 3})` },
                v.toLocaleString("id-ID"))
            : el("text", { x: cx, y: y - 5, "text-anchor": "middle", "font-size": fs.val, fill: "#1f2937" },
                v.toLocaleString("id-ID")));
        }
      });
      svg.appendChild(el("text", { x: L + ci * gw + gw / 2, y: H - 10, "text-anchor": "middle", "font-size": fs.cat, fill: "#1f2937" }, compact ? c.replace(/^MOR\s*/, "") : c));
    });

    if (compact) {
      svg.appendChild(el("text", { x: 0, y: H - 10, "font-size": fs.cat, "font-weight": 600, fill: "#5b6778" }, "MOR"));
    }
    container.innerHTML = "";
    container.appendChild(legend);
    container.appendChild(svg);
  }

  window.BarChart = { groupedBar };
})();
