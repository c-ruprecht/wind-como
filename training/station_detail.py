"""Genauere Stationsanalyse für den Breva (Sommer-Nachmittagswind aus Süd).

  python training/station_detail.py

Liest data/arpa/<station>_wind.csv (Zeit UTC, Stundenende) und data/arpa/sensors.json.
Schreibt results/station_detail.png und results/station_detail.txt.
"""
import json, os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARPA = os.path.join(ROOT, "data", "arpa")
RES = os.path.join(ROOT, "results")
TZ = "Europe/Rome"
SOMMER = [5, 6, 7, 8, 9]
NACHM = range(12, 20)


def load():
    meta = json.load(open(os.path.join(ARPA, "sensors.json")))
    d = {}
    for st in meta:
        fn = os.path.join(ARPA, f"{st}_wind.csv")
        if not os.path.exists(fn):
            continue
        x = pd.read_csv(fn, parse_dates=["time"]).set_index("time")
        x.index = x.index.tz_convert(TZ)
        d[st] = x
    return meta, d


def sued(dirs, lo=135, hi=225):
    return (dirs >= lo) & (dirs <= hi)


def run_lengths(mask):
    """längste zusammenhängende Folge True je Tag (mask: bool-Serie, stündlich)."""
    best, cur = 0, 0
    for v in mask:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


