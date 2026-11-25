"""Daten für die Seite „Windanalyse & Breva“ (app/analyse.html) aus den Auswertungen.

  python training/export_analyse.py

Liest data/arpa/*_wind.csv und results/*.csv, schreibt app/analyse.json und kopiert Bilder nach app/img/.
"""
import json, os, shutil
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
APP = os.path.join(ROOT, "app")
ARPA = os.path.join(ROOT, "data", "arpa")
TZ = "Europe/Rome"
SEASON = [3, 4, 5, 6, 7, 8, 9, 10]
STATIONS = {"samolaco": ("Samolaco", (112, 202)), "vercana": ("Vercana", (180, 270)), "colico": ("Colico", (200, 315)),
            "morbegno": ("Morbegno", (200, 290)), "sansiro": ("San Siro", (180, 270)), "como": ("Como", (0, 90))}
LABEL = {
    "wind_see_15_sued": "Südwind über dem See (Modell, 15 Uhr)",
    "wind_see_15": "Wind über dem See (Modell, 15 Uhr)",
    "taupunktdiff_milano": "Trockene Luft (Taupunktabstand Mailand)",
    "wind_milano_12": "Wind in der Po-Ebene (Mailand, 12 Uhr)",
    "dp_tag_minus_nacht": "Tief im Tal bildet sich tagsüber (Druckgefälle 15 minus 6 Uhr)",
    "dp_bergamo_sondrio_15": "Druckgefälle Bergamo → Sondrio (Veltlin), 15 Uhr",
    "dp_po_tal_15": "Druckgefälle Mailand → Chiavenna, 15 Uhr",
    "dp_po_tal_18": "Druckgefälle Mailand → Chiavenna, 18 Uhr",
    "bodenfeuchte_milano": "Bodenfeuchte Po-Ebene",
    "bodenfeuchte_chiavenna": "Bodenfeuchte Tal",
    "dp_muenchen_genova_12": "Druck München − Genua (Alpen-Föhnlage)",
    "wolken_chiavenna": "Wolken im Tal (Chiavenna)",
    "wolken_tief_see": "Tiefe Wolken über dem See",
    "wolken_morgen_see": "Wolken am Morgen über dem See",
    "luft_minus_see_t30": "Warme Luft über kühlem See (Ersatz Wassertemperatur)",
    "geo_aus_sued": "Großräumige Strömung aus Süd",
    "tmax_sondrio": "Höchsttemperatur Sondrio",
    "tmax_bergamo": "Höchsttemperatur Bergamo (Ebene)",
    "dp_zurich_milano_12": "Nordföhn-Index (Zürich − Mailand)",
    "rad_chiavenna": "Sonne im Tal (Einstrahlung Chiavenna)",
    "see_t30": "Ersatz Wassertemperatur (30-Tage-Mittel Luft am See)",
    "regen_see": "Regen am See 11–19 Uhr",
    "regen_chiavenna": "Regen im Tal 11–19 Uhr",
}


def load(st):
    x = pd.read_csv(os.path.join(ARPA, f"{st}_wind.csv"), parse_dates=["time"]).set_index("time")
    x.index = pd.DatetimeIndex(x.index).tz_convert(TZ).tz_localize(None)
    return x


def rnd(v, n=2):
    return None if v is None or (isinstance(v, float) and not np.isfinite(v)) else round(float(v), n)


