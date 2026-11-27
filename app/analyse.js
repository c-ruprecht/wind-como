/* Wind analysis & Breva: charts and tables from analyse.json (training/export_analyse.py). */
"use strict";
const $ = s => document.querySelector(s);
const de = (x, n = 1) => x == null ? "–" : Number(x).toFixed(n);
const pct = p => p == null ? "–" : Math.round(p * 100) + " %";
const MON = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const COL = { samolaco: "#0b6e8a", vercana: "#e08a1e", colico: "#6a2f8f", morbegno: "#2f9d5c", sansiro: "#8a6a00", como: "#b3261e" };
const KCOL = { "Breva lang": "#1f6f43", "Breva kurz": "#5cb87a", "Grenzfall": "#e6cf86", "Breva": "#1f8a4c", "Breva schwach": "#8fd48a", "ruhig": "#c7d2d8", "Nordföhn": "#4b7fbf", "Regen/Gewitter": "#7d6aa8", "synoptisch": "#e0a93b" };
/* class and variable names in analyse.json are German keys – shown in English */
const KNAME = { "Breva lang": "long Breva (5+ h)", "Breva kurz": "short Breva (2–4 h)", "Grenzfall": "near miss", "Breva": "Breva", "Breva schwach": "weak Breva", "ruhig": "calm", "Nordföhn": "north foehn", "Regen/Gewitter": "rain/thunderstorm", "synoptisch": "synoptic" };
const FNAME = { wind_see_15_sued: "South wind over the lake (model, 15:00)", wind_see_15: "Wind over the lake (model, 15:00)",
  wind_milano_12: "Wind in the Po plain (Milan, 12:00)", dp_tag_minus_nacht: "Valley low forms during the day (gradient 15:00 minus 6:00)",
  taupunktdiff_milano: "Dry air (dew-point spread, Milan)", bodenfeuchte_milano: "Soil moisture, Po plain", wolken_tief_see: "Low clouds over the lake",
  dt_tal_po: "Temperature valley minus plain", geo_aus_sued: "Large-scale flow from the south", dp_po_tal_15: "Pressure gradient plain → valley (15:00)",
  dp_bergamo_sondrio_15: "Pressure gradient Bergamo → Sondrio (15:00)", rad_chiavenna: "Sun in the valley (Chiavenna)", regen_see: "Rain on the lake",
  dp_zurich_milano_12: "North-foehn index (Zurich − Milan)", doy_sin: "Season (spring–summer)", doy_cos: "Season (winter vs summer)",
  rad_milano: "Sun in the plain (Milan)", rad_see: "Sun over the lake", rad_spaet_chiavenna: "Late-afternoon sun in the valley",
  luft_minus_see_t30: "Warm air over a cool lake", tmax_engadin: "Max. temperature Engadine", tmax_chiavenna: "Max. temperature Chiavenna",
  tmax_milano: "Max. temperature Milan", tmax_sondrio: "Max. temperature Sondrio", tmax_bergamo: "Max. temperature Bergamo",
  geo_staerke: "Large-scale wind strength", drucktendenz_24h: "Pressure rising over 24 h", dp_po_tal_18: "Pressure gradient plain → valley (18:00)",
  regen_chiavenna: "Rain in the valley", wolken_chiavenna: "Clouds in the valley" };
const fname = r => FNAME[r.merkmal] || r.name;

