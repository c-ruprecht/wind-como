/* Messungen fremder Stationen archivieren und live bereitstellen (läuft als GitHub Action, siehe messungen.yml).

   Weather Underground (PWS-API von The Weather Company): Schlüssel nur für Besitzer einer eigenen, hochladenden Station
   (wunderground.com/member/api-keys). Der Schlüssel steht als Secret WU_API_KEY in GitHub – nie in der App.

   node tools/messungen.js <archiv-ordner>
     -> stationen/<ID>/JJJJ-MM.csv   alle Einzelwerte (5 min), UTC, kn
        stationen/live.json          letzte 12 h je Station (für die App, über raw.githubusercontent.com)
*/
const fs = require("fs"), path = require("path"), vm = require("vm");
const OUT = process.argv[2] || "archiv-wt";
const KEY = process.env.WU_API_KEY || "";
const S = {};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "..", "app", "spots.js"), "utf8") + ";this.EXTERN = EXTERN;", S);
const KMH2KN = 0.539957;
const COLS = ["time_utc", "kn", "boe_kn", "dir", "temp_c", "rh", "solar", "druck_hpa", "regen_mm_h"];

async function wuDay(id) {
  const u = `https://api.weather.com/v2/pws/observations/all/1day?stationId=${id}&format=json&units=m&numericPrecision=decimal&apiKey=${KEY}`;
  const r = await fetch(u, { signal: AbortSignal.timeout(30000) });
  if (r.status === 204) return [];                       // Station sendet gerade nicht
  if (!r.ok) throw new Error(`${id}: HTTP ${r.status}`);
  const b = await r.json();
  return (b.observations || []).map(o => ({
    time_utc: o.obsTimeUtc, kn: o.metric?.windspeedAvg != null ? +(o.metric.windspeedAvg * KMH2KN).toFixed(1) : "",
    boe_kn: o.metric?.windgustHigh != null ? +(o.metric.windgustHigh * KMH2KN).toFixed(1) : "", dir: o.winddirAvg ?? "",
    temp_c: o.metric?.tempAvg ?? "", rh: o.humidityAvg ?? "", solar: o.solarRadiationHigh ?? "",
    druck_hpa: o.metric?.pressureMax ?? "", regen_mm_h: o.metric?.precipRate ?? ""
  }));
}

function append(id, rows) {
  const byMonth = {};
  for (const r of rows) (byMonth[r.time_utc.slice(0, 7)] ??= []).push(r);
  let neu = 0;
  for (const [m, rs] of Object.entries(byMonth)) {
    const dir = path.join(OUT, "stationen", id); fs.mkdirSync(dir, { recursive: true });
    const f = path.join(dir, `${m}.csv`);
    const have = new Set(fs.existsSync(f) ? fs.readFileSync(f, "utf8").split("\n").slice(1).map(l => l.split(",")[0]) : []);
    if (!fs.existsSync(f)) fs.writeFileSync(f, COLS.join(",") + "\n");
    const add = rs.filter(r => !have.has(r.time_utc)).sort((a, b) => a.time_utc.localeCompare(b.time_utc));
    if (add.length) fs.appendFileSync(f, add.map(r => COLS.map(c => r[c]).join(",")).join("\n") + "\n");
    neu += add.length;
  }
  return neu;
}

async function main() {
  if (!KEY) { console.log("Kein WU_API_KEY gesetzt – nichts zu tun."); return; }
  const live = { aktualisiert: new Date().toISOString(), stationen: {} };
  const fl = path.join(OUT, "stationen", "live.json");
  try { Object.assign(live.stationen, JSON.parse(fs.readFileSync(fl, "utf8")).stationen || {}); } catch (e) {}
  for (const st of S.EXTERN.filter(s => s.quelle === "wu")) {
    try {
      const rows = await wuDay(st.id);
      const neu = append(st.id, rows);
      const since = Date.now() - 12 * 3600e3;
      const series = rows.filter(r => Date.parse(r.time_utc) >= since && r.kn !== "")
        .map(r => ({ t: r.time_utc, kn: r.kn, boe: r.boe_kn === "" ? null : r.boe_kn, dir: r.dir === "" ? null : r.dir }));
      if (series.length) live.stationen[st.id] = { name: st.name, letzte: series[series.length - 1], serie: series };
      console.log(`${st.id}: ${rows.length} Werte heute, ${neu} neu archiviert, letzte ${series.at(-1)?.t ?? "–"}`);
    } catch (e) { console.warn(String(e.message || e)); }
  }
  fs.mkdirSync(path.dirname(fl), { recursive: true });
  fs.writeFileSync(fl, JSON.stringify(live));
}
main().catch(e => { console.error(e); process.exit(1); });
