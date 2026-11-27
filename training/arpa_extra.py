"""ARPA-Messungen außer Wind: Temperatur, Feuchte, Globalstrahlung, Niederschlag entlang Ebene → See → Täler.

Wozu: Der Breva wird vom Temperatur-/Druckgefälle zwischen Po-Ebene und den Alpentälern angetrieben. Für die
Vorhersage am selben Tag ist das *gemessene* Gefälle am Vormittag (und wie schnell es wächst) vermutlich verlässlicher
als das vorhergesagte – besonders an Tagen, an denen das Wettermodell die Wolken falsch hat.
(Luftdruck veröffentlicht ARPA Lombardia im offenen Datensatz nicht.)

Ablauf
  1. sensoren: für jeden Zielpunkt die nächstgelegene aktive Station je Größe aus dem Stationsverzeichnis
     (mit Höhengrenze, damit z. B. „Milano“ wirklich Ebene ist) -> data/arpa/sensors_extra.json
  2. laden: Messwerte je Sensor und Jahr (Archiv + letzte 7 Monate) -> data/arpa/raw/<größe>_<sensor>_<jahr>.csv
     (gleiches Schema wie download_arpa.py; fertige Jahre werden übersprungen, das laufende erneuert)
  3. stunden: Stundenwerte (Ende der Stunde, UTC; Temperatur/Feuchte/Strahlung Mittel, Regen Summe)
     -> data/arpa/messungen_stunde.csv  Spalten <punkt>_<größe>

Aufruf:  python training/arpa_extra.py [--from 2014] [--schritt sensoren|laden|stunden|alle]
"""
import argparse, json, math, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import download_arpa as A  # noqa: E402

OUT = A.OUT
KINDS = {"temp": "temperatura", "rh": "umidit", "rad": "radiazione", "rain": "precipitazione"}
# Zielpunkt -> (lat, lon, min. Höhe, max. Höhe, Rolle)
TARGETS = {
    "milano":    (45.47, 9.19,    0,  250, "Po-Ebene"),
    "bergamo":   (45.69, 9.67,    0,  450, "Ebene/Voralpen Ost"),
    "como":      (45.81, 9.08,    0,  400, "Südende Como-Arm"),
    "lecco":     (45.85, 9.39,    0,  400, "Südende Lecco-Arm"),
    "colico":    (46.13, 9.37,    0,  450, "Nordende See"),
    "chiavenna": (46.30, 9.40,    0,  600, "Mera-Tal / Valchiavenna"),
    "morbegno":  (46.14, 9.57,    0,  450, "unteres Veltlin"),
    "sondrio":   (46.17, 9.87,    0,  550, "mittleres Veltlin"),
    "berg_see":  (46.08, 9.30, 1300, 2400, "Berg über dem See (Schichtung)"),
    "berg_nord": (46.42, 9.35, 1400, 2600, "Hochlage Valchiavenna"),
}
LIMITS = {"temp": (-35, 45), "rh": (1, 100), "rad": (0, 1400), "rain": (0, 60)}


def km(la1, lo1, la2, lo2):
    return 6371 * math.hypot(math.radians(la2 - la1) * 1, math.radians(lo2 - lo1) * math.cos(math.radians((la1 + la2) / 2)))


