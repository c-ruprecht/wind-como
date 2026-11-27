/* Model page: charts from modell.json (training/export_modell.py). Plain SVG, hover tooltips, tables as text view. */
"use strict";
const $ = s => document.querySelector(s);
const de = (x, n = 2) => x == null ? "–" : Number(x).toFixed(n);
const pc = p => p == null ? "–" : Math.round(p * 100) + " %";
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

/* English names of the model variables (German keys in the data) */
const FN = {
  wind_see_15_sued: ["South wind over the lake", "weather model, 15:00"], wind_see_15: ["Wind over the lake", "weather model, 15:00"],
  wind_milano_12: ["Wind in the Po plain", "Milan, 12:00"], taupunktdiff_milano: ["Dry air", "dew-point spread, Milan 13:00"],
  dp_po_tal_06: ["Pressure gradient plain → valley", "Milan − Chiavenna, 6:00"], dp_po_tal_15: ["Pressure gradient plain → valley", "Milan − Chiavenna, 15:00"],
  dp_po_tal_18: ["Pressure gradient plain → valley", "Milan − Chiavenna, 18:00"], dp_tag_minus_nacht: ["Valley low builds during the day", "gradient 15:00 minus 6:00"],
  dp_bergamo_sondrio_15: ["Pressure gradient into Valtellina", "Bergamo − Sondrio, 15:00"], dp_zurich_milano_12: ["North-foehn index", "Zurich − Milan, 12:00"],
  dp_muenchen_genova_12: ["Alpine foehn situation", "Munich − Genoa, 12:00"], dp_lyon_venezia_12: ["West–east gradient", "Lyon − Venice, 12:00"],
  geo_staerke: ["Large-scale wind strength", "from the pressure field"], geo_aus_sued: ["Large-scale flow from the south", "from the pressure field"],
  geo_aus_west: ["Large-scale flow from the west", "from the pressure field"], drucktendenz_24h: ["Pressure tendency", "change over 24 h, Milan"],
  rad_see: ["Sun over the lake", "9–17:00"], rad_chiavenna: ["Sun in the valley", "Chiavenna, 9–17:00"], rad_milano: ["Sun in the plain", "Milan, 9–17:00 (not in model)"],
  rad_spaet_chiavenna: ["Late-afternoon sun in the valley", "Chiavenna, 15–18:00"], wolken_see: ["Clouds over the lake", "9–17:00"],
  wolken_morgen_see: ["Morning clouds over the lake", "6–11:00"], wolken_chiavenna: ["Clouds in the valley", "Chiavenna, 9–17:00"],
  tmax_milano: ["Max. temperature Milan", "plain"], tmax_bergamo: ["Max. temperature Bergamo", "plain"], tmax_sondrio: ["Max. temperature Sondrio", "Valtellina"],
  tmax_chiavenna: ["Max. temperature Chiavenna", "valley"], tmax_engadin: ["Max. temperature Engadine", "above the Alps"], tmax_see: ["Max. temperature at the lake", "(not in model)"],
  tmin_chiavenna: ["Night temperature Chiavenna", "3–8:00"], dt_tal_po: ["Valley warmer than the plain", "temperature difference"],
  dt_engadin_po: ["Engadine vs plain", "temperature difference"], regen_see: ["Rain on the lake", "11–19:00"], regen_chiavenna: ["Rain in the valley", "11–19:00"],
  regen_vortag: ["Rain the day before", "lake and valley"], see_t30: ["Lake temperature (proxy)", "30-day mean air at the lake"],
  luft_minus_see_t30: ["Warm air over a cool lake", "air minus lake proxy"], doy_sin: ["Season", "time of year (sine)"], doy_cos: ["Season", "time of year (cosine)"],
  bodenfeuchte_milano: ["Soil moisture in the plain", "(not in model)"]
};
const HN = {
  _jetzt: "now", _mittel2h: "mean of the last 2 h", _max_ab10: "max since 10:00",
  samolaco: "Samolaco", colico: "Colico", vercana: "Vercana (980 m)", morbegno: "Morbegno",
  tivano_samolaco: ["Tivano this morning", "north wind at Samolaco 5–9:00"], see_jetzt: ["Lake wind now", "estimate from Samolaco/Colico"],
  see_stunden: ["Breva hours so far", "hours with 14+ kn since 11:00"], see_lauf: ["Current Breva run", "hours in a row with 14+ kn"],
  morgen_nicht_breva: ["Morning wind from another direction", "Samolaco 6–10:00"], rad_gem_tal: ["Measured sun, valleys", "ARPA Chiavenna/Sondrio since 7:00"],
  rad_gem_ebene: ["Measured sun, plain", "ARPA Milan/Bergamo since 7:00"], dt_gem_tal_ebene: ["Measured temperature valley − plain", "ARPA, now"],
  gestern_breva: ["Breva yesterday", "yes/no"], gestern_max: ["Strongest hour yesterday", "lake estimate"]
};
const fname = f => FN[f] ? FN[f] : [f, ""];
function hname(f) {
  if (Array.isArray(HN[f])) return HN[f];
  const m = f.match(/^(samolaco|colico|vercana|morbegno)(_jetzt|_mittel2h|_max_ab10)$/);
  return m ? [`Wind in Breva direction, ${HN[m[1]]}`, HN[m[2]]] : [f, ""];
}

