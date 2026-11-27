/* Vorhersage-Archiv: rechnet genau das, was die App anzeigt (gleiche Dateien: app/breva_model.js, app/spots.js,
   app/model/*), und hängt es mit Kennungen an data-Dateien im Archiv-Ordner an.

   node tools/archiv.js <archiv-ordner>

   Je Lauf:
     vorhersagen.csv   eine Zeile je Zieltag × Schwelle (7-Tage-Modell) bzw. je Schwelle (Heute-Modell)
     merkmale/<JJJJ-MM>.jsonl  Eingangsgrößen je Lauf (zum späteren Nachrechnen / Modellvergleich)
   Kennungen:
     lauf_id       Zeitstempel dieses Archiv-Laufs (UTC)
     modell_id     z. B. breva7-B-14-3f2a9c1d07 = Modellart, Ziel, Schwelle, Prüfsumme der Modelldatei + Eichung
                   (ändert sich bei jedem Neutraining)
     wettermodell  Eingangsmodell (ecmwf_ifs025) und ecmwf_init = Startzeit des verwendeten Laufs (Open-Meteo-Metadaten)
     app_commit    Git-Commit des App-Codes
*/
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm"), crypto = require("crypto");

const ROOT = path.resolve(__dirname, "..");
const APP = path.join(ROOT, "app");
const OUT = path.resolve(process.argv[2] || path.join(ROOT, "archiv"));
const BrevaModel = require(path.join(APP, "breva_model.js"));
const S = (() => {
  const ctx = {};
  vm.runInNewContext(fs.readFileSync(path.join(APP, "spots.js"), "utf8") +
    ";this.X={SPOTS,STATIONS,POINTS,THRESHOLDS,MODEL_POINTS,MODEL_VARS};", ctx);
  return ctx.X;
})();
const WX = "ecmwf_ifs025";
const MS2KN = 1 / 0.514444;
const ARPA = "https://www.dati.lombardia.it/resource/647i-nhxk.json";
const readJSON = f => JSON.parse(fs.readFileSync(path.join(APP, "model", f), "utf8"));
const sha = s => crypto.createHash("sha1").update(s).digest("hex").slice(0, 10);

async function fetchJSON(url, tries = 3) {
  for (let i = 0; ; i++) {
    try {
      const r = await fetch(url, { signal: AbortSignal.timeout(60000) });
      const b = await r.json().catch(() => null);
      if (!r.ok) throw new Error((b && (b.reason || b.message)) || `${r.status}`);
      return b;
    } catch (e) {
      if (i >= tries - 1) throw e;
      await new Promise(r => setTimeout(r, 10000 * (i + 1)));
    }
  }
}

/* wie app.js fetchModelPoints */
async function modelPoints() {
  const ids = Object.keys(S.MODEL_POINTS);
  const p = new URLSearchParams({
    latitude: ids.map(k => S.MODEL_POINTS[k][0]).join(","), longitude: ids.map(k => S.MODEL_POINTS[k][1]).join(","),
    hourly: S.MODEL_VARS.join(","), models: WX, wind_speed_unit: "kn", timezone: "Europe/Rome",
    past_days: "31", forecast_days: "7"
  });
  let res = await fetchJSON("https://api.open-meteo.com/v1/forecast?" + p);
  if (!Array.isArray(res)) res = [res];
  const H = {};
  ids.forEach((k, i) => {
    const h = res[i]?.hourly; if (!h) return;
    H[k] = { time: h.time };
    for (const v of S.MODEL_VARS) H[k][v] = h[v] || h[`${v}_${WX}`] || [];
  });
  return H;
}

async function ecmwfInit() {
  try {
    const m = await fetchJSON(`https://api.open-meteo.com/data/${WX}/static/meta.json`, 2);
    const t = m.last_run_initialisation_time;
    return t ? new Date(t * 1000).toISOString().slice(0, 16) + "Z" : "";
  } catch (e) { return ""; }
}

