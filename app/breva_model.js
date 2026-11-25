/* Breva-Modelle im Browser: Merkmale wie training/breva_daten.py features(), XGBoost-Bäume auswerten, eichen.
   7 Tage: train_breva.py (nur Vorhersage). Heute: train_heute.py (Vorhersage Tag 0 + Messungen bis zur Uhrzeit + Vortag). */
"use strict";

const BrevaModel = (() => {
  const f32 = Math.fround;
  const fin = v => v !== null && v !== undefined && Number.isFinite(v);

  function predictMargin(model, x) {
    let s = model.base;
    for (const [feat, thr, left, right, defl] of model.trees) {
      let n = 0;
      while (left[n] !== -1) {
        const v = x[feat[n]];
        if (!fin(v)) n = defl[n] ? left[n] : right[n];
        else n = f32(v) < thr[n] ? left[n] : right[n];
      }
      s += thr[n];
    }
    return s;
  }
  const predictProba = (model, x) => 1 / (1 + Math.exp(-predictMargin(model, x)));
  function calibrate(curve, p) {
    if (!curve || p == null) return p;
    const [xs, ys] = curve;
    if (p <= xs[0]) return ys[0];
    if (p >= xs[xs.length - 1]) return ys[ys.length - 1];
    let i = 1; while (xs[i] < p) i++;
    const f = (p - xs[i - 1]) / Math.max(xs[i] - xs[i - 1], 1e-12);
    return ys[i - 1] + f * (ys[i] - ys[i - 1]);
  }

  /* H: { punkt: { time: ["YYYY-MM-DDTHH:MM", …] (Ortszeit), var: [Werte …] } } -> { datum: { merkmal: Wert } } */
  function features(H, POINTS) {
    const ser = (p, v) => (H[p] && H[p][v]) ? H[p] : null;
    const days = new Set();
    for (const p of Object.keys(H)) for (const t of H[p].time) days.add(t.slice(0, 10));
    const D = [...days].sort();
    // Stundenwerte je Tag vorindizieren
    const idx = {};
    for (const p of Object.keys(H)) {
      idx[p] = {};
      H[p].time.forEach((t, i) => { (idx[p][t.slice(0, 10)] ||= {})[+t.slice(11, 13)] = i; });
    }
    function win(p, v, h0, h1, how, d) {
      const o = ser(p, v); if (!o) return NaN;
      const row = idx[p][d]; if (!row) return NaN;
      const vals = []; let present = false;
      for (let h = h0; h <= h1; h++) if (row[h] !== undefined) { present = true; const x = o[v][row[h]]; if (fin(x)) vals.push(x); }
      if (!present) return NaN;
      if (how === "sum") return vals.reduce((a, b) => a + b, 0);       // wie pandas: leere Summe = 0
      if (!vals.length) return NaN;
      if (how === "mean") return vals.reduce((a, b) => a + b, 0) / vals.length;
      if (how === "max") return Math.max(...vals);
      if (how === "min") return Math.min(...vals);
      return NaN;
    }
    function at(p, v, h, d) {
      const o = ser(p, v); if (!o) return NaN;
      const i = idx[p][d]?.[h]; if (i === undefined) return NaN;
      const x = o[v][i]; return fin(x) ? x : NaN;
    }
    const SYN = ["lyon", "zurich", "muenchen", "genova", "venezia", "milano", "bergamo"].filter(p => ser(p, "pressure_msl"));
    let geoA = null;
    if (SYN.length >= 4) {
      const lat0 = SYN.reduce((a, p) => a + POINTS[p][0], 0) / SYN.length;
      geoA = SYN.map(p => [1, (POINTS[p][1] - 9.2) * 111.2 * Math.cos(lat0 * Math.PI / 180) / 100, (POINTS[p][0] - lat0) * 111.2 / 100]);
    }
    const out = {};
    const rows = D.map(d => {
      const F = {
        rad_see: win("see", "shortwave_radiation", 9, 17, "sum", d) / 1000,
        rad_chiavenna: win("chiavenna", "shortwave_radiation", 9, 17, "sum", d) / 1000,
        rad_milano: win("milano", "shortwave_radiation", 9, 17, "sum", d) / 1000,
        rad_spaet_chiavenna: win("chiavenna", "shortwave_radiation", 15, 18, "sum", d) / 1000,
        wolken_see: win("see", "cloud_cover", 9, 17, "mean", d),
        wolken_morgen_see: win("see", "cloud_cover", 6, 11, "mean", d),
        wolken_chiavenna: win("chiavenna", "cloud_cover", 9, 17, "mean", d),
        tmax_milano: win("milano", "temperature_2m", 12, 17, "max", d),
        tmax_bergamo: win("bergamo", "temperature_2m", 12, 17, "max", d),
        tmax_chiavenna: win("chiavenna", "temperature_2m", 12, 17, "max", d),
        tmax_sondrio: win("sondrio", "temperature_2m", 12, 17, "max", d),
        tmax_engadin: win("engadin", "temperature_2m", 12, 17, "max", d),
        tmin_milano: win("milano", "temperature_2m", 3, 8, "min", d),
        tmin_chiavenna: win("chiavenna", "temperature_2m", 3, 8, "min", d),
        tmean_see: win("see", "temperature_2m", 0, 23, "mean", d),
        tmax_see: win("see", "temperature_2m", 12, 17, "max", d),
        taupunktdiff_milano: at("milano", "temperature_2m", 13, d) - at("milano", "dew_point_2m", 13, d),
        dp_po_tal_06: at("milano", "pressure_msl", 6, d) - at("chiavenna", "pressure_msl", 6, d),
        dp_po_tal_15: at("milano", "pressure_msl", 15, d) - at("chiavenna", "pressure_msl", 15, d),
        dp_po_tal_18: at("milano", "pressure_msl", 18, d) - at("chiavenna", "pressure_msl", 18, d),
        dp_bergamo_sondrio_15: at("bergamo", "pressure_msl", 15, d) - at("sondrio", "pressure_msl", 15, d),
        dp_zurich_milano_12: at("zurich", "pressure_msl", 12, d) - at("milano", "pressure_msl", 12, d),
        dp_muenchen_genova_12: at("muenchen", "pressure_msl", 12, d) - at("genova", "pressure_msl", 12, d),
        dp_lyon_venezia_12: at("lyon", "pressure_msl", 12, d) - at("venezia", "pressure_msl", 12, d),
        p_milano_12: at("milano", "pressure_msl", 12, d),
        regen_see: win("see", "precipitation", 11, 19, "sum", d),
        regen_chiavenna: win("chiavenna", "precipitation", 11, 19, "sum", d),
        wind_see_15: at("see", "wind_speed_10m", 15, d),
        wind_milano_12: at("milano", "wind_speed_10m", 12, d)
      };
      F.wind_see_15_sued = F.wind_see_15 * Math.cos((at("see", "wind_direction_10m", 15, d) - 200) * Math.PI / 180);
      F.dt_tal_po = F.tmax_chiavenna - F.tmax_milano;
      F.dt_engadin_po = F.tmax_engadin - F.tmax_milano;
      F.amp_tal_minus_po = (F.tmax_chiavenna - F.tmin_chiavenna) - (F.tmax_milano - F.tmin_milano);
      F.dp_tag_minus_nacht = F.dp_po_tal_15 - F.dp_po_tal_06;
      if (geoA) {
        const P = SYN.map(p => at(p, "pressure_msl", 12, d));
        if (P.every(fin)) {
          const c = lstsq3(geoA, P);
          F.geo_staerke = Math.hypot(c[1], c[2]); F.geo_aus_sued = c[1]; F.geo_aus_west = -c[2];
        } else { F.geo_staerke = F.geo_aus_sued = F.geo_aus_west = NaN; }
      }
      const doy = dayOfYear(d);
      F.doy_sin = Math.sin(2 * Math.PI * doy / 365.25); F.doy_cos = Math.cos(2 * Math.PI * doy / 365.25);
      return F;
    });
    rows.forEach((F, k) => {
      const prev = rows[k - 1];
      F.drucktendenz_24h = prev ? F.p_milano_12 - prev.p_milano_12 : NaN;
      F.regen_vortag = prev ? prev.regen_see + prev.regen_chiavenna : NaN;
      const w = rows.slice(Math.max(0, k - 29), k + 1).map(r => r.tmean_see).filter(fin);
      F.see_t30 = w.length >= 20 ? w.reduce((a, b) => a + b, 0) / w.length : NaN;
      F.luft_minus_see_t30 = F.tmax_see - F.see_t30;
      out[D[k]] = F;
    });
    return out;
  }
  function dayOfYear(d) {
    const t = Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10));
    return Math.round((t - Date.UTC(+d.slice(0, 4), 0, 1)) / 864e5) + 1;
  }
  /* kleinste Quadrate für p = a + b·x + c·y (3 Unbekannte, Normalgleichungen) */
  function lstsq3(A, y) {
    const M = [[0, 0, 0], [0, 0, 0], [0, 0, 0]], r = [0, 0, 0];
    A.forEach((row, i) => { for (let a = 0; a < 3; a++) { r[a] += row[a] * y[i]; for (let b = 0; b < 3; b++) M[a][b] += row[a] * row[b]; } });
    // Gauß-Elimination
    for (let c = 0; c < 3; c++) {
      let piv = c; for (let k = c + 1; k < 3; k++) if (Math.abs(M[k][c]) > Math.abs(M[piv][c])) piv = k;
      [M[c], M[piv]] = [M[piv], M[c]]; [r[c], r[piv]] = [r[piv], r[c]];
      for (let k = c + 1; k < 3; k++) { const f = M[k][c] / M[c][c]; for (let j = c; j < 3; j++) M[k][j] -= f * M[c][j]; r[k] -= f * r[c]; }
    }
    const x = [0, 0, 0];
    for (let c = 2; c >= 0; c--) { let s = r[c]; for (let j = c + 1; j < 3; j++) s -= M[c][j] * x[j]; x[c] = s / M[c][c]; }
    return x;
  }
  const vec = (F, names) => names.map(n => (F && fin(F[n])) ? F[n] : null);

  /* ---------- Heute: Messungen bis zur Entscheidungsstunde (wie train_heute.py obs_features) ----------
     hourly: { station: { "YYYY-MM-DDTHH": {kn, dir} } } – Stundenmittel, Stunde endet zur vollen Stunde (Ortszeit) */
  const AXIS = { samolaco: 157, colico: 270, vercana: 225, morbegno: 245 };
  function obsFeatures(hourly, date, hour) {
    const F = {};
    const val = (st, h, d = date) => hourly[st]?.[`${d}T${String(h).padStart(2, "0")}`] ?? null;
    const comp = (o, ax) => o && fin(o.kn) && fin(o.dir) ? o.kn * Math.cos((o.dir - ax) * Math.PI / 180) : null;
    for (const [st, ax] of Object.entries(AXIS)) {
      const last = comp(val(st, hour), ax), prev = comp(val(st, hour - 1), ax);
      const seq = []; for (let h = 10; h <= hour; h++) { const c = comp(val(st, h), ax); if (c != null) seq.push(c); }
      F[`${st}_jetzt`] = last ?? NaN;
      F[`${st}_mittel2h`] = last != null && prev != null ? (last + prev) / 2 : (last ?? NaN);
      F[`${st}_max_ab10`] = seq.length ? Math.max(...seq) : NaN;
    }
    // Tivano am Morgen: Samolaco Nordkomponente 5–9 Uhr (max), Vercana Wind 7–9 Uhr (Mittel)
    const tiv = []; for (let h = 5; h <= 9; h++) { const c = comp(val("samolaco", h), 337); if (c != null) tiv.push(c); }
    F.tivano_samolaco = tiv.length ? Math.max(...tiv) : NaN;
    return F;
  }
  /* Breva gestern aus den Messungen (wie tage(): Samolaco × Faktor ≥ 14 kn, ≥ 2 h aus SSO–S, 11–20 Uhr, morgens ruhig) */
  function brevaDay(hourly, date, factor) {
    const s = hourly.samolaco; if (!s) return null;
    let run = 0, best = 0, n = 0, morning = [], max = 0;
    for (let h = 0; h <= 23; h++) {
      const o = s[`${date}T${String(h).padStart(2, "0")}`];
      if (!o) { if (h >= 11 && h <= 20) run = 0; continue; }
      if (h >= 6 && h <= 10) morning.push(o.kn);
      if (h >= 11 && h <= 20) {
        n++; max = Math.max(max, o.kn);
        const ok = o.kn * factor >= 14 && o.dir >= 112 && o.dir <= 202;
        run = ok ? run + 1 : 0; best = Math.max(best, run);
      }
    }
    if (n < 8) return null;
    const m = morning.length ? morning.reduce((a, b) => a + b, 0) / morning.length : 0;
    return { breva: best >= 2 && m < 6 ? 1 : 0, max: max * factor, stunden: best };
  }

  return { predictMargin, predictProba, calibrate, features, vec, obsFeatures, brevaDay, AXIS };
})();
if (typeof module !== "undefined") module.exports = BrevaModel;
