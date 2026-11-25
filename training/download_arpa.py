"""Winddaten der ARPA-Lombardia-Stationen am Comer See laden (offen, ohne Zugangsdaten).

Quelle: Open Data Lombardia (Socrata), Regione Lombardia / ARPA Lombardia.
  Stationsverzeichnis   https://www.dati.lombardia.it/resource/nf78-nj6b.json
  Messwerte             Datensatz „Dati sensori meteo“ (647i-nhxk) als Tabelle; zusätzlich sucht das Skript im Katalog
                        nach Jahresarchiven (falls ältere Jahre ausgelagert sind).
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
MAIN = "647i-nhxk"            # „Dati sensori meteo“: alle Messwerte als Tabelle
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
                    "speed": v and int(v["idsensore"]), "dir": d and int(d["idsensore"]), "gust": g and int(g["idsensore"]),
                    "da": v and v.get("datastart", "")[:10], "tipologie": sorted({r["tipologia"] for r in mine})}
        print(f"  {key:10s} {name:28s} Wind {out[key]['speed']}  Richtung {out[key]['dir']}  Böe {out[key]['gust']}  seit {out[key]['da']}")
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(f"{OUT}/sensors.json", "w"), indent=1, ensure_ascii=False)
    return out


# ---------------------------------------------------------------- 2. Datensätze je Jahr

def yearly_datasets():
    """Archive „Dati sensori meteo <Jahr>“ im Katalog von Open Data Lombardia suchen: {jahr: (id, typ)}.
    typ "dataset" = abfragbare Tabelle, sonst Datei (ZIP/CSV), die ganz geladen und gefiltert wird."""
    urls = [f"{DOMAIN}/api/catalog/v1?" + urllib.parse.urlencode({"q": "sensori meteo", "limit": 200}),
            "https://api.eu.socrata.com/api/catalog/v1?" + urllib.parse.urlencode(
                {"domains": "www.dati.lombardia.it", "q": "sensori meteo", "limit": 200})]
    results = []
    for u in urls:
        try:
            results = get(u).get("results", [])
            if results:
                break
        except NotFound as e:
            print("   Katalog nicht erreichbar:", e)
    import re
    found = {}
    print("   Katalog (nur Messwert-Archive):")
    for r in results:
        res = r["resource"]; name = res.get("name", "")
        if not name.lower().startswith("dati sensori meteo") or res.get("type") not in ("dataset", "file", "blob"):
            continue                                             # Verzeichnisse („Elenco“, „Anagrafica“), Filter, Grafiken
        years = [int(x) for x in re.findall(r"(?<!\d)(20\d\d)(?!\d)", name)]
        print(f"     {res['id']}  {res.get('type', '?'):8s} {name}")
        if not years:
            continue
        span = range(min(years), max(years) + 1)                 # „dal 2011 al 2019“ -> alle Jahre dazwischen
        for y in span:
            found.setdefault(y, (res["id"], res.get("type", "?"), name))
    return found


def load_sensor_year(dataset, sensor, year):
    w = f"idsensore='{sensor}' AND data >= '{year}-01-01T00:00:00' AND data < '{year + 1}-01-01T00:00:00'"
    rows = soql(dataset, **{"$where": w, "$select": "data,valore,idoperatore"})
    return pd.DataFrame(rows)


def archive_file(ds_id, year):
    """Jahresarchiv als Datei laden (einmal), gibt den lokalen Pfad zurück."""
    os.makedirs(f"{OUT}/archive", exist_ok=True)
    meta = get(f"{DOMAIN}/api/views/{ds_id}.json")
    blob, fname = meta.get("blobId"), meta.get("blobFilename") or f"{year}.bin"
    path = f"{OUT}/archive/{year}_{fname}"
    if os.path.exists(path):
        return path
    urls = ([f"{DOMAIN}/api/views/{ds_id}/files/{blob}?download=true&filename={urllib.parse.quote(fname)}"] if blob else []) + \
           [f"{DOMAIN}/download/{ds_id}/application%2Fzip", f"{DOMAIN}/api/views/{ds_id}/rows.csv?accessType=DOWNLOAD"]
    for u in urls:
        try:
            print(f"    lade Archiv {year} ({fname}) …", flush=True)
            data = get(u, raw=True)
            open(path, "wb").write(data)
            print(f"    {len(data) / 1e6:.0f} MB", flush=True)
            return path
        except NotFound:
            continue
    raise NotFound(f"Archiv {year} ({ds_id}) nicht ladbar")


def filter_archive(path, sensor_ids):
    """Zeilen der gewünschten Sensoren aus einem Jahresarchiv (CSV, auch in ZIP), stückweise gelesen."""
    import zipfile, io
    def frames(fh):
        for ch in pd.read_csv(fh, chunksize=1_000_000):
            ch.columns = [c.strip().lower() for c in ch.columns]
            yield ch[ch["idsensore"].astype(str).isin([str(x) for x in sensor_ids])]
    if zipfile.is_zipfile(path):
        z = zipfile.ZipFile(path)
        parts = [f for n in z.namelist() if n.lower().endswith(".csv") for f in frames(z.open(n))]
    else:
        parts = list(frames(path))
    d = pd.concat(parts) if parts else pd.DataFrame()
    return d.rename(columns={"idoperatore": "idoperatore", "data": "data", "valore": "valore"})


def coverage(sid):
    """Erster und letzter Zeitpunkt eines Sensors im Hauptdatensatz."""
    try:
        r = get(f"{DOMAIN}/resource/{MAIN}.json?" + urllib.parse.urlencode(
            {"$select": "min(data) as von, max(data) as bis, count(*) as n", "$where": f"idsensore='{sid}'"}))
        return r[0] if r else {}
    except NotFound as e:
        return {"fehler": str(e)}


def download(sens, first_year):
    this = pd.Timestamp.today().year
    os.makedirs(f"{OUT}/raw", exist_ok=True)
    wanted = {s[k]: (key, k) for key, s in sens.items() for k in ("speed", "dir", "gust") if s[k]}
    print(f"   Hauptdatensatz {MAIN}:")
    for sid, (key, kind) in wanted.items():
        c = coverage(sid)
        print(f"     {key} {kind} ({sid}): {str(c.get('von', '?'))[:10]} – {str(c.get('bis', '?'))[:10]}, {c.get('n', '?')} Werte {c.get('fehler', '')}")
    yd = yearly_datasets()
    if yd:
        print("   Jahresarchive:", {y: f"{v[0]} ({v[1]})" for y, v in sorted(yd.items())})
    for y in range(first_year, this + 1):
        todo = [sid for sid in wanted if not (os.path.exists(f"{OUT}/raw/{sid}_{y}.csv") and y < this)]
        for sid in todo:
            df = pd.DataFrame()
            sources = [MAIN] + ([yd[y][0]] if y in yd and yd[y][1] == "dataset" else []) + [CURRENT]
            for ds in sources:
                try:
                    df = load_sensor_year(ds, sid, y)
                except NotFound as e:
                    print("   ", e); continue
                if len(df):
                    break
            if df.empty and y in yd and yd[y][1] != "dataset":   # Archiv als Datei
                try:
                    d = filter_archive(archive_file(yd[y][0], y), [sid])
                    df = d[[c for c in ("data", "valore", "idoperatore") if c in d]]
                except NotFound as e:
                    print("   ", e)
            df.to_csv(f"{OUT}/raw/{sid}_{y}.csv", index=False)
            key, kind = wanted[sid]
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
    raw_t = d["data"].astype(str)
    t = pd.to_datetime(raw_t, errors="coerce", dayfirst=raw_t.str.contains("/").any())   # Archiv: TT/MM/JJJJ hh:mm:ss
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