/* ---------- tooltip ---------- */
const tip = () => $("#tip");
function showTip(ev, html) {
  const t = tip(); t.innerHTML = html; t.hidden = false;
  const r = t.getBoundingClientRect(), pad = 12;
  let x = ev.clientX + pad, y = ev.clientY + pad;
  if (x + r.width > innerWidth - 4) x = ev.clientX - r.width - pad;
  if (y + r.height > innerHeight - 4) y = ev.clientY - r.height - pad;
  t.style.left = x + "px"; t.style.top = y + "px";
}
const hideTip = () => { tip().hidden = true; };

/* ---------- generic x/y chart: lines and/or points, nearest-point hover ---------- */
let chartId = 0;
function xy(el, series, o = {}) {
  const W = o.W ?? 420, H = o.H ?? 260, L = 40, R = 10, T = 10, Bm = 34;
  const [x0, x1] = o.xr, [y0, y1] = o.yr;
  const X = v => L + (v - x0) / (x1 - x0) * (W - L - R), Y = v => T + (1 - (v - y0) / (y1 - y0)) * (H - T - Bm);
  const id = "c" + (++chartId);
  let s = `<svg viewBox="0 0 ${W} ${H}" class="chart" id="${id}" role="img" aria-label="${esc(o.aria || "")}">`;
  for (const v of o.yt) s += `<line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" class="grid"/><text x="${L - 5}" y="${Y(v) + 3}" class="ax" text-anchor="end">${o.yf(v)}</text>`;
  for (const v of o.xt) s += `<text x="${X(v)}" y="${H - Bm + 14}" class="ax" text-anchor="middle">${o.xf(v)}</text>`;
  s += `<text x="${(L + W - R) / 2}" y="${H - 4}" class="ax lab" text-anchor="middle">${o.xl}</text>`;
  s += `<text x="10" y="${(T + H - Bm) / 2}" class="ax lab" text-anchor="middle" transform="rotate(-90 10 ${(T + H - Bm) / 2})">${o.yl}</text>`;
  for (const r of o.refs || []) s += `<line x1="${X(r[0])}" y1="${Y(r[1])}" x2="${X(r[2])}" y2="${Y(r[3])}" class="ref"/>`;
  const pts = [];
  for (const se of series) {
    if (se.line !== false) {
      const d = se.pts.map((p, i) => `${i ? "L" : "M"}${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`).join("");
      s += `<path d="${d}" fill="none" style="stroke:${se.c}" stroke-width="2" stroke-linejoin="round" ${se.dash ? 'stroke-dasharray="5 4"' : ""}/>`;
    }
    if (se.base != null) s += `<line x1="${L}" x2="${W - R}" y1="${Y(se.base)}" y2="${Y(se.base)}" class="base" style="stroke:${se.c}"/>`;
    for (const p of se.pts) {
      const cx = X(p[0]), cy = Y(p[1]);
      if (se.dots) s += `<circle cx="${cx}" cy="${cy}" r="${se.r ? se.r(p) : 4}" style="fill:${se.c}" class="dot"/>`;
      pts.push({ cx, cy, html: se.tip(p) });
    }
  }
  s += `<rect x="${L}" y="${T}" width="${W - L - R}" height="${H - T - Bm}" fill="transparent" class="hit"/></svg>`;
  el.innerHTML = s;
  const svg = el.querySelector("svg");
  const move = ev => {
    const m = svg.getScreenCTM(); if (!m) return;
    const px = (ev.clientX - m.e) / m.a, py = (ev.clientY - m.f) / m.d;
    let best = null, bd = 1e9;
    for (const p of pts) { const d = (p.cx - px) ** 2 + (p.cy - py) ** 2; if (d < bd) { bd = d; best = p; } }
    let mk = svg.querySelector(".hov");
    if (best && bd < 900) {
      if (!mk) { mk = document.createElementNS("http://www.w3.org/2000/svg", "circle"); mk.setAttribute("class", "hov"); mk.setAttribute("r", 5); svg.appendChild(mk); }
      mk.setAttribute("cx", best.cx); mk.setAttribute("cy", best.cy);
      showTip(ev, best.html);
    } else { if (mk) mk.remove(); hideTip(); }
  };
  svg.addEventListener("pointermove", move);
  svg.addEventListener("pointerleave", () => { svg.querySelector(".hov")?.remove(); hideTip(); });
}
const legend = (el, items) => { el.innerHTML = items.map(([n, c, dash]) =>
  `<span><i class="ln" style="background:${dash ? "transparent" : c};${dash ? `border-top:2px dashed ${c};height:0` : ""}"></i>${n}</span>`).join(""); };

