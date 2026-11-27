"""Einzelne ECMWF-Läufe (IFS HRES 9 km) holen: genau der Lauf, der zur Entscheidungszeit am Morgen verfügbar war.

Warum: Das Heute-Modell wurde bisher mit dem Lauf vom Vortag geprüft (previous_day1), weil der „gleiche Tag“
im Previous-Runs-Archiv für die Nachmittagsstunden aus Läufen stammt, die morgens noch nicht da sind (Leck).
Die Single-Runs-API liefert dagegen einen Lauf nach Startzeit – ECMWF IFS HRES 9 km ab 14.03.2024.

  00 UTC-Lauf des Tages: um 11 und 13 Uhr sicher verfügbar (Veröffentlichung ca. 7–8 h nach Start)
  18 UTC-Lauf des Vortags: für die 9-Uhr-Entscheidung (der 00-UTC-Lauf ist im Sommer um 9 Uhr evtl. noch nicht da)

Gespeichert wird je Lauf der Zieltag und die 7 Tage danach (Ortszeit), alle 11 Punkte, die 8 Grundgrößen:
  data/runs/ecmwf_ifs_<HH>z_<jahr>.csv  Spalten tag, vorlauf (0 = Zieltag … 7), punkt, time (Ortszeit), <größen>
Damit gibt es nebenbei ECMWF 9 km für Tag 1–7 ab 3/2024 (das Previous-Runs-Archiv hat 9 km erst ab 10/2025).
  python training/einzellaeufe.py umformen   schreibt daraus data/prevv2/ecmwf_ifs00z_<punkt>_<jahr>.csv
  im Format des Previous-Runs-Archivs (…_previous_day0 … day7) für modell_vergleich.py und train_breva.py.
Fertige Läufe werden übersprungen; beim Tageslimit sauber abbrechen und am nächsten Tag weitermachen.

Aufwand: 1 Abruf je Lauf (alle Punkte zusammen, zählt als 11). Nur 00 UTC seit 3/2024: ca. 990 Abrufe ≈ 11 000
gewichtete, also zwei Tage Kontingent (~2,2 h Laufzeit). Mit 18 UTC doppelt.

Aufruf:  python training/einzellaeufe.py [--laeufe 00,18] [--ab 2024-03-14] [--modell ecmwf_ifs]
"""
import argparse, glob, http.client, json, os, sys, time, urllib.error, urllib.parse, urllib.request
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402
from breva_events import _ctx  # noqa: E402

URL = "https://single-runs-api.open-meteo.com/v1/forecast"
OUT = os.path.join(B.DATA, "runs")
PAUSE = 8.0          # Sekunden zwischen Abrufen: 11 Punkte × 450/h bleibt unter 5 000 gewichteten Abrufen je Stunde


class Tageslimit(Exception):
    pass


def fetch(q):
    url = URL + "?" + urllib.parse.urlencode(q)
    for i in range(5):
        try:
            with urllib.request.urlopen(url, timeout=180, context=_ctx()) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="ignore")[:300]
            if "daily" in body.lower():
                raise Tageslimit(body)
            if e.code == 429 or "limit" in body.lower():
                wait = 70 * (i + 1); print(f"   Limit, warte {wait} s ({body.strip()[:80]})", flush=True); time.sleep(wait); continue
            if e.code == 400:
                raise ValueError(body)
            time.sleep(15 * (i + 1))
        except (OSError, http.client.HTTPException) as e:      # Zeitüberschreitung, Verbindung getrennt, SSL
            print("  ", e); time.sleep(15 * (i + 1))
    raise RuntimeError("keine Antwort")


def done_runs(model, hh):
    s = set()
    for f in glob.glob(f"{OUT}/{model}_{hh}z_*.csv"):
        head = pd.read_csv(f, nrows=1)
        if "vorlauf" not in head:
            sys.exit(f"{f} ist im alten Format (nur Zieltag). Bitte data/runs/ löschen und neu starten – "
                     "das neue Format speichert die Tage 1–7 gleich mit.")
        s |= set(pd.read_csv(f, usecols=["tag"]).tag.astype(str))
    return s


