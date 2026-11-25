"""Winddaten der ARPA-Lombardia-Stationen am Comer See laden (offen, ohne Zugangsdaten).

Quelle: Open Data Lombardia (Socrata), Regione Lombardia / ARPA Lombardia.
  Stationsverzeichnis   https://www.dati.lombardia.it/resource/nf78-nj6b.json
  Messwerte             Datensatz „Dati sensori meteo“ (i95f-5avh, laufende Daten) und je Jahr ein Archiv-Datensatz,
                        die das Skript über den Socrata-Katalog selbst sucht.
Werte: 10-Minuten-Mittel (idoperatore 3 = Mittel, 4 = Maximum/Böe); -9999 = fehlt;
Richtung 777/7777 = Windstille, 888/8888 = umlaufend.

Ablauf
  1. Sensoren nachschlagen: für jede Station in STATIONS die IDs von Velocità Vento, Direzione Vento,
     Raffica (Böe), soweit vorhanden -> data/arpa/sensors.json
  2. Messwerte je Sensor und Jahr laden -> data/arpa/raw/<sensor>_<jahr>.csv (vorhandene Jahre werden übersprungen,
     das laufende Jahr wird erneuert)
  3. Stundenwerte je Station (Mittel der 10-Minuten-Werte, Richtung vektoriell, Böe = Maximum)
     -> data/arpa/<station>_wind.csv  Spalten time (UTC, Ende der Stunde), kn, dir, gust_kn

Aufruf (Repo-Ordner):  python training/download_arpa.py [--from 2014] [--only colico,como]
"""
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "arpa")
DOMAIN = "https://www.dati.lombardia.it"
REGISTRY = "nf78-nj6b"
CURRENT = "i95f-5avh"
MS2KN = 1.943844

# Stationen am und um den Comer See (idstazione aus dem Verzeichnis, Höhe m)
STATIONS = {
    "colico":    (573,  "Colico v.La Madoneta", 229),     # Nordende, Hauptstation für Colico/Gera Lario/Domaso
    "como":      (646,  "Como Villa Gallia", 201),         # Südende, Arm von Como
    "lecco":     (706,  "Lecco v.Sora", 272),              # Lecco-Arm
    "valmadrera": (679, "Valmadrera v.Pozzi", 247),
    "samolaco":  (108,  "Samolaco v.Vignola", 206),        # Pian di Spagna / Mera-Tal nördlich des Sees
    "morbegno":  (1651, "Morbegno eliporto", 230),         # Veltlin, Talwind
    "vercana":   (1202, "Vercana", 980),                   # Hang über Domaso: Höhenwind, Föhn
    "sansiro":   (1545, "San Siro Alpe Rescascìa", 1285),  # Hang Westufer
    "canzo":     (212,  "Canzo", 1233),
}


def _ssl():
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


CTX = _ssl()


def get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}),
                                        timeout=180, context=CTX) as r:
                return json.loads(r.read())
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            if "CERTIFICATE_VERIFY_FAILED" in str(e):
                sys.exit("SSL-Zertifikate fehlen: im conda-Env mit python starten oder pip install certifi")
            wait = 60 if "429" in str(e) else 5 * (i + 1)
            print(f"    {e} – neuer Versuch in {wait} s", flush=True); time.sleep(wait)
    sys.exit(f"keine Antwort: {url[:120]}")


def soql(dataset, **q):
    """Alle Zeilen einer Socrata-Abfrage, seitenweise."""
    rows, off = [], 0
    while True:
        params = {**q, "$limit": 50000, "$offset": off}
        part = get(f"{DOMAIN}/resource/{dataset}.json?" + urllib.parse.urlencode(params))
        rows += part
        if len(part) < 50000:
            return rows
        off += 50000


# ---------------------------------------------------------------- 1. Sensoren

def sensors():
    ids = ",".join(f"'{v[0]}'" for v in STATIONS.values())
    reg = soql(REGISTRY, **{"$where": f"idstazione in({ids})"})
    out = {}
    for key, (sid, name, h) in STATIONS.items():
        mine = [r for r in reg if str(r["idstazione"]) == str(sid)]
        find = lambda word: next((r for r in mine if word in r["tipologia"].lower()), None)
        v, d = find("velocit"), find("direzione")
        g = next((r for r in mine if "raffica" in r["tipologia"].lower() and "velocit" in r["tipologia"].lower()), None)
        out[key] = {"idstazione": sid, "nome": name, "quota": h,
                    "lat": float(v["lat"]) if v else None, "lon": float(v["lng"]) if v else None,
                    "speed": v and int(v["idsensore"]), "dir": d and int(d["idsensore"]), "gust": g and int(g["idsensore"]),
                    "da": v and v.get("datastart", "")[:10], "tipologie": sorted({r["tipologia"] for r in mine})}
        print(f"  {key:10s} {name:28s} Wind {out[key]['speed']}  Richtung {out[key]['dir']}  Böe {out[key]['gust']}  seit {out[key]['da']}")
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(f"{OUT}/sensors.json", "w"), indent=1, ensure_ascii=False)
    return out


# ---------------------------------------------------------------- 2. Datensätze je Jahr

