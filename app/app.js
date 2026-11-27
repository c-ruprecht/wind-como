/* Breva – Kitewind oberer Comer See. Holt alles direkt im Browser (Open-Meteo, ARPA Lombardia), kein Server.
   Erste Version: Breva-Zeichen aus den Wettermodellen (vorläufig, noch ohne trainiertes Modell),
   Breva-Vorhersage (7 Tage + heute), Stationsmessungen, Breva-Bild aus Sentinel-1. */
"use strict";

const DEMO = new URLSearchParams(location.search).has("demo");
const MODELS = { icon: "icon_seamless", ecmwf: "ecmwf_ifs025" };
const MODEL_LABEL = { icon: "ICON", ecmwf: "ECMWF" };
const VARS = ["wind_speed_10m", "wind_direction_10m", "wind_gusts_10m", "temperature_2m", "dew_point_2m", "pressure_msl",
  "shortwave_radiation", "cloud_cover", "precipitation"];
const MS2KN = 1 / 0.514444;
const ARPA = "https://www.dati.lombardia.it/resource/647i-nhxk.json";
const CACHE_KEY = "breva-cache-v1";

const state = {
  fc: null, obs: {}, info: null,
  model: load("model", "icon"), thr: Number(load("thr", 14)) === 18 ? 18 : 14,
  spot: load("spot", "gera_lario"), day: 0, map: null, markers: [], layer: load("layer", "map"),
  mfc: null,        // Modellpunkte (ECMWF, mit 31 Tagen Vergangenheit)
  M: null,          // { man, m14, m18, heute, h: {"9_14": Modell, …} }
  hourly: null      // Stundenmittel der Stationen { station: { "YYYY-MM-DDTHH": {kn, dir} } }
};

/* ---------- Helfer ---------- */
function load(k, d) { try { return localStorage.getItem("breva-" + k) ?? d; } catch (e) { return d; } }
function save(k, v) { try { localStorage.setItem("breva-" + k, v); } catch (e) {} }
const $ = s => document.querySelector(s);
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const compass = d => d == null ? "" : ["N","NNO","NO","ONO","O","OSO","SO","SSO","S","SSW","SW","WSW","W","WNW","NW","NNW"][Math.round((((d % 360) + 360) % 360) / 22.5) % 16];
const inSec = (d, [a, b]) => d != null && (a <= b ? d >= a && d <= b : d >= a || d <= b);
const arrow = (dir, cls = "arrow") => `<svg class="${cls}" viewBox="0 0 20 20" aria-hidden="true"><g transform="rotate(${(dir + 180) % 360} 10 10)"><path d="M10 1 L15 11 L11 9.5 L11 19 L9 19 L9 9.5 L5 11 Z"/></g></svg>`;
const fmtTime = d => d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Rome" });
const de = (x, n = 1) => x.toFixed(n).replace(".", ",");
const pct = p => p == null ? "–" : Math.round(p * 100) + " %";
function dayLabel(dateStr, i) {
  const d = new Date(dateStr + "T12:00:00");
  if (i === 0) return "Heute";
  if (i === 1) return "Morgen";
  return d.toLocaleDateString("de-DE", { weekday: "short", day: "numeric", month: "numeric" });
}
const isWeekend = s => [0, 6].includes(new Date(s + "T12:00:00").getDay());

async function fetchJSON(url, timeoutMs = 25000) {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), timeoutMs);
  try {
    const r = await fetch(url, { signal: ctl.signal });
    const body = await r.json().catch(() => null);
    if (!r.ok) throw new Error((body && (body.reason || body.message)) || `${r.status} ${r.statusText}`);
    return body;
  } finally { clearTimeout(t); }
}

/* ---------- Vorhersage (Open-Meteo, ICON + ECMWF) ---------- */
async function fetchForecast() {
  const places = [...SPOTS, ...POINTS];
  const p = new URLSearchParams({
    latitude: places.map(s => s.lat).join(","), longitude: places.map(s => s.lon).join(","),
    hourly: VARS.join(","), daily: "sunrise,sunset", models: Object.values(MODELS).join(","),
    wind_speed_unit: "kn", timezone: "Europe/Rome", forecast_days: "7"
  });
  let res = await fetchJSON(DEMO ? "demo/forecast.json" : "https://api.open-meteo.com/v1/forecast?" + p);
  if (!Array.isArray(res)) res = [res];
  if (res.length < places.length) throw new Error(`Open-Meteo lieferte ${res.length} statt ${places.length} Orte`);
  const parse = r => {
    const h = r.hourly;
    const o = { time: h.time, sunrise: {}, sunset: {} };
    (r.daily?.time || []).forEach((d, k) => {
      const pick = n => r.daily[n]?.[k] ?? Object.entries(r.daily).find(([key]) => key.startsWith(n + "_"))?.[1]?.[k] ?? null;
      o.sunrise[d] = pick("sunrise"); o.sunset[d] = pick("sunset");
    });
    for (const [key, m] of Object.entries(MODELS)) {
      o[key] = {};
      for (const v of VARS) o[key][v] = h[`${v}_${m}`] || h[v] || [];
    }
    return o;
  };
  const spots = {}, points = {};
  SPOTS.forEach((s, i) => { spots[s.id] = parse(res[i]); });
  POINTS.forEach((s, i) => { points[s.id] = parse(res[SPOTS.length + i]); });
  return { spots, points, fetched: new Date().toISOString() };
}