function line(series, xs, { W = 360, H = 190, ymin = 0, ymax = null, ylab = "", fmt = v => v } = {}) {
  const L = 30, B = 22, T = 8, R = 8;
  const all = series.flatMap(s => s.v).filter(v => v != null);
  const top = ymax ?? Math.ceil(Math.max(...all, 1) / 2) * 2;
  const x = i => L + i * (W - L - R) / Math.max(xs.length - 1, 1);
  const y = v => T + (1 - (v - ymin) / (top - ymin)) * (H - T - B);
  let s = `<svg viewBox="0 0 ${W} ${H}" class="chart">`;
  const step = (top - ymin) / 4;
  for (let v = ymin; v <= top + 1e-9; v += step) s += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" class="grid"/><text x="${L - 4}" y="${y(v) + 3}" class="ax" text-anchor="end">${fmt(v)}</text>`;
  xs.forEach((l, i) => { if (l !== "") s += `<text x="${x(i)}" y="${H - 6}" class="ax" text-anchor="middle">${l}</text>`; });
  for (const se of series) {
    let d = "", pen = false;
    se.v.forEach((v, i) => { if (v == null) { pen = false; return; } d += `${pen ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`; pen = true; });
    s += `<path d="${d}" fill="none" stroke="${se.c}" stroke-width="${se.w ?? 2}" ${se.dash ? 'stroke-dasharray="4 3"' : ""}/>`;
    se.v.forEach((v, i) => { if (v != null && se.dots) s += `<circle cx="${x(i)}" cy="${y(v)}" r="2.5" fill="${se.c}"><title>${se.n}: ${fmt(v)}</title></circle>`; });
  }
  if (ylab) s += `<text x="4" y="${T + 6}" class="ax">${ylab}</text>`;
  return s + "</svg>";
}
function stacked(rows, labels, order, { W = 360, H = 190 } = {}) {
  const L = 26, B = 22, T = 8, bw = (W - L - 8) / labels.length;
  const tot = labels.map((_, i) => order.reduce((a, k) => a + (rows[k]?.[i] ?? 0), 0));
  const top = Math.ceil(Math.max(...tot) / 5) * 5;
  const y = v => T + (1 - v / top) * (H - T - B);
  let s = `<svg viewBox="0 0 ${W} ${H}" class="chart">`;
  for (let v = 0; v <= top; v += top / 5) s += `<line x1="${L}" x2="${W - 8}" y1="${y(v)}" y2="${y(v)}" class="grid"/><text x="${L - 4}" y="${y(v) + 3}" class="ax" text-anchor="end">${Math.round(v)}</text>`;
  labels.forEach((l, i) => {
    let acc = 0;
    for (const k of order) {
      const v = rows[k]?.[i] ?? 0; if (!v) continue;
      s += `<rect x="${L + i * bw + bw * 0.15}" y="${y(acc + v)}" width="${bw * 0.7}" height="${y(acc) - y(acc + v)}" fill="${KCOL[k]}"><title>${l}: ${KNAME[k] || k} ${de(v)} days</title></rect>`;
      acc += v;
    }
    s += `<text x="${L + i * bw + bw / 2}" y="${H - 6}" class="ax" text-anchor="middle">${l}</text>`;
  });
  return s + "</svg>";
}
function bars(vals, labels, { W = 360, H = 150, color = "#0b6e8a", fmt = v => v } = {}) {
  const L = 26, B = 22, T = 10, bw = (W - L - 8) / labels.length, top = Math.max(...vals, 1) * 1.15;
  const y = v => T + (1 - v / top) * (H - T - B);
  let s = `<svg viewBox="0 0 ${W} ${H}" class="chart">`;
  vals.forEach((v, i) => {
    s += `<rect x="${L + i * bw + bw * 0.15}" y="${y(v)}" width="${bw * 0.7}" height="${y(0) - y(v)}" rx="2" fill="${color}"><title>${labels[i]}: ${fmt(v)}</title></rect>`;
    s += `<text x="${L + i * bw + bw / 2}" y="${y(v) - 3}" class="ax" text-anchor="middle">${fmt(v)}</text>`;
    s += `<text x="${L + i * bw + bw / 2}" y="${H - 6}" class="ax" text-anchor="middle">${labels[i]}</text>`;
  });
  return s + `<line x1="${L}" x2="${W - 8}" y1="${y(0)}" y2="${y(0)}" class="grid"/></svg>`;
}
const legend = items => items.map(([n, c, dash]) => `<span><i class="ln" style="background:${dash ? "transparent" : c};${dash ? `border-top:2px dashed ${c};height:0` : ""}"></i>${n}</span>`).join("");