const C = ["var(--c1)", "var(--c2)", "var(--c3)"];
const RAMP = n => Array.from({ length: n }, (_, i) => `var(--s${i + 1})`);   // s1 = darkest (most important)

/* ---------- sections ---------- */
function kpis(M) {
  const s = M.sieben, h = M.heute?.["14"], hl = M.heute?.lang;
  const items = [
    [Math.round(M.anteil.tage_jahr_breva), "Breva days per year (March–October)"],
    [Math.round(M.anteil.tage_jahr_lang), "of them long (5+ h)"],
    [de(s["1"].breva.auc), `skill tomorrow (AUC) · day 3: ${de(s["3"].breva.auc)}`],
    [h ? de(h["13"].auc) : "–", `skill today at 13:00 · long Breva ${hl ? de(hl["13"].auc) : "–"}`]
  ];
  $("#kpis").innerHTML = items.map(([a, b]) => `<div class="kpi"><b>${a}</b><span>${b}</span></div>`).join("");
  $("#fsam").textContent = "× " + de(M.faktor_sam, 2); $("#fcol").textContent = "× " + de(M.faktor_col, 2);
  $("#langh").textContent = M.lang_h;
  $("#stand").textContent = `Data as of ${M.stand}. Test: real ECMWF forecasts 2024–2026, each year predicted by a model trained without it.`;
}

function faktoren(M) {
  const F = M.faktoren || []; if (!F.length) return;
  const W = 760, rowH = 36, T = 30, L = 270, R = 16, H = T + F.length * rowH + 30, lo = -0.6, hi = 0.6;
  const X = v => L + (v - lo) / (hi - lo) * (W - L - R);
  let s = `<svg viewBox="0 0 ${W} ${H}" class="chart" role="img" aria-label="Effect of each weather variable">`;
  for (const v of [-0.6, -0.4, -0.2, 0, 0.2, 0.4, 0.6]) s += `<line x1="${X(v)}" x2="${X(v)}" y1="${T - 6}" y2="${H - 26}" class="${v === 0 ? "zero" : "grid"}"/><text x="${X(v)}" y="${H - 12}" class="ax" text-anchor="middle">${v > 0 ? "+" : ""}${v.toFixed(1)}</text>`;
  s += `<text x="${X(-0.3)}" y="${T - 10}" class="ax lab" text-anchor="middle">lower on Breva / long days</text><text x="${X(0.3)}" y="${T - 10}" class="ax lab" text-anchor="middle">higher on Breva / long days</text>`;
  const dots = [];
  F.forEach((f, i) => {
    const y = T + i * rowH + rowH / 2, [n, sub] = fname(f.f);
    s += `<text x="${L - 10}" y="${y - 2}" class="fl-t2" text-anchor="end">${f.eigen_lang ? "◆ " : ""}${esc(n)}</text><text x="${L - 10}" y="${y + 12}" class="ax" text-anchor="end">${esc(sub)}</text>`;
    s += `<line x1="${X(f.ruhig_kurz)}" x2="${X(f.kurz_lang)}" y1="${y}" y2="${y}" class="conn"/>`;
    for (const [k, c, lab] of [["ruhig_kurz", C[0], "calm → short Breva"], ["kurz_lang", C[1], "short → long Breva"]]) {
      s += `<circle cx="${X(f[k])}" cy="${y}" r="6.5" style="fill:${c}" class="dot"/>`;
      dots.push({ cx: X(f[k]), cy: y, html: `<b>${esc(n)}</b> <small>${esc(sub)}</small><br>${lab}: ${f[k] > 0 ? "+" : ""}${de(f[k])}<br><small>median calm ${de(f.med[0], 1)} · near miss ${de(f.med[1], 1)} · short ${de(f.med[2], 1)} · long ${de(f.med[3], 1)}</small>` });
    }
  });
  s += `</svg>`;
  const el = $("#faktorChart"); el.innerHTML = s;
  const svg = el.querySelector("svg");
  svg.addEventListener("pointermove", ev => {
    const m = svg.getScreenCTM(); const px = (ev.clientX - m.e) / m.a, py = (ev.clientY - m.f) / m.d;
    let b = null, bd = 1e9; for (const d of dots) { const q = (d.cx - px) ** 2 + (d.cy - py) ** 2; if (q < bd) { bd = q; b = d; } }
    if (b && bd < 400) showTip(ev, b.html); else hideTip();
  });
  svg.addEventListener("pointerleave", hideTip);
  legend($("#faktorLeg"), [["calm → short Breva", C[0]], ["short → long Breva", C[1]], ["◆ matters only for the duration", "transparent"]]);
  $("#featTab").innerHTML = "<thead><tr><th>Variable</th><th>Detail</th></tr></thead><tbody>" +
    M.features7.map(f => { const [n, s2] = fname(f); return `<tr><th>${esc(n)}</th><td>${esc(s2)}</td></tr>`; }).join("") + "</tbody>";
}