/* ---------- Vorhersage an den Modellpunkten (ECMWF, wie im Training) ---------- */
async function fetchModelPoints() {
  const ids = Object.keys(MODEL_POINTS);
  const p = new URLSearchParams({
    latitude: ids.map(k => MODEL_POINTS[k][0]).join(","), longitude: ids.map(k => MODEL_POINTS[k][1]).join(","),
    hourly: MODEL_VARS.join(","), models: "ecmwf_ifs025", wind_speed_unit: "kn", timezone: "Europe/Rome",
    past_days: "31", forecast_days: "7"
  });
  let res = await fetchJSON(DEMO ? "demo/points.json" : "https://api.open-meteo.com/v1/forecast?" + p);
  if (!Array.isArray(res)) res = [res];
  const H = {};
  ids.forEach((k, i) => {
    const h = res[i]?.hourly; if (!h) return;
    H[k] = { time: h.time };
    for (const v of MODEL_VARS) H[k][v] = h[v] || h[`${v}_ecmwf_ifs025`] || [];
  });
  return H;
}
async function loadModels() {
  const man = await fetchJSON("model/manifest.json");
  const M = { man, h: {} };
  const jobs = Object.entries(man.files).map(([thr, f]) => fetchJSON("model/" + f, 60000).then(m => { M["m" + thr] = m; }));
  jobs.push(fetchJSON("model/heute.json").then(async H => {
    M.heute = H;
    await Promise.all(Object.entries(H.files).map(([k, f]) => fetchJSON("model/" + f, 60000).then(m => { M.h[k] = m; })));
  }).catch(e => console.warn("Heute-Modell", e)));
  await Promise.all(jobs);
  return M;
}

/* ---------- Messungen (ARPA Lombardia, 10-Minuten-Werte, Zeit = UTC+1) ---------- */
async function fetchObs() {
  const ids = STATIONS.flatMap(s => [s.speed, s.dir]);
  const since = new Date(Date.now() + 3600e3 - 44 * 3600e3).toISOString().slice(0, 19);  // UTC+1, ab gestern früh
  const q = new URLSearchParams({ $where: `idsensore in(${ids.map(i => `'${i}'`).join(",")}) AND data > '${since}'`,
    $order: "data DESC", $limit: "20000" });
  const rows = await fetchJSON(DEMO ? "demo/arpa.json" : `${ARPA}?${q}`);
  const out = {};
  for (const st of STATIONS) {
    const ser = id => rows.filter(r => Number(r.idsensore) === id && Number(r.valore) > -900 && (r.stato ?? "VA") !== "NV")
      .map(r => ({ t: new Date(r.data.slice(0, 19) + "+01:00"), v: Number(r.valore) })).sort((a, b) => a.t - b.t);
    const sp = ser(st.speed), di = ser(st.dir);
    if (!sp.length) continue;
    const last = sp[sp.length - 1].t;
    const recent = sp.filter(x => last - x.t <= 20 * 60e3);                // Mittel der letzten 30 min (3 Werte)
    const dmap = new Map(di.map(x => [x.t.getTime(), x.v]));
    let u = 0, v = 0, n = 0;
    for (const x of recent) {
      const d = dmap.get(x.t.getTime());
      if (d == null || d > 360) continue;
      u += -x.v * Math.sin(d * Math.PI / 180); v += -x.v * Math.cos(d * Math.PI / 180); n++;
    }
    const kn = recent.reduce((a, x) => a + x.v, 0) / recent.length * MS2KN;
    const dir = n ? (Math.atan2(-u, -v) * 180 / Math.PI + 360) % 360 : null;
    const hourAgo = sp.filter(x => last - x.t >= 50 * 60e3 && last - x.t <= 70 * 60e3);
    const kn1h = hourAgo.length ? hourAgo.reduce((a, x) => a + x.v, 0) / hourAgo.length * MS2KN : null;
    out[st.id] = { kn, dir, time: last, kn1h, series: sp.filter(x => last - x.t <= 6 * 3600e3).map(x => ({ t: x.t, kn: x.v * MS2KN })),
                   hourly: hourlyMeans(sp, dmap) };
  }
  return out;
}
/* Stundenmittel wie im Training (download_arpa.py): Stunde endet zur vollen Stunde, mind. 3 von 6 Werten,
   Richtung als Vektormittel. Schlüssel "YYYY-MM-DDTHH" in Ortszeit (Europe/Rome). */
function localKey(d) {
  const s = d.toLocaleString("sv-SE", { timeZone: "Europe/Rome" });
  return s.slice(0, 10) + "T" + s.slice(11, 13);
}
function hourlyMeans(sp, dmap) {
  const g = new Map();
  for (const x of sp) {
    const end = new Date(Math.ceil(x.t.getTime() / 3600e3) * 3600e3);
    const k = localKey(end);
    if (!g.has(k)) g.set(k, []);
    g.get(k).push(x);
  }
  const out = {};
  for (const [k, xs] of g) {
    if (xs.length < 3) continue;
    let u = 0, v = 0, n = 0;
    for (const x of xs) { const d = dmap.get(x.t.getTime()); if (d == null || d > 360) continue;
      u += -x.v * Math.sin(d * Math.PI / 180); v += -x.v * Math.cos(d * Math.PI / 180); n++; }
    out[k] = { kn: xs.reduce((a, x) => a + x.v, 0) / xs.length * MS2KN, dir: n ? (Math.atan2(-u, -v) * 180 / Math.PI + 360) % 360 : null };
  }
  return out;
}