function kpis(A) {
  const k = A.klassen_saison || {}, v = A.vortag || {}, V = A.vorlauf_neu;
  const breva = k["Breva kurz"] != null ? (k["Breva kurz"] || 0) + (k["Breva lang"] || 0) : k["Breva"];
  const items = [
    [de(breva, 0), "Breva days per year (14+ kn for 2 h or more)"],
    [de(k["Breva lang"], 0), "of them long (5 h or more)"],
    [pct(v.nach_breva), `Breva after a Breva day (otherwise ${pct(v.sonst)})`],
    [V ? de(V.breva[0], 2) : "–", `Skill tomorrow (AUC, March–October)${V ? `, day 4: ${de(V.breva[3], 2)}` : ""}`]
  ];
  $("#kpis").innerHTML = items.map(([a, b]) => `<div class="kpi"><b>${a}</b><span>${b}</span></div>`).join("");
}

function diurnal(A) {
  const hrs = Array.from({ length: 17 }, (_, i) => i + 6);
  const xs = hrs.map(h => h % 3 === 0 ? String(h) : "");
  const show = ["samolaco", "vercana", "colico"].filter(s => A.tagesgang[s]);
  const series = show.flatMap(s => [
    { n: A.tagesgang[s].name, c: COL[s], v: hrs.map(h => A.tagesgang[s].breva[h]), dots: true },
    { n: A.tagesgang[s].name + " other days", c: COL[s], v: hrs.map(h => A.tagesgang[s].sonst[h]), dash: true, w: 1.3 }]);
  $("#diurnal").innerHTML = line(series, xs, { ylab: "kn", fmt: v => Math.round(v) });
  $("#diurnalLeg").innerHTML = legend(show.map(s => [A.tagesgang[s].name, COL[s]]).concat([["other days", "#5a6e77", true]]));
}
function months(A) {
  const order = ["Breva lang", "Breva kurz", "Breva", "Breva schwach", "Grenzfall", "ruhig", "Nordföhn", "Regen/Gewitter", "synoptisch"].filter(k => A.klassen.klassen[k]);
  $("#months").innerHTML = stacked(A.klassen.klassen, A.klassen.monate.map(m => MON[m]), order);
  $("#monthsLeg").innerHTML = order.map(k => `<span><i class="sw" style="background:${KCOL[k]}"></i>${KNAME[k] || k}</span>`).join("");
  const ys = Object.keys(A.je_jahr);
  $("#years").innerHTML = bars(ys.map(y => A.je_jahr[y]), ys.map(y => "'" + y.slice(2)), { fmt: v => v });
  const kl = A.klima?.["14"];
  $("#seasonHint").innerHTML = kl ? `Usual, at least 2 h from 14 kn on the lake: ${Object.entries(kl).map(([m, o]) => `${MON[m]} ${pct(o.p)}`).join(", ")} of days. `
    + `The Breva is most reliable in spring, when the valleys already warm strongly but the plain is not yet hot and humid. In late summer calm days increase. `
    + `“Near miss”: south wind on the lake, but not 14 kn for 2 hours. “Rain/thunderstorm” and “north foehn”: disturbed days without a Breva.` : "";
}
const unit = f => f.startsWith("wind") || f.startsWith("geo") ? "kn" : f.startsWith("rad") ? "kWh/m²" : f.startsWith("tmax") || f.startsWith("tmin") ? "°C"
  : f.startsWith("dp_") || f.startsWith("druck") ? "hPa" : f.startsWith("luft_minus") || f.startsWith("taupunkt") ? "K" : f.startsWith("regen") ? "mm" : f.startsWith("wolken") ? "%" : "";
