"""Vergangene Messungen einer Weather-Underground-Station laden (für Abgleich mit Satellit und ARPA).

Schlüssel: nur für Besitzer einer eigenen, hochladenden Station (wunderground.com/member/api-keys); damit lassen sich
auch andere öffentliche Stationen abfragen. Grenze laut WU: 1500 Abrufe am Tag, 30 je Minute – ein Abruf je Tag.

  export WU_API_KEY=...
  python training/wu_history.py IGERAL122 --start 2024-03-01        # schon geladene Tage werden übersprungen
  -> data/extern/IGERAL122.csv (Einzelwerte, UTC, kn), data/extern/IGERAL122_stunde.csv (Stundenmittel Ortszeit,
     Stunde endet zur vollen Stunde – wie die ARPA-Stationen)
"""
import argparse, json, os, sys, time, urllib.error, urllib.request
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "extern")
KMH2KN = 0.539957


def day(station, d, key):
    u = (f"https://api.weather.com/v2/pws/history/all?stationId={station}&format=json&units=m&numericPrecision=decimal"
         f"&date={d:%Y%m%d}&apiKey={key}")
    for i in range(4):
        try:
            with urllib.request.urlopen(u, timeout=60) as r:
                if r.status == 204:
                    return []
                return json.loads(r.read() or b"{}").get("observations", [])
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                sys.exit(f"Schlüssel abgelehnt (HTTP {e.code}) – WU_API_KEY prüfen")
            if e.code == 204:
                return []
            time.sleep(10 * (i + 1))
        except Exception as e:
            print("  ", d.date(), e); time.sleep(10 * (i + 1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("station")
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--end", default=(pd.Timestamp.today() - pd.Timedelta(days=1)).strftime("%Y-%m-%d"))
    a = ap.parse_args()
    key = os.environ.get("WU_API_KEY")
    if not key:
        sys.exit("WU_API_KEY fehlt")
    os.makedirs(OUT, exist_ok=True)
    f = os.path.join(OUT, f"{a.station}.csv")
    old = pd.read_csv(f, parse_dates=["time_utc"]) if os.path.exists(f) else pd.DataFrame()
    have = set(old.time_utc.dt.strftime("%Y-%m-%d")) if len(old) else set()
    fleer = os.path.join(OUT, f"{a.station}_leer.txt")                  # Tage ohne Daten nicht erneut abfragen
    leer = set(open(fleer).read().split()) if os.path.exists(fleer) else set()
    days = [d for d in pd.date_range(a.start, a.end) if d.strftime("%Y-%m-%d") not in have | leer]
    print(f"{a.station}: {len(days)} Tage zu laden", flush=True)
    rows = []
    for i, d in enumerate(days):
        obs = day(a.station, d, key)
        if obs is None:
            continue
        if not obs:
            leer.add(d.strftime("%Y-%m-%d"))
        for o in obs:
            m = o.get("metric") or {}
            rows.append(dict(time_utc=o.get("obsTimeUtc"), kn=None if m.get("windspeedAvg") is None else m["windspeedAvg"] * KMH2KN,
                             boe_kn=None if m.get("windgustHigh") is None else m["windgustHigh"] * KMH2KN, dir=o.get("winddirAvg"),
                             temp_c=m.get("tempAvg"), rh=o.get("humidityAvg"), solar=o.get("solarRadiationHigh"),
                             druck_hpa=m.get("pressureMax"), regen_mm_h=m.get("precipRate")))
        time.sleep(2.2)                                                     # unter 30 Abrufen je Minute
        if (i + 1) % 50 == 0 or i == len(days) - 1:
            new = pd.DataFrame(rows)
            if len(new):
                new["time_utc"] = pd.to_datetime(new.time_utc, utc=True)
                old = pd.concat([old, new]).drop_duplicates("time_utc").sort_values("time_utc")
                old.to_csv(f, index=False, float_format="%.2f"); rows = []
            open(fleer, "w").write("\n".join(sorted(leer)))
            print(f"  {i + 1}/{len(days)} Tage, {len(old)} Werte gespeichert", flush=True)
    if not len(old):
        return
    x = old.set_index(pd.to_datetime(old.time_utc, utc=True)).tz_convert("Europe/Rome").tz_localize(None)
    def mdir(d):
        d = d.dropna()
        return np.nan if not len(d) else float(np.degrees(np.arctan2(np.sin(np.radians(d)).mean(), np.cos(np.radians(d)).mean())) % 360)
    h = x.resample("h", label="right", closed="right").agg({"kn": "mean", "boe_kn": "max", "dir": mdir, "temp_c": "mean", "solar": "mean"})
    n = x.kn.resample("h", label="right", closed="right").count()
    h = h[n >= 3]
    h.round(2).to_csv(os.path.join(OUT, f"{a.station}_stunde.csv"), index_label="time")
    print(f"geschrieben: {os.path.relpath(f)} und Stundenmittel ({len(h)} Stunden)")


if __name__ == "__main__":
    main()