/* ---------- Breva-Zeichen je Tag (vorläufig, Schwellen aus ERA5 2014–2026, breva_events.py analyse) ---------- */
function dayIdx(o, date, h0, h1) { return o.time.map((t, i) => [t, i]).filter(([t]) => t.slice(0, 10) === date && +t.slice(11, 13) >= h0 && +t.slice(11, 13) <= h1).map(([, i]) => i); }
function atHour(o, m, v, date, h) { const i = o.time.indexOf(`${date}T${String(h).padStart(2, "0")}:00`); return i < 0 ? null : o[m][v][i] ?? null; }
const mean = a => { const b = a.filter(x => x != null); return b.length ? b.reduce((s, x) => s + x, 0) / b.length : null; };
const sum = a => { const b = a.filter(x => x != null); return b.length ? b.reduce((s, x) => s + x, 0) : null; };

function brevaSigns(date, m) {
  const P = state.fc.points, see = P.see, mi = P.milano, ch = P.chiavenna, zu = P.zurich;
  const idx = dayIdx(see, date, 13, 17);
  const sued = mean(idx.map(i => see[m].wind_speed_10m[i] == null ? null :
    see[m].wind_speed_10m[i] * Math.cos((see[m].wind_direction_10m[i] - 200) * Math.PI / 180)));
  const p = (o, h) => atHour(o, m, "pressure_msl", date, h);
  const dp = p(mi, 15) != null && p(ch, 15) != null ? p(mi, 15) - p(ch, 15) : null;
  const rad = sum(dayIdx(ch, date, 9, 17).map(i => ch[m].shortwave_radiation[i])) ;
  const foehn = p(zu, 12) != null && p(mi, 12) != null ? p(zu, 12) - p(mi, 12) : null;
  const rain = (sum(dayIdx(see, date, 11, 19).map(i => see[m].precipitation[i])) ?? 0) + (sum(dayIdx(ch, date, 11, 19).map(i => ch[m].precipitation[i])) ?? 0);
  const t13 = atHour(mi, m, "temperature_2m", date, 13), d13 = atHour(mi, m, "dew_point_2m", date, 13);
  const td = t13 != null && d13 != null ? t13 - d13 : null;
  const parts = [
    { key: "sued", label: "Südwind am See (Modell)", w: 0.30, v: sued, s: sued == null ? null : clamp((sued - 0.5) / 3),
      txt: sued == null ? "–" : `${de(sued)} kn aus SSW` },
    { key: "dp", label: "Druckgefälle Ebene → Tal", w: 0.20, v: dp, s: dp == null ? null : clamp((dp + 3.2) / 2.2),
      txt: dp == null ? "–" : `Mailand – Chiavenna ${dp > 0 ? "+" : ""}${de(dp)} hPa` },
    { key: "sonne", label: "Sonne im Tal", w: 0.20, v: rad, s: rad == null ? null : clamp((rad / 1000 - 3.0) / 2.5),
      txt: rad == null ? "–" : `${de(rad / 1000)} kWh/m² Chiavenna` },
    { key: "foehn", label: "kein Nordföhn", w: 0.15, v: foehn, s: foehn == null ? null : clamp((4.5 - foehn) / 3.5),
      txt: foehn == null ? "–" : `Zürich – Mailand ${foehn > 0 ? "+" : ""}${de(foehn)} hPa` },
    { key: "trocken", label: "trockene Luft", w: 0.15, v: td, s: td == null ? null : clamp((td - 7) / 6),
      txt: td == null ? "–" : `Mailand Taupunktabstand ${de(td)} K` }
  ];
  const ok = parts.filter(x => x.s != null);
  if (!ok.length) return null;
  const base = ok.reduce((a, x) => a + x.w * x.s, 0) / ok.reduce((a, x) => a + x.w, 0);
  const rainF = rain < 0.5 ? 1 : rain < 2 ? 0.6 : 0.25;
  return { score: base * rainF, parts, rain, rainF };
}
const signalClass = s => s == null ? "r0" : s >= 0.65 ? "r4" : s >= 0.5 ? "r2" : s >= 0.35 ? "r1" : "r0";
const signalWord = s => s == null ? "–" : s >= 0.65 ? "gute Zeichen" : s >= 0.5 ? "möglich" : s >= 0.35 ? "schwach" : "eher nicht";
function climateP(date, thr) {
  const m = String(Number(date.slice(5, 7)));
  return state.info?.klima?.[String(thr)]?.[m] ?? null;
}