/* wie app.js fetchObs / hourlyMeans / localKey */
function localKey(d) {
  const s = d.toLocaleString("sv-SE", { timeZone: "Europe/Rome" });
  return s.slice(0, 10) + "T" + s.slice(11, 13);
}
function hourlyMeans(sp, dmap) {
  const g = new Map();
  for (const x of sp) {
    const k = localKey(new Date(Math.ceil(x.t.getTime() / 3600e3) * 3600e3));
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
async function observations() {
  const ids = S.STATIONS.flatMap(s => [s.speed, s.dir]);
  const since = new Date(Date.now() + 3600e3 - 44 * 3600e3).toISOString().slice(0, 19);
  const q = new URLSearchParams({ $where: `idsensore in(${ids.map(i => `'${i}'`).join(",")}) AND data > '${since}'`,
    $order: "data DESC", $limit: "20000" });
  const rows = await fetchJSON(`${ARPA}?${q}`);
  const out = {};
  for (const st of S.STATIONS) {
    const ser = id => rows.filter(r => Number(r.idsensore) === id && Number(r.valore) > -900 && (r.stato ?? "VA") !== "NV")
      .map(r => ({ t: new Date(r.data.slice(0, 19) + "+01:00"), v: Number(r.valore) })).sort((a, b) => a.t - b.t);
    const sp = ser(st.speed), di = ser(st.dir);
    if (sp.length) out[st.id] = hourlyMeans(sp, new Map(di.map(x => [x.t.getTime(), x.v])));
  }
  return out;
}

const shiftDate = (d, n) => { const t = new Date(d + "T12:00:00Z"); t.setUTCDate(t.getUTCDate() + n); return t.toISOString().slice(0, 10); };
const csvLine = a => a.map(x => x == null || (typeof x === "number" && !Number.isFinite(x)) ? "" :
  typeof x === "number" ? String(Math.round(x * 10000) / 10000) : /[",\n]/.test(String(x)) ? `"${String(x).replace(/"/g, '""')}"` : String(x)).join(",");

async function main() {
  const now = new Date();
  const lauf_id = now.toISOString().slice(0, 16) + "Z";
  const today = now.toLocaleString("sv-SE", { timeZone: "Europe/Rome" }).slice(0, 10);
  const commit = (process.env.GITHUB_SHA || "").slice(0, 10);
  const man = readJSON("manifest.json"), heuteMan = readJSON("heute.json");
  const M = {}; for (const [thr, f] of Object.entries(man.files)) M[thr] = readJSON(f);
  const ids = {};
  for (const thr of Object.keys(man.files))
    ids[thr] = `breva7-${man.ziel || "A"}-${thr}-` + sha(fs.readFileSync(path.join(APP, "model", man.files[thr]), "utf8") + JSON.stringify(man.calib[thr]));
  const [H, init] = await Promise.all([modelPoints(), ecmwfInit()]);
  const F = BrevaModel.features(H, S.MODEL_POINTS);
  const ds = Object.keys(F).filter(d => d >= today).sort().slice(0, 7);
  const rows = [];
  const base = { lauf_id, app_commit: commit, wettermodell: WX, ecmwf_init: init };
  const p7 = {};
  ds.forEach((d, i) => {
    for (const thr of S.THRESHOLDS) {
      const raw = BrevaModel.predictProba(M[thr], BrevaModel.vec(F[d], man.features));
      const cal = man.calib[String(thr)] || {};
      const p = BrevaModel.calibrate(cal[String(i)] ?? cal["7"], raw);
      p7[`${d}_${thr}`] = p;
      const cc = (man.call || {})[String(thr)] || {}, k = cc[String(i)] ?? cc["7"];
      rows.push({ ...base, art: "7tage", modell_id: ids[thr], zieldatum: d, vorlauf: i, schwelle: thr, stunde: "", p, p_roh: raw,
        call_ab: k ? k.schwelle : "", call: k ? Number(p >= k.schwelle) : "" });
    }
  });
  // Heute-Modell (wie app.js heute()); ohne Messungen nur Vorhersage
  let obs = {}, obsErr = "";
  try { obs = await observations(); } catch (e) { obsErr = String(e.message || e); }
  const hourKey = h => `${today}T${String(h).padStart(2, "0")}`;
  const hour = [...heuteMan.hours].reverse().find(h => ["vercana", "samolaco", "colico"].some(st => obs[st]?.[hourKey(h)])) ?? null;
  const g = BrevaModel.brevaDay(obs, shiftDate(today, -1), heuteMan.faktor, heuteMan.faktor_col, heuteMan.lang_h);
  const hx = hour == null ? null : { ...F[today], ...BrevaModel.obsFeatures(obs, today, hour, heuteMan.faktor, heuteMan.faktor_col),
    gestern_breva: g ? g.breva : NaN, gestern_max: g ? g.max : NaN };
  for (const ziel of Object.keys(heuteMan.ziele || { 14: 1 })) {
    const key = `${hour}_${ziel}`, m = hour == null ? null : readJSON(heuteMan.files[key]);
    const hid = `heute-${heuteMan.ziel || "A"}-${key}-` + (m ? sha(JSON.stringify(m) + JSON.stringify(heuteMan.calib[key])) : "nurvorhersage");
    const raw = m ? BrevaModel.predictProba(m, BrevaModel.vec(hx, heuteMan.features)) : null;
    const p = m ? BrevaModel.calibrate(heuteMan.calib[key], raw) : (ziel === "14" ? p7[`${today}_14`] : null);
    const k = m ? (heuteMan.call || {})[key] : (ziel === "14" ? (((man.call || {})["14"] || {})["0"]) : null);
    rows.push({ ...base, art: "heute", modell_id: hid, zieldatum: today, vorlauf: 0, schwelle: ziel, stunde: hour ?? "", p, p_roh: raw,
      call_ab: k ? k.schwelle : "", call: k && p != null ? Number(p >= k.schwelle) : "" });
  }
  // schreiben
  fs.mkdirSync(path.join(OUT, "merkmale"), { recursive: true });
  const readme = path.join(OUT, "README.md");
  if (!fs.existsSync(readme)) fs.writeFileSync(readme, `# Breva-Vorhersage-Archiv

Automatisch geschrieben von \`tools/archiv.js\` (GitHub Action „Vorhersagen archivieren“, Branch \`main\`).
Jeder Lauf rechnet genau, was die App in dem Moment anzeigt.

**vorhersagen.csv** – eine Zeile je Lauf × Zieltag × Schwelle
- \`lauf_id\`: Zeitpunkt des Archiv-Laufs (UTC)
- \`art\`: \`7tage\` (7-Tage-Modell) oder \`heute\` (Heute-Modell mit Messungen)
- \`modell_id\`: Modellart-Ziel-Schwelle-Prüfsumme (Modelldatei + Eichung); ändert sich bei jedem Neutraining
- \`wettermodell\`, \`ecmwf_init\`: Eingangsmodell und Startzeit des verwendeten Laufs (Open-Meteo)
- \`app_commit\`: Git-Commit des App-Codes
- \`zieldatum\`, \`vorlauf\` (Tage), \`schwelle\` (kn), \`stunde\` (Entscheidungsstunde des Heute-Modells, leer = nur Vorhersage)
- \`p\`: geeichte Chance (wie in der App), \`p_roh\`: Modellausgabe vor der Eichung
- \`call_ab\`: Schwelle für einen Breva-Call (≥ 80 % Präzision in der Prüfung; leer = nie erreicht), \`call\`: 1 = Call

**merkmale/JJJJ-MM.jsonl** – je Lauf die Eingangsgrößen (zum Nachrechnen und für Modellvergleiche)
`);
  const cols = ["lauf_id", "art", "modell_id", "wettermodell", "ecmwf_init", "app_commit", "zieldatum", "vorlauf", "schwelle", "stunde", "p", "p_roh", "call_ab", "call"];
  const f = path.join(OUT, "vorhersagen.csv");
  if (!fs.existsSync(f)) fs.writeFileSync(f, cols.join(",") + "\n");
  fs.appendFileSync(f, rows.map(r => csvLine(cols.map(c => r[c]))).join("\n") + "\n");
  const rec = { lauf_id, ecmwf_init: init, wettermodell: WX, modell_ids: ids, heute_stunde: hour, obs_fehler: obsErr,
    merkmale: Object.fromEntries(ds.map(d => [d, F[d]])), heute_eingang: hx };
  fs.appendFileSync(path.join(OUT, "merkmale", `${today.slice(0, 7)}.jsonl`), JSON.stringify(rec) + "\n");
  console.log(`${lauf_id}: ${rows.length} Zeilen, ECMWF-Lauf ${init || "?"}, Heute-Stunde ${hour ?? "–"}${obsErr ? " (Messungen: " + obsErr + ")" : ""}`);
  for (const r of rows) console.log(`  ${r.art.padEnd(5)} ${r.zieldatum} ≥${r.schwelle} ${r.stunde === "" ? "  " : String(r.stunde).padStart(2)} ${r.p == null ? "–" : (100 * r.p).toFixed(0) + " %"}  ${r.modell_id}`);
}
main().catch(e => { console.error(e); process.exit(1); });