def umformen(model, hh):
    """Läufe -> Previous-Runs-Format: Wert zur Stunde t aus dem Lauf, dessen Zieltag t − L Tage ist = previous_dayL."""
    fs = sorted(glob.glob(f"{OUT}/{model}_{hh}z_*.csv"))
    if not fs:
        sys.exit("keine Läufe – erst laden")
    D = pd.concat(pd.read_csv(f) for f in fs)
    D["time"] = pd.to_datetime(D.time)
    vs = [c for c in D.columns if c not in ("tag", "vorlauf", "punkt", "time")]
    name = f"{model}{hh}z"
    os.makedirs(B.PREV, exist_ok=True)
    for p, g in D.groupby("punkt"):
        W = g.pivot_table(index="time", columns="vorlauf", values=vs)
        W.columns = [f"{v}_previous_day{int(L)}" for v, L in W.columns]
        for y, gy in W.groupby(W.index.year):
            gy.reset_index().to_csv(f"{B.PREV}/{name}_{p}_{y}.csv", index=False)
    print(f"geschrieben: data/prevv2/{name}_<punkt>_<jahr>.csv – Modellname für modell_vergleich: {name}")


def one_run(model, run_utc, day, points, variables, use_fh=True):
    q = dict(latitude=",".join(str(points[p][0]) for p in points), longitude=",".join(str(points[p][1]) for p in points),
             models=model, run=run_utc.strftime("%Y-%m-%dT%H:%M"), hourly=",".join(variables),
             timezone=B.TZ, wind_speed_unit="kn")
    if use_fh:
        q["forecast_hours"] = 210
    j = fetch(q)
    js = j if isinstance(j, list) else [j]
    rows = []
    for p, r in zip(points, js):
        d = pd.DataFrame(r["hourly"])
        d["time"] = pd.to_datetime(d.time)
        lead = (d.time.dt.normalize() - pd.Timestamp(day)).dt.days
        d = d[(lead >= 0) & (lead <= 7)].copy()                     # Zieltag + 7 Tage (Ortszeit)
        d.insert(0, "punkt", p); d.insert(0, "vorlauf", lead[d.index].values); d.insert(0, "tag", day)
        rows.append(d)
    return pd.concat(rows)


def main(model, runs, start):
    os.makedirs(OUT, exist_ok=True)
    points = {p: (la, lo) for p, (la, lo, _) in B.POINTS.items()}
    variables = list(B.BASIC)
    yesterday = pd.Timestamp.today().normalize() - pd.Timedelta(days=1)
    days = pd.date_range(start, yesterday, freq="D")
    use_fh = True
    for hh in runs:
        have = done_runs(model, hh)
        todo = [d for d in days if d.strftime("%Y-%m-%d") not in have]
        print(f"{model} {hh} UTC: {len(todo)} von {len(days)} Tagen fehlen (ca. {len(todo) * PAUSE / 3600:.1f} h)", flush=True)
        buf = []

        def flush():
            if not buf:
                return
            D = pd.concat(buf); buf.clear()
            for y, g in D.groupby(D.tag.str[:4]):
                f = f"{OUT}/{model}_{hh}z_{y}.csv"
                g.to_csv(f, mode="a", header=not os.path.exists(f), index=False)

        try:
            for i, d in enumerate(todo):
                day = d.strftime("%Y-%m-%d")
                run = (d - pd.Timedelta(days=1) + pd.Timedelta(hours=int(hh))) if int(hh) >= 12 else d + pd.Timedelta(hours=int(hh))
                try:
                    buf.append(one_run(model, run, day, points, variables, use_fh))
                except ValueError as e:
                    if use_fh and "forecast_hours" in str(e):
                        use_fh = False
                        buf.append(one_run(model, run, day, points, variables, use_fh))
                    else:
                        print(f"  {day} {hh}z: {str(e)[:120]}"); continue
                if (i + 1) % 20 == 0:
                    flush(); print(f"  {hh}z bis {day} ({i + 1}/{len(todo)})", flush=True)
                time.sleep(PAUSE)
        except Tageslimit:
            flush(); sys.exit("Tageslimit erreicht – morgen denselben Befehl erneut starten, Fertiges bleibt.")
        flush()
    print("fertig:", sorted(glob.glob(f"{OUT}/{model}_*z_*.csv")))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("schritt", nargs="?", default="laden", choices=["laden", "umformen"])
    ap.add_argument("--laeufe", default="00", help="00 (Lauf des Tages) und/oder 18 (Vortag 18 UTC), z. B. 00,18")
    ap.add_argument("--ab", default="2024-03-14")
    ap.add_argument("--modell", default="ecmwf_ifs")
    a = ap.parse_args()
    if a.schritt == "umformen":
        for hh in a.laeufe.split(","):
            umformen(a.modell, hh)
    else:
        main(a.modell, a.laeufe.split(","), a.ab)