/* ---------- Modelle: 7 Tage und Heute ---------- */
let F7cache = null;
function features7() {
  if (!state.mfc || !state.M) return null;
  if (!F7cache) F7cache = BrevaModel.features(state.mfc, MODEL_POINTS);
  return F7cache;
}
function weekProb(date, i, thr) {
  const F = features7(), M = state.M; if (!F || !M || !M["m" + thr] || !F[date]) return null;
  const raw = BrevaModel.predictProba(M["m" + thr], BrevaModel.vec(F[date], M.man.features));
  const cal = M.man.calib[String(thr)] || {};
  return BrevaModel.calibrate(cal[String(i)] ?? cal["7"], raw);
}
const pClass = p => p == null ? "r0" : p >= 0.6 ? "r4" : p >= 0.4 ? "r2" : p >= 0.2 ? "r1" : "r0";
/* Breva-Call: Chance über der Schwelle, ab der das Modell in der Prüfung 2024–heute ≥ 80 % Präzision hatte */
function weekCall(i, thr, p) {
  const c = state.M?.man?.call?.[String(thr)]; const k = c && (c[String(i)] ?? c["7"]);
  return k && p != null && p >= k.schwelle ? k : null;
}
function heuteCall(H, thr) {
  if (!H || H.hour == null) return weekCall(0, thr, H?.p[thr]);
  const k = state.M?.heute?.call?.[`${H.hour}_${thr}`];
  return k && H.p[thr] != null && H.p[thr] >= k.schwelle ? k : null;
}
const callTip = c => `Breva-Call: Bei so hohen Werten gab es in der Prüfung 2024–heute in ${Math.round(c.praezision * 100)} % der Fälle wirklich Breva; erwischt werden so ${Math.round(c.trefferquote * 100)} % aller Breva-Tage.`;
const callTag = c => c ? `<span class="call" title="${callTip(c)}">Call</span>` : "";
function hourlyAll() {
  const h = {}; for (const st of STATIONS) if (state.obs[st.id]?.hourly) h[st.id] = state.obs[st.id].hourly; return h;
}
function shiftDate(d, n) { const t = new Date(d + "T12:00:00Z"); t.setUTCDate(t.getUTCDate() + n); return t.toISOString().slice(0, 10); }
function heute() {
  const M = state.M, H = M?.heute, F = features7(); const ds = days();
  if (!H || !F || !ds.length) return null;
  const today = ds[0], hourly = hourlyAll();
  const have = h => ["vercana", "samolaco", "colico"].some(st => hourly[st]?.[`${today}T${String(h).padStart(2, "0")}`]);
  const hour = [...H.hours].reverse().find(h => have(h)) ?? null;
  const g = BrevaModel.brevaDay(hourly, shiftDate(today, -1), H.faktor);
  const res = { hour, gestern: g, today, p: {}, pForecast: {}, obs: null };
  for (const thr of THRESHOLDS) res.pForecast[thr] = weekProb(today, 0, thr);
  if (hour == null) { res.p = { ...res.pForecast }; return res; }
  const obs = BrevaModel.obsFeatures(hourly, today, hour);
  res.obs = obs;
  const x = { ...F[today], ...obs, gestern_breva: g ? g.breva : NaN, gestern_max: g ? g.max : NaN };
  for (const thr of THRESHOLDS) {
    const m = M.h[`${hour}_${thr}`]; if (!m) continue;
    res.p[thr] = BrevaModel.calibrate(H.calib[`${hour}_${thr}`], BrevaModel.predictProba(m, BrevaModel.vec(x, H.features)));
  }
  return res;
}