function vorlauf(M) {
  const S = M.sieben, Ls = Object.keys(S).map(Number).sort((a, b) => a - b);
  const ser = [["Breva day", "breva", C[0]], ["Long Breva", "lang", C[1]]].map(([n, k, c]) => ({
    c, dots: true, pts: Ls.filter(L => S[L][k]).map(L => [L, S[L][k].auc]),
    tip: p => `<b>${n}</b>, ${p[0] === 1 ? "tomorrow" : `in ${p[0]} days`}<br>AUC ${de(p[1])}`
  }));
  xy($("#aucChart"), ser, { xr: [0.7, 7.3], yr: [0.5, 1], xt: Ls, yt: [0.5, 0.6, 0.7, 0.8, 0.9, 1], xf: v => v === 1 ? "1 (tomorrow)" : v,
    yf: v => v.toFixed(1), xl: "days ahead", yl: "AUC", aria: "Skill by days ahead", H: 240 });
  legend($("#aucLeg"), [["Breva day", C[0]], ["Long Breva", C[1]]]);
  $("#aucTab").innerHTML = `<thead><tr><th>Days ahead</th><th>AUC Breva</th><th>AUC long</th><th>caught at ≥ 70 % precision</th><th>test days</th></tr></thead><tbody>` +
    Ls.map(L => `<tr><th>${L}</th><td>${de(S[L].breva.auc)}</td><td>${de(S[L].lang?.auc)}</td><td>${pc(S[L].breva.r70)}</td><td>${S[L].tage}</td></tr>`).join("") + "</tbody>";
}

function prChart(el, groups, labelFn) {
  const keys = Object.keys(groups), cols = RAMP(keys.length);
  const ser = keys.map((k, i) => {
    const g = groups[k];
    return { c: cols[i], pts: g.punkte.filter(p => p[0] != null && p[1] != null),
      tip: p => `<b>${labelFn(k)}</b><br>precision ${pc(p[1])} · recall ${pc(p[0])}<br><small>days with chance ≥ ${pc(p[2])}</small>` };
  });
  const base = groups[keys[0]].anteil;
  xy(el, ser, { xr: [0, 1], yr: [0, 1], xt: [0, 0.2, 0.4, 0.6, 0.8, 1], yt: [0, 0.2, 0.4, 0.6, 0.8, 1], xf: v => Math.round(v * 100) + "%",
    yf: v => Math.round(v * 100) + "%", xl: "recall – share of Breva days caught", yl: "precision", aria: "Precision-recall curves",
    refs: [[0, base, 1, base]] });
}

function pr7(M) {
  const S = M.sieben, Ls = Object.keys(S).sort((a, b) => a - b);
  const lab = L => L === "1" ? "tomorrow" : `day ${L}`;
  prChart($("#pr7b"), Object.fromEntries(Ls.map(L => [L, S[L].breva])), lab);
  prChart($("#pr7l"), Object.fromEntries(Ls.filter(L => S[L].lang).map(L => [L, S[L].lang])), lab);
  const cols = RAMP(Ls.length);
  legend($("#pr7Leg"), [...Ls.map((L, i) => [lab(L), cols[i]]), ["share of Breva days (guessing)", "var(--muted)", true]]);
  $("#prTab").innerHTML = `<thead><tr><th>Days ahead</th><th>AP Breva</th><th>recall at ≥ 70 % precision</th><th>AP long</th><th>recall long at ≥ 70 %</th></tr></thead><tbody>` +
    Ls.map(L => `<tr><th>${lab(L)}</th><td>${de(S[L].breva.ap)}</td><td>${pc(S[L].breva.r70)}</td><td>${de(S[L].lang?.ap)}</td><td>${pc(S[L].lang?.r70)}</td></tr>`).join("") + "</tbody>";
}