def main():
    os.makedirs(RES, exist_ok=True)
    meta, d = load()
    out = []
    p = lambda *a: (print(*a), out.append(" ".join(str(x) for x in a)))

    # 1. Abdeckung je Jahr (Anteil Sommerstunden vorhanden)
    p("Abdeckung Sommerstunden je Jahr (%):")
    cov = {}
    for st, x in d.items():
        s = x[x.index.month.isin(SOMMER)]
        cov[st] = (s.groupby(s.index.year)["kn"].count() / (153 * 24) * 100).round(0)
    p(pd.DataFrame(cov).fillna(0).astype(int).T.to_string())

    # 2. Tagesgang Sommer: Mittel kn und Südanteil je Stunde
    prof, south = {}, {}
    for st, x in d.items():
        s = x[x.index.month.isin(SOMMER)].dropna(subset=["kn"])
        prof[st] = s.groupby(s.index.hour)["kn"].mean()
        south[st] = s.groupby(s.index.hour)["dir"].apply(lambda v: sued(v).mean() * 100)
    prof, south = pd.DataFrame(prof), pd.DataFrame(south)
    p("\nTagesgang Sommer, Mittel kn (Ortszeit):")
    p(prof.loc[[6, 9, 11, 13, 15, 17, 19, 21]].round(1).T.to_string())
    p("\nSüdanteil % (135–225°):")
    p(south.loc[[6, 9, 11, 13, 15, 17, 19, 21]].round(0).T.to_string())

    # 3. Richtungsverteilung nachmittags (8 Sektoren)
    p("\nRichtung nachmittags 12–19 Uhr, Sommer, nur ≥ 6 kn (% je Sektor):")
    sek = ["N", "NO", "O", "SO", "S", "SW", "W", "NW"]
    rose = {}
    for st, x in d.items():
        s = x[x.index.month.isin(SOMMER) & x.index.hour.isin(NACHM) & (x.kn >= 6)].dropna(subset=["dir"])
        if len(s) < 50:
            continue
        k = ((s.dir + 22.5) % 360 // 45).astype(int)
        rose[st] = (k.value_counts(normalize=True).reindex(range(8), fill_value=0) * 100).round(0).values
    p(pd.DataFrame(rose, index=sek).T.astype(int).to_string())

    # 4. Breva-Tage je Station: ≥2 h am Stück Süd und ≥ Schwelle zwischen 11 und 20 Uhr
    p("\nTage mit ≥2 h am Stück Süd ≥ X kn (11–20 Uhr), Mittel je Sommer:")
    days = {}
    for st, x in d.items():
        s = x[x.index.month.isin(SOMMER) & x.index.hour.isin(range(11, 21))]
        row = {}
        for thr in (8, 10, 12, 14, 18):
            m = (s.kn >= thr) & sued(s.dir)
            rl = m.groupby(s.index.date).apply(run_lengths)
            n_years = max(1, len(set(pd.DatetimeIndex(s.index).year)))
            row[f"≥{thr}"] = round((rl >= 2).sum() / n_years, 1)
        days[st] = row
    p(pd.DataFrame(days).T.to_string())

    # 5. Bei Breva in Samolaco: was zeigen die anderen? (gleichzeitige Stunden)
    ref = "samolaco"
    if ref in d:
        r = d[ref]
        sel = r[r.index.month.isin(SOMMER) & r.index.hour.isin(NACHM) & (r.kn >= 12) & sued(r.dir)]
        p(f"\nStunden mit Samolaco ≥ 12 kn aus Süd (n={len(sel)}): gleichzeitig an den anderen Stationen")
        rows = {}
        for st, x in d.items():
            j = x.reindex(sel.index)
            ok = j.kn.notna()
            rows[st] = dict(kn=round(j.kn[ok].mean(), 1), verh=round((j.kn[ok] / sel.kn[ok]).median(), 2),
                            sued=round(sued(j.dir[ok]).mean() * 100), boe=round((j.gust_kn[ok] / j.kn[ok]).median(), 2))
        p(pd.DataFrame(rows).T.to_string())

        # Beginn: erste Stunde ≥ 8 kn Süd an Samolaco-Breva-Tagen
        bd = sorted(set(sel.index.date))
        p(f"\nEinsetzen (erste Stunde ≥ 8 kn Süd, 9–20 Uhr) an {len(bd)} Samolaco-Breva-Tagen, Median Ortszeit:")
        onset = {}
        for st, x in d.items():
            s = x[x.index.month.isin(SOMMER) & x.index.hour.isin(range(9, 21))]
            s = s[pd.Index(s.index.date).isin(bd)]
            m = s[(s.kn >= 8) & sued(s.dir)]
            if len(m) < 30:
                continue
            first = m.groupby(m.index.date).apply(lambda v: v.index.hour.min())
            last = m.groupby(m.index.date).apply(lambda v: v.index.hour.max())
            onset[st] = dict(beginn=first.median(), ende=last.median(), tage=len(first))
        p(pd.DataFrame(onset).T.to_string())

    # 6. Monatsgang Samolaco und Vercana
    p("\nBreva-Tage (≥2 h Süd ≥ 12 kn, 11–20 Uhr) je Monat, Mittel über Jahre:")
    mon = {}
    for st in ("samolaco", "vercana", "colico", "morbegno"):
        if st not in d:
            continue
        x = d[st]
        s = x[x.index.hour.isin(range(11, 21))]
        m = (s.kn >= 12) & sued(s.dir)
        rl = m.groupby(s.index.date).apply(run_lengths)
        rl.index = pd.to_datetime(rl.index)
        yrs = rl.index.year.nunique()
        mon[st] = ((rl >= 2).groupby(rl.index.month).sum() / yrs).round(1)
    p(pd.DataFrame(mon).T.to_string())

    # 7. Jahrestrend Samolaco (Mittel Sommernachmittag) – Hinweis auf Sensorwechsel/Umstellung
    p("\nSommer-Nachmittag 13–18 Uhr, Mittel kn je Jahr:")
    tr = {}
    for st, x in d.items():
        s = x[x.index.month.isin(SOMMER) & x.index.hour.isin(range(13, 19))]
        tr[st] = s.groupby(s.index.year)["kn"].mean().round(1)
    p(pd.DataFrame(tr).T.to_string())

    open(os.path.join(RES, "station_detail.txt"), "w").write("\n".join(out) + "\n")

    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
        for st in prof:
            lw = 2.5 if st in ("samolaco", "vercana", "colico") else 1
            ax[0].plot(prof.index, prof[st], label=st, lw=lw)
            ax[1].plot(south.index, south[st], label=st, lw=lw)
        ax[0].set(title="Sommer (Mai–Sep): mittlere Geschwindigkeit", xlabel="Ortszeit", ylabel="kn")
        ax[1].set(title="Anteil Südwind 135–225°", xlabel="Ortszeit", ylabel="%")
        ax[0].legend(fontsize=8); ax[0].grid(alpha=.3); ax[1].grid(alpha=.3)
        fig.tight_layout(); fig.savefig(os.path.join(RES, "station_detail.png"), dpi=120)
    except ImportError:
        pass


if __name__ == "__main__":
    main()