/* ---------- Karte ---------- */
function initMap() {
  const map = new maplibregl.Map({ container: "map", style: "https://tiles.openfreemap.org/styles/liberty",
    center: [9.33, 46.11], zoom: 10.6, attributionControl: { compact: true }, cooperativeGestures: true });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.on("load", () => {
    const first = map.getStyle().layers.find(l => l.type === "symbol");
    map.addSource("s2", { type: "raster", tileSize: 256, maxzoom: 15,
      tiles: ["https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg"],
      attribution: "Sentinel-2 cloudless – https://s2maps.eu by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2020)" });
    map.addLayer({ id: "s2", type: "raster", source: "s2", layout: { visibility: "none" } }, first && first.id);
    state.map = map;
    addOverlay(); setLayer(state.layer); drawMarkers();
  });
}
function addOverlay() {
  const m = state.map, o = state.info?.overlay;
  if (!m || !o || m.getSource("breva")) return;
  const [w, s, e, n] = o.bbox;
  m.addSource("breva", { type: "image", url: o.bild, coordinates: [[w, n], [e, n], [e, s], [w, s]] });
  const first = m.getStyle().layers.find(l => l.type === "symbol");
  m.addLayer({ id: "breva", type: "raster", source: "breva", paint: { "raster-opacity": 0.85, "raster-resampling": "nearest" },
    layout: { visibility: "none" } }, first && first.id);
  setLayer(state.layer);
}
function setLayer(which) {
  state.layer = which; save("layer", which);
  for (const [id, key] of [["#btnMap", "map"], ["#btnSat", "sat"], ["#btnBreva", "breva"]]) {
    $(id).classList.toggle("on", which === key); $(id).setAttribute("aria-pressed", which === key);
  }
  $("#brevaLegend").hidden = which !== "breva";
  const m = state.map; if (!m) return;
  if (m.getLayer("s2")) m.setLayoutProperty("s2", "visibility", which === "sat" ? "visible" : "none");
  if (m.getLayer("breva")) m.setLayoutProperty("breva", "visibility", which === "breva" ? "visible" : "none");
}
function drawMarkers() {
  state.markers.forEach(m => m.remove()); state.markers = [];
  if (!state.map) return;
  const today = state.fc ? Object.keys(state.fc.points.see.sunrise)[0] : null;
  const sig = today ? brevaSigns(today, state.model) : null;
  for (const sp of SPOTS) {
    const el = document.createElement("button");
    el.type = "button";
    const pt = state.M && features7() && today ? weekProb(today, 0, state.thr) : null;
    el.className = `spot-mk mk-${pt != null ? pClass(pt) : signalClass(sig?.score)}${sp.id === state.spot ? " cur" : ""}`;
    el.innerHTML = `<span class="dot"></span><span class="lab"><b>${sp.short}</b></span>`;
    el.setAttribute("aria-label", sp.name);
    el.addEventListener("click", ev => { ev.stopPropagation(); selectSpot(sp.id); });
    state.markers.push(new maplibregl.Marker({ element: el, anchor: "left", offset: [-8, 0] }).setLngLat([sp.lon, sp.lat]).addTo(state.map));
  }
  for (const st of STATIONS) {
    const o = state.obs[st.id];
    const el = document.createElement("div");
    el.className = "stn-mk" + (o ? "" : " off");
    el.title = `${st.name} (${st.note})${o ? ", " + fmtTime(o.time) + " Uhr" : ", keine aktuellen Daten"}`;
    el.innerHTML = `${o && o.dir != null ? arrow(o.dir, "arrow big") : '<span class="sq"></span>'}<span class="lab"><b>${o ? Math.round(o.kn) + " kn " + compass(o.dir) : "–"}</b><small>${st.name}</small></span>`;
    state.markers.push(new maplibregl.Marker({ element: el, anchor: "center" }).setLngLat([st.lon, st.lat]).addTo(state.map));
  }
}

/* ---------- Jetzt ---------- */
function spark(series) {
  if (!series || series.length < 2) return "";
  const W = 120, H = 28, t0 = series[0].t, t1 = series[series.length - 1].t, mx = Math.max(16, ...series.map(x => x.kn));
  const pts = series.map(x => `${((x.t - t0) / Math.max(t1 - t0, 1) * W).toFixed(1)},${(H - x.kn / mx * H).toFixed(1)}`).join(" ");
  const y14 = H - 14 / mx * H;
  return `<svg class="spark" viewBox="0 0 ${W} ${H}" aria-hidden="true"><line x1="0" x2="${W}" y1="${y14}" y2="${y14}" class="l14"/><polyline points="${pts}"/></svg>`;
}
function drawNow() {
  const box = $("#now");
  const stn = STATIONS.map(st => {
    const o = state.obs[st.id];
    const breva = o && inSec(o.dir, st.sektor) && o.kn >= 2;
    const trend = o && o.kn1h != null ? (o.kn - o.kn1h >= 1.5 ? "↑" : o.kn1h - o.kn >= 1.5 ? "↓" : "→") : "";
    return `<li>${o && o.dir != null ? arrow(o.dir) : '<span class="arrow"></span>'}<span><b>${st.name}</b> <small>${st.note}</small></span>
      <span>${o ? `<b>${Math.round(o.kn)} kn</b> ${compass(o.dir)} ${trend} <small>${fmtTime(o.time)}${breva ? " · Breva-Richtung" : ""}</small>` : "keine Daten"}</span>
      ${o ? spark(o.series) : "<span></span>"}</li>`;
  }).join("");
  const H = heute();
  const ds = days();
  const cl = ds.length ? climateP(ds[0], state.thr) : null;
  const fmtObs = v => v == null || !Number.isFinite(v) ? "–" : `${v >= 0 ? "" : "−"}${de(Math.abs(v))} kn`;
  const heuteHtml = H ? `<div class="heute">
      <div class="hcards">${THRESHOLDS.map(t => `<div class="hcard ${pClass(H.p[t])}"><span class="hp">${H.p[t] == null ? "–" : Math.round(H.p[t] * 100) + "\u00a0%"}${callTag(heuteCall(H, t))}</span>
        <span class="hl">Breva ≥ ${t} kn heute<br><small>mind. 2 h am Stück</small></span></div>`).join("")}</div>
      <p class="hint">${H.hour == null ? "Nur Vorhersage – Messungen fließen ab 9 Uhr ein (Modell 9, 11 und 13 Uhr)."
        : `Stand ${H.hour} Uhr: Vorhersage für heute + Messungen bis ${H.hour} Uhr + gestern. ${state.M.heute.hours.some(h => h > H.hour) ? `Neu um ${state.M.heute.hours.filter(h => h > H.hour).join(" und ")} Uhr.` : "Letzter Stand des Tages – ab jetzt zeigen die Stationen, wie es weitergeht."}`}</p>
      <ul class="hfak">
        <li><b>Vorhersage allein</b> (ECMWF, 7-Tage-Modell): ${THRESHOLDS.map(t => `≥${t}: ${pct(H.pForecast[t])}`).join(" · ")}</li>
        <li><b>Gestern Breva</b>: ${H.gestern == null ? "unbekannt" : H.gestern.breva ? `ja (bis ~${Math.round(H.gestern.max)} kn auf dem See)` : `nein (max ~${Math.round(H.gestern.max)} kn)`}
          <small>– nach einem Breva-Tag folgt in ${pct(state.M.heute.vortag_stat?.["1"])} der Fälle wieder einer, sonst in ${pct(state.M.heute.vortag_stat?.["0"])}</small></li>
        ${H.obs ? `<li><b>Breva-Richtung jetzt</b>: Vercana ${fmtObs(H.obs.vercana_jetzt)}, Samolaco ${fmtObs(H.obs.samolaco_jetzt)}, Colico ${fmtObs(H.obs.colico_jetzt)}, Morbegno ${fmtObs(H.obs.morbegno_jetzt)}
          <small>– Wind in Breva-Richtung, negativ = Gegenwind. Vercana dreht als erste auf Südwest.</small></li>
        <li><b>Tivano heute früh</b> (Samolaco aus Nord, 5–9 Uhr): ${fmtObs(H.obs.tivano_samolaco)}</li>` : ""}
        ${cl ? `<li><b>Üblich</b> im ${new Date(ds[0] + "T12:00:00").toLocaleDateString("de-DE", { month: "long" })}: ${pct(cl.p)} der Tage ≥ ${state.thr} kn</li>` : ""}
      </ul></div>` : "";
  box.innerHTML = `<div class="panel-head"><h2>Heute</h2><span class="meta">Lohnt es sich loszufahren?</span></div>
    ${heuteHtml}
    <h3>Stationen (ARPA Lombardia, letzte 6 h)</h3><ul class="stnlist">${stn}</ul>`;
  box.querySelectorAll("[data-spot]").forEach(e => e.addEventListener("click", () => selectSpot(e.dataset.spot)));
}