def sensoren(first_year):
    reg = A.soql(A.REGISTRY)
    print(f"  Verzeichnis: {len(reg)} Sensoren")
    out = {}
    for key, (la, lo, hmin, hmax, rolle) in TARGETS.items():
        out[key] = {"rolle": rolle}
        for kind, word in KINDS.items():
            cand = []
            for r in reg:
                if word not in str(r.get("tipologia", "")).lower():
                    continue
                if str(r.get("storico", "N")).upper() == "S" or r.get("datastop"):
                    continue
                try:
                    q = float(r.get("quota", "nan")); rla, rlo = float(r["lat"]), float(r["lng"])
                except (KeyError, ValueError):
                    continue
                if math.isnan(q):
                    if hmin > 0:              # ohne Höhenangabe keine Bergstation wählen
                        continue
                    q = 0.0
                if not (hmin <= q <= hmax):
                    continue
                start = str(r.get("datastart", ""))[:4]
                late = 1 if start.isdigit() and int(start) > first_year else 0       # lieber lange Reihen
                cand.append((late, km(la, lo, rla, rlo), r, q))
            cand = [c for c in cand if c[1] <= 25]
            if not cand:
                print(f"  {key:10s} {kind:5s} – keine Station ≤ 25 km"); continue
            late, d, r, q = min(cand, key=lambda c: (c[1] + 15 * c[0]))           # spät beginnende Reihe = +15 km
            out[key][kind] = {"idsensore": int(r["idsensore"]), "station": r.get("nomestazione", ""),
                              "quota": q, "km": round(d, 1), "seit": str(r.get("datastart", ""))[:10]}
            print(f"  {key:10s} {kind:5s} {r.get('nomestazione', ''):30s} {q:5.0f} m  {d:4.1f} km  seit {str(r.get('datastart', ''))[:10]}")
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(f"{OUT}/sensors_extra.json", "w"), indent=1, ensure_ascii=False)
    return out


def laden(sens, first_year):
    this = pd.Timestamp.today().year
    os.makedirs(f"{OUT}/raw", exist_ok=True)
    jobs = sorted({(kind, v["idsensore"]) for s in sens.values() for kind, v in s.items() if kind in KINDS})
    print(f"  {len(jobs)} Sensoren × {this - first_year + 1} Jahre")
    for y in range(first_year, this + 1):
        for kind, sid in jobs:
            f = f"{OUT}/raw/{kind}_{sid}_{y}.csv"
            n = A.fetch_year(f, kind, sid, y, this)    # laufendes Jahr nur ab dem letzten Wert nachladen
            if n is not None:
                print(f"  {kind} {sid} {y}: {n} neue Werte", flush=True)


def stunden(sens, first_year):
    cols = {}
    for key, s in sens.items():
        for kind in KINDS:
            if kind not in s:
                continue
            x = A.read_raw(kind, s[kind]["idsensore"], first_year)
            if x.empty:
                continue
            lo, hi = LIMITS[kind]
            bad = (x < lo) | (x > hi)
            x = x[~bad]
            g = x.resample("1h", label="right", closed="right")
            h = g.sum(min_count=3) if kind == "rain" else g.mean()
            h = h[g.count() >= 3]
            if kind == "temp":                                   # Sprünge > 8 °C in einer Stunde = Messfehler
                jump = h.diff().abs() > 8
                h[jump & (h.shift(-1).diff().abs() > 8)] = np.nan
            cols[f"{key}_{kind}"] = h
            print(f"  {key:10s} {kind:5s} {h.notna().sum():6d} Stunden  {h.index.min():%Y-%m-%d} – {h.index.max():%Y-%m-%d}"
                  f"  Mittel {h.mean():7.1f}  entfernt {int(bad.sum())}")
    if not cols:
        sys.exit("keine Messwerte – erst laden")
    M = pd.DataFrame(cols).sort_index()
    M.to_csv(f"{OUT}/messungen_stunde.csv", index_label="time", float_format="%.2f")
    print(f"geschrieben: data/arpa/messungen_stunde.csv ({M.shape[1]} Reihen, {len(M)} Stunden)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="first", type=int, default=2014)
    ap.add_argument("--schritt", default="alle", choices=["sensoren", "laden", "stunden", "alle"])
    a = ap.parse_args()
    f = f"{OUT}/sensors_extra.json"
    if a.schritt in ("sensoren", "alle") or not os.path.exists(f):
        print("1. Sensoren"); sens = sensoren(a.first)
    else:
        sens = json.load(open(f))
    if a.schritt in ("laden", "alle"):
        print("2. Messwerte"); laden(sens, a.first)
    if a.schritt in ("stunden", "alle"):
        print("3. Stundenwerte"); stunden(sens, a.first)