function eichung(M) {
  const S = M.sieben, pick = ["1", "3", "5"].filter(L => S[L]);
  const lab = L => L === "1" ? "tomorrow" : `day ${L}`;
  for (const [el, k] of [["#calB", "breva"], ["#calL", "lang"]]) {
    const ser = pick.filter(L => S[L][k]).map((L, i) => ({
      c: C[i], dots: true, r: p => Math.max(3, Math.min(9, Math.sqrt(p[2]) * 0.7)),
      pts: S[L][k].eichung.map(e => [e[0], e[1], e[2]]),
      tip: p => `<b>${lab(L)}</b><br>chance shown ${pc(p[0])} → real ${pc(p[1])}<br><small>${p[2]} days</small>`
    }));
    xy($(el), ser, { xr: [0, 1], yr: [0, 1], xt: [0, 0.2, 0.4, 0.6, 0.8, 1], yt: [0, 0.2, 0.4, 0.6, 0.8, 1], xf: v => Math.round(v * 100) + "%",
      yf: v => Math.round(v * 100) + "%", xl: "chance shown in the app", yl: "share with a real Breva", refs: [[0, 0, 1, 1]], aria: "Calibration" });
  }
  legend($("#calLeg"), [...pick.map((L, i) => [lab(L), C[i]]), ["perfect calibration", "var(--muted)", true]]);
}

function heute(M) {
  const Q = M.heute_quellen; if (!Q) return;
  for (const [el, z] of [["#hQuelle", "14"], ["#hQuelleL", "lang"]]) {
    const q = Q[z]; if (!q) continue;
    const hs = Object.keys(q).map(Number).sort((a, b) => a - b);
    const ser = [["forecast + measurements", "alles", C[0]], ["forecast only", "vorhersage", C[1]], ["measurements only", "messungen", C[2]]].map(([n, k, c]) => ({
      c, dots: true, dash: k === "vorhersage", pts: hs.map(h => [h, q[h][k]]).filter(p => p[1] != null),
      tip: p => `<b>${n}</b>, ${p[0]}:00<br>AUC ${de(p[1])}` }));
    xy($(el), ser, { xr: [6.5, 15.5], yr: [0.5, 1], xt: hs, yt: [0.5, 0.6, 0.7, 0.8, 0.9, 1], xf: v => v + ":00", yf: v => v.toFixed(1),
      xl: "time of day", yl: "AUC", aria: "Today model skill by hour", H: 230 });
  }
  legend($("#hQuelleLeg"), [["forecast + measurements", C[0]], ["forecast only", C[1], true], ["measurements only", C[2]]]);
  const Hh = M.heute || {};
  const hs = Object.keys(Hh["14"] || {}).sort((a, b) => b - a);          // latest hour = darkest
  const lab = h => `${h}:00`;
  if (Hh["14"]) prChart($("#prHb"), Object.fromEntries(hs.map(h => [h, Hh["14"][h]])), lab);
  if (Hh.lang) prChart($("#prHl"), Object.fromEntries(hs.map(h => [h, Hh.lang[h]])), lab);
  const cols = RAMP(hs.length);
  legend($("#prHLeg"), [...hs.map((h, i) => [lab(h), cols[i]]), ["share of Breva days (guessing)", "var(--muted)", true]]);
  $("#hFeatTab").innerHTML = "<thead><tr><th>Measured</th><th>Detail</th></tr></thead><tbody>" +
    M.features_heute.map(f => { const [n, s] = hname(f); return `<tr><th>${esc(n)}</th><td>${esc(s)}</td></tr>`; }).join("") +
    `<tr class="fa"><th>+ the 37 forecast variables</th><td>for today, as in the 7-day model</td></tr></tbody>`;
}

fetch("modell.json").then(r => r.json()).then(M => {
  kpis(M); faktoren(M); vorlauf(M); pr7(M); eichung(M); heute(M);
}).catch(e => { document.querySelector("main").insertAdjacentHTML("afterbegin", `<p class="status err">Model data could not be loaded (${esc(e.message)}).</p>`); });