/* ---------- Woche ---------- */
function days() { return state.fc ? Object.keys(state.fc.points.see.sunrise).slice(0, 7) : []; }
function drawWeek() {
  const t = $("#week");
  const ds = days();
  if (!ds.length) { t.innerHTML = ""; return; }
  const head = ds.map((d, i) => `<th scope="col" class="${isWeekend(d) ? "we" : ""}">${i === 0 ? "Heute" : new Date(d + "T12:00:00").toLocaleDateString("de-DE", { weekday: "short" })}<br><small>${+d.slice(8)}.${+d.slice(5, 7)}.</small></th>`).join("");
  const S = ds.map(d => ({ d, sig: brevaSigns(d, state.model), cl: climateP(d, state.thr), season: SEASON.includes(Number(d.slice(5, 7))) }));
  const sigRow = S.map(({ d, sig, season }, i) => `<td class="cell ${season ? signalClass(sig?.score) : "r0 offs"}${isWeekend(d) ? " we" : ""}${i === state.day ? " sel" : ""}" data-day="${i}"
      title="${sig ? signalWord(sig.score) : ""}"><span class="v">${sig ? Math.round(sig.score * 100) : "–"}</span><span class="pd">${season ? signalWord(sig?.score) : "keine Saison"}</span></td>`).join("");
  const clRow = S.map(({ d, cl }, i) => `<td class="climc${isWeekend(d) ? " we" : ""}" data-day="${i}">${cl ? pct(cl.p) : "–"}</td>`).join("");
  const partRows = ["sued", "dp", "sonne", "foehn", "trocken"].map(k => {
    const lab = S[0].sig?.parts.find(p => p.key === k)?.label ?? k;
    return `<tr class="part"><th scope="row">${lab}</th>${S.map(({ sig }, i) => {
      const p = sig?.parts.find(x => x.key === k);
      return `<td data-day="${i}" title="${p?.txt ?? ""}"><span class="bar"><i style="width:${p?.s == null ? 0 : Math.round(p.s * 100)}%"></i></span></td>`; }).join("")}</tr>`;
  }).join("");
  const rainRow = S.map(({ sig }, i) => `<td data-day="${i}" class="rain">${sig == null ? "" : sig.rain >= 2 ? "🌧" : sig.rain >= 0.5 ? "🌦" : ""}</td>`).join("");
  const modelRow = state.M && features7() ? `<tr><th scope="row">Chance ≥ ${state.thr} kn<br><small>Breva-Modell, mind. 2 h</small></th>${S.map(({ d, season }, i) => {
      const p = weekProb(d, i, state.thr);
      return `<td class="cell ${season ? pClass(p) : "r0 offs"}${isWeekend(d) ? " we" : ""}${i === state.day ? " sel" : ""}" data-day="${i}"><span class="v">${p == null ? "–" : Math.round(p * 100) + "%"}</span>${season ? callTag(weekCall(i, state.thr, p)) : ""}</td>`; }).join("")}</tr>` : "";
  t.innerHTML = `<thead><tr><th scope="col" class="spotcol"></th>${head}</tr></thead><tbody>
    ${modelRow}
    <tr class="${modelRow ? "zeichen" : ""}"><th scope="row">Breva-Zeichen<br><small>0–100, ${MODEL_LABEL[state.model]}</small></th>${sigRow}</tr>
    <tr><th scope="row">Üblich ${state.thr}+ kn<br><small>Anteil Tage im Monat</small></th>${clRow}</tr>
    ${partRows}
    <tr class="part"><th scope="row">Regen 11–19 Uhr</th>${rainRow}</tr></tbody>`;
  t.querySelectorAll("[data-day]").forEach(e => e.addEventListener("click", () => { state.day = Number(e.dataset.day); drawWeek(); drawDetail(); }));
}