function faktoren(A) {
  const F = A.faktoren2;
  const eff = v => v == null ? "–" : `<span class="${v >= 0.15 ? "bp" : v <= -0.15 ? "bn" : ""}">${v > 0 ? "+" : ""}${de(v, 2)}</span>`;
  if (F) {
    $("#faktTab").innerHTML = `<thead><tr><th>Variable</th><th>calm</th><th>near miss</th><th>short Breva</th><th>long Breva</th><th>calm → Breva</th><th>short → long</th></tr></thead><tbody>`
      + F.filter(r => !r.merkmal.startsWith("doy")).map(r => `<tr><th>${r.eigen_lang ? "◆ " : ""}${FNAME[r.merkmal] || r.name}${unit(r.merkmal) ? ` <small>${unit(r.merkmal)}</small>` : ""}</th><td>${de(r.ruhig, 1)}</td><td>${de(r.grenzfall, 1)}</td><td>${de(r.kurz, 1)}</td><td>${de(r.lang, 1)}</td><td>${eff(r.eff_breva)}</td><td>${eff(r.eff_lang)}</td></tr>`).join("") + "</tbody>";
  }
  $("#warumTips").innerHTML = [
    "<b>South wind and sun</b>: the strongest signs are south wind over the lake in the weather model and sun in the valleys and the plain. The model's wind is far too weak – 2–3 kn on Breva days against 1 kn on calm days, while 15–20 kn blow on the water (a 25 km grid does not resolve the lake) – but its direction and trend are right.",
    "<b>Warm air over a cool lake, dry air, season</b>: spring and early summer, when the air warms faster than the lake, and a large dew-point spread in Milan – the sun heats the air instead of evaporating water.",
    "<b>No foehn, no rain, weak large-scale wind</b>: a strong large-scale flow, north foehn (Zurich − Milan) and rain stop the thermal circulation.",
    "<b>What makes it long</b>: more of the same (south wind, late-afternoon sun, dry air) plus a stronger pressure gradient from the plain into the valleys at 15:00 and rising pressure – a building high (◆).",
    "<b>Heat alone does not help</b>: Breva days are warmer than calm days (which are often cloudy), but short and long Breva days are equally warm – and among sunny days the very hottest have fewer Breva (table under “How it forms”)."
  ].map(t => `<li>${t}</li>`).join("");
}
function vorhersage(A) {
  const V = A.vorlauf || {}, N = A.vorlauf_neu;
  const pick = thr => (V[thr] || []).map(r => r.auc);
  const ser = [{ n: "≥ 14 kn", c: "#0b6e8a", v: pick("14"), dots: true }, { n: "≥ 18 kn", c: "#e08a1e", v: pick("18"), dots: true }].filter(x => x.v.length);
  if (N) {
    const ser2 = [{ n: "Breva day", c: "#0b6e8a", v: N.breva, dots: true }, { n: "long Breva", c: "#e08a1e", v: N.lang, dots: true }];
    $("#lead").innerHTML = line(ser2, N.vorlauf.map(String), { ymin: 0.5, ymax: 1, fmt: v => de(v, 2) });
    $("#leadLeg").innerHTML = legend(ser2.map(x => [x.n, x.c])) + "<span>x: days ahead · real ECMWF forecasts 2024–2026</span>";
  } else {
    const labs = ["perfect", "1", "2", "3", "4", "5", "6", "7"];
    $("#lead").innerHTML = line(ser, labs, { ymin: 0.5, ymax: 1, fmt: v => de(v, 2) });
    $("#leadLeg").innerHTML = legend(ser.map(x => [x.n, x.c])) + "<span>x: days ahead (“perfect” = with the weather as it was)</span>";
  }
  const T = A.timing || {}, hrs = Object.keys(Object.values(T)[0] || {});
  const q = v => v == null ? "" : v >= 0.8 ? "q3" : v >= 0.7 ? "q2" : v >= 0.6 ? "q1" : "q0";
  const nm = { samolaco: "Samolaco*", vercana: "Vercana", colico: "Colico", morbegno: "Morbegno" };
  $("#timing").innerHTML = `<thead><tr><th>Station</th>${hrs.map(h => `<th>${h}:00</th>`).join("")}</tr></thead><tbody>`
    + Object.entries(T).map(([st, r]) => `<tr><th>${nm[st] || st}</th>${hrs.map(h => `<td class="${q(r[h])}">${de(r[h], 2)}</td>`).join("")}</tr>`).join("")
    + `</tbody>`;
  const H = A.heute;
  $("#heuteTab").innerHTML = (H ? `<h3>Today model</h3><div class="tscroll"><table class="atab num"><thead><tr><th>As of</th><th>Target</th><th>AUC overall</th><th>forecast only</th><th>measurements only</th></tr></thead><tbody>`
    + H.map(r => `<tr><th>${r.uhr}:00</th><td>${r.ziel === "lang" ? "long Breva (≥ 5 h)" : r.ziel != null ? "Breva day" : `≥ ${r.schwelle} kn`}</td><td>${de(r.auc, 2)}</td><td>${de(r.auc_saison_nur_vorhersage ?? r.auc_nur_vorhersage, 2)}</td><td>${de(r.auc_saison_nur_messungen ?? r.auc_nur_messungen, 2)}</td></tr>`).join("")
    + `</tbody></table></div>` : "")
    + `<p class="hint">* Samolaco helps define the Breva days; against the satellite its midday values are hardly better than those of the other stations (see model check). Vercana (980 m above Domaso) is the first independent station to turn south-west – from 11:00 it is a clear sign. For “go today?” the today model combines the forecast with these measurements and the previous day.</p>`;
}
function stationen(A) {
  const nm = { samolaco: "Samolaco (Pian di Spagna, 206 m)", colico: "Colico (La Madoneta, 229 m)", morbegno: "Morbegno (Valtellina)", vercana: "Vercana (980 m)",
    sansiro: "San Siro (1285 m)", canzo: "Canzo (1233 m)", como: "Como", lecco: "Lecco", valmadrera: "Valmadrera" };
  $("#stTab").innerHTML = `<thead><tr><th>Station</th><th>Evenings</th><th>Correlation r</th><th>Factor lake/station</th><th>Skill (AUC)</th></tr></thead><tbody>`
    + (A.stationen || []).filter(r => !r.station.startsWith("Modell")).map(r => `<tr><th>${nm[r.station] || r.station}</th><td>${r.n}</td><td>${de(r.r, 2)}</td><td>× ${de(r.verhaeltnis_see_zu_station, 2)}</td><td>${de(r.auc_see_ab_12kn, 2)}</td></tr>`).join("")
    + "</tbody>";
  $("#sfak").textContent = de(A.satfaktor_samolaco, 2);
  if ($("#cfak")) $("#cfak").textContent = de(A.satfaktor_colico, 2);
}
function spots(A) {
  const S = A.spot_zu_see || {};
  const ids = SPOTS.map(s => s.id).filter(i => S[i]);
  $("#spotbars").innerHTML = `<figure><figcaption>Spot relative to the upper-lake average on Breva evenings</figcaption>${bars(ids.map(i => S[i]), ids.map(i => SPOTS.find(s => s.id === i).short), { fmt: v => de(v, 2), H: 140 })}</figure>`;
}
function map(A) {
  const o = A.overlay;
  $("#anLegend").innerHTML = `<span class="grad"></span><small>0</small><small style="margin-left:auto">14</small><small style="margin-left:auto">28 kn</small>`;
  if (!window.maplibregl || !o) { $("#anmap").innerHTML = '<p class="maperr">Map not available.</p>'; return; }
  const m = new maplibregl.Map({ container: "anmap", style: "https://tiles.openfreemap.org/styles/liberty", center: [9.33, 46.1], zoom: 10.4,
    attributionControl: { compact: true }, cooperativeGestures: true });
  m.on("load", () => {
    const [w, s, e, n] = o.bbox, first = m.getStyle().layers.find(l => l.type === "symbol");
    m.addSource("breva", { type: "image", url: o.bild, coordinates: [[w, n], [e, n], [e, s], [w, s]] });
    m.addLayer({ id: "breva", type: "raster", source: "breva", paint: { "raster-opacity": 0.85, "raster-resampling": "nearest" } }, first && first.id);
    for (const sp of SPOTS) {
      const el = document.createElement("div"); el.className = "spot-mk";
      el.innerHTML = `<span class="dot"></span><span class="lab"><b>${sp.short}</b><span>×${de(A.spot_zu_see?.[sp.id], 2)}</span></span>`;
      new maplibregl.Marker({ element: el, anchor: "left", offset: [-8, 0] }).setLngLat([sp.lon, sp.lat]).addTo(m);
    }
  });
}

fetch("analyse.json").then(r => r.json()).then(A => {
  kpis(A); map(A); spots(A); diurnal(A); months(A); faktoren(A); vorhersage(A); stationen(A);
  $("#stand").textContent = `Analysis as of ${A.stand} · data ${A.jahre} · ${A.sat_abende ?? "–"} Breva evenings in satellite images.`;
}).catch(e => { document.querySelector("main").insertAdjacentHTML("afterbegin", `<p class="status err">analyse.json not loaded (${e.message}).</p>`); });
