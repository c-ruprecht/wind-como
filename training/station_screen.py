"""Welche ARPA-Station misst den Wind am See? Bewertung jeder Station nur aus ihren eigenen Messungen.

Für Kiten am oberen Comer See zählt vor allem der Breva (Südwind, Nachmittag, Mai–September). Eine Station, die ihn
gut misst, zeigt im Sommer einen klaren Tagesgang mit Maximum am Nachmittag, Wind aus Süd entlang der Seeachse und
ein normales Verhältnis Böe/Mittel (geschützte Standorte: kaum Mittelwind, aber hohe Böen).

Kennzahlen je Station (Mai–September)
  mittag_kn      Mittel 13–18 Uhr Ortszeit          frueh_kn   Mittel 5–9 Uhr (Tivano/Nordwind)
  amplitude      mittag_kn − Mittel 0–6 Uhr          p10/p14    Anteil Nachmittagsstunden ab 10 / 14 kn
  boe_faktor     Median Böe / Mittel bei ≥ 4 kn       sued       Anteil Nachmittagsstunden mit Wind aus 135–225°
  tage_breva     Tage/Sommer mit ≥ 2 h am Stück ab 10 kn zwischen 12 und 19 Uhr
Zusätzlich: Zusammenhang der Nachmittags-Tagesmaxima zwischen den Stationen (r).

Aufruf (Repo-Ordner): python training/station_screen.py      -> results/station_screen.csv
"""
import glob, json, os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARPA = os.path.join(ROOT, "data", "arpa")


def runs(flags):
    best = cur = 0
    for f in flags:
        cur = cur + 1 if f else 0
        best = max(best, cur)
    return best


def main():
    sens = json.load(open(f"{ARPA}/sensors.json")) if os.path.exists(f"{ARPA}/sensors.json") else {}
    rows, daily = [], {}
    for f in sorted(glob.glob(f"{ARPA}/*_wind.csv")):
        key = os.path.basename(f)[:-9]
        d = pd.read_csv(f, parse_dates=["time"]).set_index("time")
        loc = d.index.tz_convert("Europe/Rome")
        S = d[loc.month.isin([5, 6, 7, 8, 9])]
        sl = S.index.tz_convert("Europe/Rome"); h = sl.hour
        aft = S[(h >= 13) & (h <= 18)]
        night = S[h <= 5]
        early = S[(h >= 5) & (h <= 9)]
        g = S[S.kn >= 4]
        sued = ((aft["dir"] >= 135) & (aft["dir"] <= 225)).mean() if "dir" in aft else np.nan
        win = S[(h >= 12) & (h <= 19)]
        per_day = win.groupby(win.index.tz_convert("Europe/Rome").date).kn.apply(lambda x: runs(x.values >= 10))
        years = max(1, S.index.year.nunique())
        mx = win.groupby(win.index.tz_convert("Europe/Rome").date).kn.max()
        daily[key] = mx
        s = sens.get(key, {})
        rows.append(dict(station=key, name=s.get("nome", ""), hoehe=s.get("quota"), stunden=len(S),
                         mittag_kn=round(aft.kn.mean(), 1), frueh_kn=round(early.kn.mean(), 1),
                         amplitude=round(aft.kn.mean() - night.kn.mean(), 1),
                         p10=round((aft.kn >= 10).mean() * 100, 1), p14=round((aft.kn >= 14).mean() * 100, 1),
                         boe_faktor=round(float((g.gust_kn / g.kn).median()), 2) if "gust_kn" in g and len(g) else np.nan,
                         sued=round(sued * 100), tage_breva=round((per_day >= 2).sum() / years, 1),
                         max_stunde=int(S.kn.groupby(sl.hour).mean().idxmax())))
    R = pd.DataFrame(rows).sort_values("tage_breva", ascending=False)
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    R.to_csv(os.path.join(ROOT, "results", "station_screen.csv"), index=False)
    pd.set_option("display.width", 200)
    print("Sommer (Mai–Sep), Ortszeit. p10/p14/sued in % der Nachmittagsstunden 13–18 Uhr, tage_breva je Sommer:")
    print(R.to_string(index=False))
    if len(daily) > 1:
        M = pd.DataFrame(daily)
        print("\nZusammenhang der Nachmittags-Tagesmaxima (r):")
        print(M.corr().round(2).to_string())
    print("\nGute Breva-Station: deutliche Amplitude, Maximum 14–18 Uhr, hoher Anteil Süd, Böe-Faktor um 1,5–2 "
          "(viel höher = geschützter Standort).")


if __name__ == "__main__":
    main()