/* ---------- Detail: Stunden eines Tages am gewählten Spot ---------- */
const KN_SCALE = [[0, "k0"], [6, "k1"], [9, "k2"], [12, "k3"], [15, "k4"], [18, "k5"], [21, "k6"], [25, "k7"], [30, "k8"]];
const knCls = kn => { if (kn == null) return "kx"; let c = "k0"; for (const [v, k] of KN_SCALE) if (kn >= v) c = k; return c; };
function drawDetail() {
  const box = $("#detail");
  const ds = days(); if (!ds.length) { box.innerHTML = ""; return; }
  const date = ds[state.day] ?? ds[0];
  const sp = SPOTS.find(s => s.id === state.spot) || SPOTS[0];
  const o = state.fc.spots[sp.id];
  const hrs = dayIdx(o, date, 8, 20);
  const sig = brevaSigns(date, state.model);
  const row = (lab, fn, cls = "") => `<tr class="${cls}"><th scope="row">${lab}</th>${hrs.map(fn).join("")}</tr>`;
  const ratio = state.info?.spot_zu_see?.[sp.id];
  const cl = climateP(date, state.thr);
  box.innerHTML = `<div class="panel-head"><h2>${sp.name} · ${dayLabel(date, ds.indexOf(date))}</h2>
      <span class="meta">${sp.shore}${ratio ? ` · bei Breva ${ratio >= 1 ? "+" : ""}${Math.round((ratio - 1) * 100)} % gegenüber dem Mittel des oberen Sees` : ""}</span></div>
    <div class="spotpick" role="group" aria-label="Spot">${SPOTS.map(s => `<button type="button" class="seg${s.id === sp.id ? " on" : ""}" data-spot="${s.id}">${s.short}</button>`).join("")}</div>
    ${state.M && features7() ? `<p class="sigline"><b>Breva-Modell:</b> ${THRESHOLDS.map(t => { const p = weekProb(date, ds.indexOf(date), t);
      return `<span class="badge ${pClass(p)}">${p == null ? "–" : Math.round(p * 100) + "%"}</span> ≥ ${t} kn${callTag(weekCall(ds.indexOf(date), t, p))}`; }).join(" · ")}${
      sig && sig.rain >= 3 && (weekProb(date, ds.indexOf(date), 14) ?? 0) >= 0.3
        ? `<br><small>🌧 Südwind mit Regen: eher Wind vor einer Front als thermischer Breva – meist gleichmäßig, aber nass; auf Gewitter achten.</small>` : ""}</p>` : ""}
    ${sig ? `<p class="sigline"><span class="badge ${signalClass(sig.score)}">${Math.round(sig.score * 100)}</span> <b>${signalWord(sig.score)}</b>
      ${cl ? ` · üblich an ${pct(cl.p)} der Tage im Monat mind. 2 h ab ${state.thr} kn` : ""}${sig.rainF < 1 ? ` · Regen ${de(sig.rain)} mm dämpft` : ""}</p>
      <ul class="parts">${sig.parts.map(p => `<li><span class="bar"><i style="width:${p.s == null ? 0 : Math.round(p.s * 100)}%"></i></span> ${p.label}: ${p.txt}</li>`).join("")}</ul>` : ""}
    <div class="ftable-wrap"><table class="ftable"><tbody>
      ${row("Uhr", i => `<td>${o.time[i].slice(11, 13)}</td>`, "hrow")}
      ${Object.keys(MODELS).map(m => row("Richtung " + MODEL_LABEL[m], i => `<td title="${compass(o[m].wind_direction_10m[i])}">${o[m].wind_direction_10m[i] != null ? arrow(o[m].wind_direction_10m[i]) : ""}</td>`, "drow")
        + row(MODEL_LABEL[m] + " kn", i => { const k = o[m].wind_speed_10m[i]; return `<td class="${knCls(k)}">${k == null ? "–" : Math.round(k)}</td>`; }, "mrow")).join("")}
      ${row("Böen ICON", i => `<td>${o.icon.wind_gusts_10m[i] == null ? "" : Math.round(o.icon.wind_gusts_10m[i])}</td>`, "grow2")}
      ${row("Wolken %", i => `<td>${o.icon.cloud_cover[i] == null ? "" : Math.round(o.icon.cloud_cover[i])}</td>`, "wrow")}
      ${row("Regen mm", i => `<td>${o.icon.precipitation[i] > 0.05 ? de(o.icon.precipitation[i]) : ""}</td>`, "wrow")}
      ${row("°C", i => `<td>${o.icon.temperature_2m[i] == null ? "" : Math.round(o.icon.temperature_2m[i])}</td>`, "trow")}
    </tbody></table></div>
    <p class="hint">Rohwerte der Modelle am Spot. Die Modelle sehen den Breva kaum (Gitter 2–9 km, der See ist 2–4 km breit):
      an Breva-Nachmittagen zeigen sie meist 4–8 kn, auf dem Wasser wehen 12–20. Deshalb zählen die Breva-Zeichen oben mehr als die Knoten hier.</p>
    <div class="legend"><span>Modell (kn):</span>${KN_SCALE.map(([v, k], j) => `<span><i class="sw ${k}"></i>${v}${KN_SCALE[j + 1] ? "–" + KN_SCALE[j + 1][0] : "+"}</span>`).join("")}</div>`;
  box.querySelectorAll("[data-spot]").forEach(e => e.addEventListener("click", () => selectSpot(e.dataset.spot, false)));
}