def main():
    out = {"stand": pd.Timestamp.today().strftime("%Y-%m-%d")}
    D = pd.read_csv(f"{RES}/breva_tage.csv", index_col=0, parse_dates=True)
    y = (D.klasse == "Breva").astype(int)
    out["jahre"] = f"{D.index.year.min()}–{D.index.year.max()}"
    # Tagesgang je Station (Mär–Okt): mittlere Stärke und Anteil Breva-Richtung, an Breva-Tagen und sonst
    prof = {}
    for st, (name, (lo, hi)) in STATIONS.items():
        f = os.path.join(ARPA, f"{st}_wind.csv")
        if not os.path.exists(f):
            continue
        x = load(st)
        x = x[x.index.month.isin(SEASON)]
        day = x.index.normalize()
        isb = pd.Series(day).map(y).fillna(0).astype(bool).values
        insec = (x.dir >= lo) & (x.dir <= hi) if lo <= hi else (x.dir >= lo) | (x.dir <= hi)
        g = lambda m: x[m].groupby(x.index.hour[m]).kn.mean().reindex(range(24))
        prof[st] = {"name": name, "breva": [rnd(v, 1) for v in g(isb)], "sonst": [rnd(v, 1) for v in g(~isb)],
                    "richtung": [rnd(v * 100, 0) for v in insec[isb].groupby(x.index.hour[isb]).mean().reindex(range(24))]}
    out["tagesgang"] = prof
    # Wie früh verraten die Stationen den Breva? AUC je Stunde (Breva-Komponente) gegen Breva-Tag
    from sklearn.metrics import roc_auc_score
    AX = {"samolaco": 157, "vercana": 225, "colico": 270, "morbegno": 245}
    timing = {}
    for st, ax in AX.items():
        x = load(st)
        c = x.kn * np.cos(np.radians(x.dir - ax))
        row = {}
        for h in range(8, 16):
            v = c[c.index.hour == h]; v.index = v.index.normalize()
            j = pd.concat([v.rename("x"), y.rename("y")], axis=1, join="inner").dropna()
            row[str(h)] = rnd(roc_auc_score(j.y, j.x), 3) if j.y.nunique() == 2 else None
        timing[st] = row
    out["timing"] = timing
    yv = y.shift(1, freq="D").reindex(y.index)
    j = pd.concat([yv.rename("v"), y.rename("y")], axis=1).dropna()
    out["vortag"] = {"nach_breva": rnd(j[j.v == 1].y.mean(), 3), "sonst": rnd(j[j.v == 0].y.mean(), 3)}
    # Klassen je Monat (Tage je Saison)
    yrs = D.index.year.nunique()
    kl = (pd.crosstab(D.index.month, D.klasse) / yrs).round(1)
    out["klassen"] = {"monate": [int(m) for m in kl.index], "klassen": {k: kl[k].tolist() for k in kl.columns}}
    out["klassen_saison"] = {k: rnd(v, 1) for k, v in (D.klasse.value_counts() / yrs).items()}
    # Breva-Tage je Jahr (Saison)
    out["je_jahr"] = {str(k): int(v) for k, v in y.groupby(D.index.year).sum().items()}
    # Satellit je Klasse
    s = D.sat_see.notna()
    out["sat_je_klasse"] = {k: {"median": rnd(v.median(), 1), "n": int(len(v))} for k, v in D[s].groupby("klasse").sat_see}
    # Faktoren (Prüfung je Größe)
    f = f"{RES}/pruefung_era5.csv"
    if os.path.exists(f):
        P = pd.read_csv(f)
        P = P[P.urteil.isin(["stark", "mittel"])].head(16)
        out["faktoren"] = [{"merkmal": r.merkmal, "name": LABEL.get(r.merkmal, r.merkmal), "breva": rnd(r.breva),
                            "kein": rnd(r.kein), "auc": rnd(r.auc_je_monat, 2), "kraft": rnd(r.kraft, 2),
                            "stabil": rnd(r.stabil, 2), "sat": rnd(r.rho_satellit, 2), "urteil": r.urteil,
                            "wie": r.wie if isinstance(r.wie, str) else ""} for r in P.itertuples()]
    # Vorhersagbarkeit
    f = f"{RES}/breva_vorlauf_v2.csv"
    if os.path.exists(f):
        V = pd.read_csv(f)
        out["vorlauf"] = {thr.strip("≥"): [{"vorlauf": r.vorlauf, "auc": r.auc, "brier": r.brier} for r in g.itertuples()]
                          for thr, g in V.groupby("schwelle")}
    f = f"{RES}/heute_skill.csv"
    if os.path.exists(f):
        out["heute"] = pd.read_csv(f).to_dict("records")
    # Stationen gegen Satellit (Breva-Abende)
    R = pd.read_csv(f"{RES}/station_ranking.csv")
    R = R[R.fall.str.contains("Breva")]
    out["stationen"] = R[["station", "n", "r", "verhaeltnis_see_zu_station", "auc_see_ab_12kn"]].to_dict("records")
    # Spots und Satellit aus breva.json
    b = json.load(open(f"{APP}/breva.json"))
    out["spot_zu_see"] = b.get("spot_zu_see")
    out["sat_abende"] = b.get("sat_abende")
    out["overlay"] = b.get("overlay")
    out["klima"] = b.get("klima")
    out["satfaktor_samolaco"] = rnd(float((D.see_max_est / D.sam_max).median()), 2)
    for img in ("breva_top.png", "station_detail.png"):
        if os.path.exists(f"{RES}/{img}"):
            shutil.copy(f"{RES}/{img}", f"{APP}/img/{img}")
    json.dump(out, open(f"{APP}/analyse.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print("geschrieben: app/analyse.json, Bilder nach app/img/")
    print(" Vortag:", out["vortag"], " Klassen/Saison:", out["klassen_saison"])
    print(" Timing Vercana:", out["timing"].get("vercana"))


if __name__ == "__main__":
    main()
