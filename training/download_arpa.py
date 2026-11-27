"""Winddaten der ARPA-Lombardia-Stationen am Comer See laden (offen, ohne Zugangsdaten).

Quelle: Open Data Lombardia (Socrata), Regione Lombardia / ARPA Lombardia.
  Stationsverzeichnis   https://www.dati.lombardia.it/resource/nf78-nj6b.json
  Messwerte             je Messgröße und Zeitraum eigene Datensätze (Geschwindigkeit ab 2021 hu5q-68e3, 2011–2020
                        x9gp-z9xx; Richtung purm-rsjf / ypty-e75m; Böen gi9u-2aez / ppwf-2tzh), dazu „Dati sensori
                        meteo“ (647i-nhxk) mit den letzten ~7 Monaten. Zuordnung wie im R-Paket ARPALData.
Werte: 10-Minuten-Mittel (idoperatore 3 = Mittel, 4 = Maximum/Böe); -9999 = fehlt;
Richtung 777/7777 = Windstille, 888/8888 = umlaufend.
Zeitstempel: feste Zone UTC+1 (keine Sommerzeit – geprüft: an den Umstelltagen weder Lücke noch Doppelung).
Böen: nur im Archiv (bis 2/2026), die Livedaten der letzten Monate enthalten keine Böen.

Ablauf
  1. Sensoren nachschlagen: für jede Station in STATIONS die IDs von Velocità Vento und Direzione Vento
     (Böen liegen unter der ID der Geschwindigkeit) -> data/arpa/sensors.json
  2. Messwerte je Größe, Sensor und Jahr -> data/arpa/raw/<größe>_<sensor>_<jahr>.csv (vorhandene Jahre übersprungen,
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
MAIN = "647i-nhxk"            # „Dati sensori meteo“: nur die letzten ~7 Monate, alle Größen
# Historie je Messgröße und Zeitraum (wie im R-Paket ARPALData, url_W_year_par):
HIST = {"speed": [(2021, "hu5q-68e3"), (2011, "x9gp-z9xx"), (0, "ed5f-uim8")],
        "dir":   [(2021, "purm-rsjf"), (2011, "ypty-e75m"), (0, "cptm-adt5")],
        "gust":  [(2021, "gi9u-2aez"), (0, "ppwf-2tzh")],          # Böen: gleiche Sensor-ID wie die Geschwindigkeit
        # weitere Größen (arpa_extra.py), Kennungen wie in ARPALData url_W_year_par
        "temp":  [(2021, "w9wd-u6jh"), (2011, "d4kj-kbpj"), (0, "6eu4-4tja")],
        "rh":    [(2021, "823w-fh4c"), (2011, "xpun-8722"), (0, "nure-mhrg")],
        "rain":  [(2021, "pstb-pga6"), (2011, "2kar-pnuk"), (0, "e7r2-7m84")],
        "rad":   [(2021, "cxym-eps2"), (0, "63ns-e4tv")]}


def hist_dataset(kind, year):
    return next(ds for y0, ds in HIST[kind] if year >= y0)
CURRENT = "i95f-5avh"         # gefilterte Ansicht davon (nur die letzten Wochen), Rückfall
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


class NotFound(Exception):
    pass


def get(url, tries=6, raw=False):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "*/*" if raw else "application/json"}),
                                        timeout=600, context=CTX) as r:
                body = r.read()
                return body if raw else json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code in (400, 403, 404):
                raise NotFound(f"{e.code} {url[:140]}")
            wait = 60 if e.code == 429 else 5 * (i + 1)
            print(f"    {e} – neuer Versuch in {wait} s", flush=True); time.sleep(wait)
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
                    "speed": v and int(v["idsensore"]), "dir": d and int(d["idsensore"]),
                    "gust": (g and int(g["idsensore"])) or (v and int(v["idsensore"])),   # ARPA: Böen unter der ID der Geschwindigkeit
                    "da": v and v.get("datastart", "")[:10], "tipologie": sorted({r["tipologia"] for r in mine})}
        print(f"  {key:10s} {name:28s} Wind {out[key]['speed']}  Richtung {out[key]['dir']}  Böe {out[key]['gust']}  seit {out[key]['da']}")
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(f"{OUT}/sensors.json", "w"), indent=1, ensure_ascii=False)
    return out


# ---------------------------------------------------------------- 2. Datensätze je Jahr

def load_sensor_year(dataset, sensor, year, since=None):
    lo = since or f"{year}-01-01T00:00:00"
    w = f"idsensore='{sensor}' AND data >= '{lo}' AND data < '{year + 1}-01-01T00:00:00'"
    rows = soql(dataset, **{"$where": w})
    d = pd.DataFrame(rows)
    return d[[c for c in ("data", "valore", "stato", "idoperatore") if c in d]] if len(d) else d


def fetch_year(f, kind, sid, y, this):
    """Ein Sensor-Jahr laden. Vergangene Jahre: vorhanden = fertig. Laufendes Jahr: nur ab dem letzten Wert
    nachladen (letzte 7 Monate aus dem Hauptdatensatz) und anhängen. Gibt die Zahl neuer Werte zurück (None = übersprungen)."""
    old = None
    if os.path.exists(f):
        if y < this:
            return None
        old = pd.read_csv(f, dtype={"data": str}) if os.path.getsize(f) > 30 else None
    since = None
    if old is not None and len(old) and "data" in old:
        since = str(old.data.max())[:19]
    if since is not None:
        if kind == "gust":                       # Böen gibt es nur im Archiv (bis 2/2026), nichts nachzuladen
            return None
        sets = [MAIN]
    else:
        sets = [hist_dataset(kind, y), MAIN if kind != "gust" else None]
    parts = []
    for ds in sets:
        if not ds:
            continue
        try:
            parts.append(load_sensor_year(ds, sid, y, since))
        except NotFound as e:
            print("   ", e)
    new = pd.concat([p for p in parts if len(p)]) if any(len(p) for p in parts) else pd.DataFrame()
    n = len(new)
    if old is not None and len(old):
        new = pd.concat([old, new]) if n else old
    if len(new):
        new = new.drop_duplicates("data", keep="last").sort_values("data")
    new.to_csv(f, index=False)
    return n


def download(sens, first_year):
    this = pd.Timestamp.today().year
    os.makedirs(f"{OUT}/raw", exist_ok=True)
    jobs = [(key, kind, s[kind]) for key, s in sens.items() for kind in ("speed", "dir", "gust") if s[kind]]
    for y in range(first_year, this + 1):
        for key, kind, sid in jobs:
            f = f"{OUT}/raw/{kind}_{sid}_{y}.csv"
            n = fetch_year(f, kind, sid, y, this)      # Historie + letzte 7 Monate; laufendes Jahr nur nachladen
            if n is not None:
                print(f"  {key} {kind} {y}: {n} neue Werte", flush=True)


# ---------------------------------------------------------------- 3. Stundenwerte

def read_raw(kind, sid, first_year):
    parts = []
    for y in range(first_year, pd.Timestamp.today().year + 1):
        f = f"{OUT}/raw/{kind}_{sid}_{y}.csv"
        if os.path.exists(f) and os.path.getsize(f) > 30:
            parts.append(pd.read_csv(f))
    if not parts:
        return pd.Series(dtype=float)
    d = pd.concat(parts)
    if "stato" in d:
        d = d[d.stato.astype(str).str.upper().isin(["VA", "NAN"])]          # nur gültige Werte
    # Zeitstempel: Ortszeit ohne Zone im Archiv (laut ARPA Sonnenzeit = UTC+1); Socrata liefert ohne Zone
    raw_t = d["data"].astype(str)
    t = pd.to_datetime(raw_t, errors="coerce", dayfirst=raw_t.str.contains("/").any())   # Archiv: TT/MM/JJJJ hh:mm:ss
    v = pd.to_numeric(d["valore"], errors="coerce")
    s = pd.Series(v.values, index=t).dropna()
    s = s[s > -9000]
    s.index = s.index.tz_localize("Etc/GMT-1").tz_convert("UTC")      # Annahme UTC+1, siehe README
    return s[~s.index.duplicated()].sort_index()


def clean(out, key):
    """Plausibilität der Stundenwerte: festhängende Richtung (≥ 12 h gleich bei Wind > 3 kn) und Einzelspitzen
    (> 30 kn und mehr als dreimal so viel wie die Stunden davor und danach) werden entfernt."""
    n0 = out.notna().sum()
    if "dir" in out:
        r = out.dir.round(0)
        grp = (r != r.shift()).cumsum()
        stuck = (r.groupby(grp).transform("size") >= 12) & (out.kn > 3)
        out.loc[stuck, "dir"] = np.nan
    nb = pd.concat([out.kn.shift(1), out.kn.shift(-1)], axis=1).mean(axis=1)
    spike = (out.kn > 30) & (out.kn > 3 * nb.clip(lower=1))
    out.loc[spike, ["kn"] + (["dir"] if "dir" in out else [])] = np.nan
    if "gust_kn" in out:
        out.loc[out.gust_kn < out.kn * 0.9, "gust_kn"] = np.nan
    d = (n0 - out.notna().sum())
    if d.sum():
        print(f"  {key}: bereinigt " + ", ".join(f"{c} {int(v)}" for c, v in d.items() if v))
    return out


def hourly(sens, first_year):
    for key, s in sens.items():
        if not s["speed"]:
            continue
        sp = read_raw("speed", s["speed"], first_year)
        if sp.empty:
            print(f"  {key}: keine Werte"); continue
        di = read_raw("dir", s["dir"], first_year) if s["dir"] else pd.Series(dtype=float)
        gu = read_raw("gust", s["gust"], first_year) if s["gust"] else pd.Series(dtype=float)
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
        out = clean(out, key)
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