def yearly_datasets():
    """Archiv-Datensätze „Dati sensori meteo <Jahr>“ über den Socrata-Katalog suchen: {jahr: dataset_id}."""
    cat = get("https://api.us.socrata.com/api/catalog/v1?" + urllib.parse.urlencode(
        {"domains": "www.dati.lombardia.it", "q": "dati sensori meteo", "limit": 100}))
    found = {}
    for r in cat.get("results", []):
        res = r["resource"]; name = res.get("name", "")
        if "sensori meteo" not in name.lower() or res.get("type") != "dataset":
            continue
        for y in range(2000, 2100):
            if str(y) in name:
                found.setdefault(y, res["id"])
    return found


def load_sensor_year(dataset, sensor, year):
    w = f"idsensore='{sensor}' AND data >= '{year}-01-01T00:00:00' AND data < '{year + 1}-01-01T00:00:00'"
    rows = soql(dataset, **{"$where": w, "$select": "data,valore,idoperatore"})
    return pd.DataFrame(rows)


def download(sens, first_year):
    yd = yearly_datasets()
    print("Archiv-Datensätze je Jahr:", {y: yd[y] for y in sorted(yd)} or "keine gefunden")
    this = pd.Timestamp.today().year
    os.makedirs(f"{OUT}/raw", exist_ok=True)
    for key, s in sens.items():
        for kind in ("speed", "dir", "gust"):
            sid = s[kind]
            if not sid:
                continue
            for y in range(first_year, this + 1):
                f = f"{OUT}/raw/{sid}_{y}.csv"
                if os.path.exists(f) and y < this:
                    continue
                df = pd.DataFrame()
                for ds in ([yd[y]] if y in yd else []) + [CURRENT]:      # Archiv des Jahres, sonst laufender Datensatz
                    df = load_sensor_year(ds, sid, y)
                    if len(df):
                        break
                df.to_csv(f, index=False)
                print(f"  {key} {kind} {y}: {len(df)} Werte", flush=True)


# ---------------------------------------------------------------- 3. Stundenwerte

def read_raw(sid, first_year):
    parts = []
    for y in range(first_year, pd.Timestamp.today().year + 1):
        f = f"{OUT}/raw/{sid}_{y}.csv"
        if os.path.exists(f) and os.path.getsize(f) > 30:
            parts.append(pd.read_csv(f))
    if not parts:
        return pd.Series(dtype=float)
    d = pd.concat(parts)
    if "idoperatore" in d:
        d = d[d.idoperatore.astype(str).isin(["1", "3", "4"])]
    # Zeitstempel: Ortszeit ohne Zone im Archiv (laut ARPA Sonnenzeit = UTC+1); Socrata liefert ohne Zone
    t = pd.to_datetime(d["data"], errors="coerce")
    v = pd.to_numeric(d["valore"], errors="coerce")
    s = pd.Series(v.values, index=t).dropna()
    s = s[s > -9000]
    s.index = s.index.tz_localize("Etc/GMT-1").tz_convert("UTC")      # Annahme UTC+1, siehe README
    return s[~s.index.duplicated()].sort_index()


def hourly(sens, first_year):
    for key, s in sens.items():
        if not s["speed"]:
            continue
        sp = read_raw(s["speed"], first_year)
        if sp.empty:
            print(f"  {key}: keine Werte"); continue
        di = read_raw(s["dir"], first_year) if s["dir"] else pd.Series(dtype=float)
        gu = read_raw(s["gust"], first_year) if s["gust"] else pd.Series(dtype=float)
        df = pd.DataFrame({"ms": sp})
        if len(di):
            dd = di.where(di <= 360)                                    # 777/888: still bzw. umlaufend
            df["u"] = -df.ms * np.sin(np.radians(dd.reindex(df.index)))
            df["v"] = -df.ms * np.cos(np.radians(dd.reindex(df.index)))
        h = df.resample("1h", label="right", closed="right").mean()
        out = pd.DataFrame({"kn": h.ms * MS2KN})
        if "u" in h:
            out["dir"] = (np.degrees(np.arctan2(-h.u, -h.v)) + 360) % 360
        if len(gu):
            out["gust_kn"] = gu.resample("1h", label="right", closed="right").max() * MS2KN
        n = df.ms.resample("1h", label="right", closed="right").count()
        out = out[n >= 3]                                              # mindestens 3 von 6 Zehn-Minuten-Werten
        out.to_csv(f"{OUT}/{key}_wind.csv", index_label="time", float_format="%.2f")
        print(f"  {key}: {len(out)} Stunden {out.index.min():%Y-%m-%d} – {out.index.max():%Y-%m-%d}, "
              f"Mittel {out.kn.mean():.1f} kn, ab 14 kn {100 * (out.kn >= 14).mean():.1f} % der Stunden")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="first", type=int, default=2014)
    ap.add_argument("--only", help="Komma-Liste von Stationen, z. B. colico,como")
    a = ap.parse_args()
    if a.only:
        STATIONS = {k: v for k, v in STATIONS.items() if k in a.only.split(",")}
    print("1. Sensoren"); sens = sensors()
    print("2. Messwerte"); download(sens, a.first)
    print("3. Stundenwerte"); hourly(sens, a.first)