function drawLegend() {
  const o = state.info?.overlay;
  $("#brevaLegend").innerHTML = `<span class="grad"></span><small>0</small><small style="margin-left:auto">14</small><small style="margin-left:auto">28 kn</small>`
    + (o ? `<span class="cap">Median ${o.abende ?? ""} Breva-Abende ${o.jahre ?? ""}, Sentinel-1 um 19:15</span>` : "");
}

/* ---------- Ablauf ---------- */
function renderAll() {
  if (state.fc) { drawWeek(); drawDetail(); }
  drawNow(); drawMarkers(); drawLegend();
}
function selectSpot(id, scroll = true) {
  state.spot = id; save("spot", id); renderAll();
  if (scroll) $("#detail").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
}
async function refresh() {
  const st = $("#status");
  st.textContent = "Lade Vorhersage und Messwerte …"; st.className = "status";
  $("#refreshBtn").disabled = true;
  const [fc, obs, mfc] = await Promise.allSettled([fetchForecast(), fetchObs(), fetchModelPoints()]);
  if (fc.status === "fulfilled") state.fc = fc.value;
  if (mfc.status === "fulfilled") { state.mfc = mfc.value; F7cache = null; } else console.warn("Modellpunkte", mfc.reason);
  if (obs.status === "fulfilled") state.obs = obs.value;
  else console.warn("ARPA", obs.reason);
  const nObs = Object.keys(state.obs).length;
  if (fc.status === "fulfilled") {
    try { localStorage.setItem(CACHE_KEY, JSON.stringify({ fc: state.fc })); } catch (e) {}
    st.textContent = `Vorhersage von ${fmtTime(new Date(state.fc.fetched))} Uhr · ${nObs} von ${STATIONS.length} Stationen live${obs.status === "rejected" ? " (ARPA nicht erreichbar)" : ""} · ${state.M && state.mfc ? "Breva-Modell aktiv" : "Breva-Modell lädt …"}`;
  } else if (state.fc) {
    st.textContent = `Keine Verbindung zu Open-Meteo (${fc.reason.message}). Zeige gespeicherte Vorhersage.`; st.className = "status warn";
  } else {
    st.textContent = `Vorhersage konnte nicht geladen werden (${fc.reason.message}).`; st.className = "status err";
  }
  $("#refreshBtn").disabled = false;
  renderAll();
}
function init() {
  $("#modelSel").value = state.model;
  $("#modelSel").addEventListener("change", e => { state.model = e.target.value; save("model", state.model); renderAll(); });
  document.querySelectorAll(".thr-toggle .seg").forEach(b => {
    const on = Number(b.dataset.thr) === state.thr;
    b.classList.toggle("on", on); b.setAttribute("aria-pressed", on);
    b.addEventListener("click", () => {
      state.thr = Number(b.dataset.thr); save("thr", state.thr);
      document.querySelectorAll(".thr-toggle .seg").forEach(x => { const o = x === b; x.classList.toggle("on", o); x.setAttribute("aria-pressed", o); });
      renderAll();
    });
  });
  $("#refreshBtn").addEventListener("click", refresh);
  $("#btnMap").addEventListener("click", () => setLayer("map"));
  $("#btnSat").addEventListener("click", () => setLayer("sat"));
  $("#btnBreva").addEventListener("click", () => setLayer("breva"));
  try { const c = JSON.parse(localStorage.getItem(CACHE_KEY) || "null"); if (c && c.fc && c.fc.points) state.fc = c.fc; } catch (e) {}
  if (window.maplibregl) initMap(); else $("#map").innerHTML = '<p class="maperr">Karte nicht verfügbar (offline).</p>';
  setLayer(state.layer);
  renderAll();
  fetchJSON("breva.json").then(x => { state.info = x; addOverlay(); renderAll(); }).catch(e => console.warn("breva.json", e));
  loadModels().then(M => { state.M = M; F7cache = null; renderAll();
    $("#status").textContent = $("#status").textContent.replace("Breva-Modell lädt …", state.mfc ? "Breva-Modell aktiv" : "Breva-Modell lädt …"); })
    .catch(e => console.warn("Breva-Modell nicht geladen (erst training/train_breva.py laufen lassen)", e));
  refresh();
  setInterval(() => fetchObs().then(o => { state.obs = o; renderAll(); }).catch(() => {}), 10 * 60e3);
  if ("serviceWorker" in navigator && !DEMO) navigator.serviceWorker.register("sw.js").catch(() => {});
}
document.addEventListener("DOMContentLoaded", init);
