"""Breva-Ereignisse aus dem Satelliten, Wetter davor und Vorhersagbarkeit nach Vorlauf.

  python training/breva_events.py wetter        # ERA5 stündlich an 5 Punkten, 2014 – gestern (einmalig, zwischengespeichert)
  python training/breva_events.py laeufe        # alte Vorhersageläufe (ECMWF IFS, 1–7 Tage vorher), 2024 – gestern
  python training/breva_events.py ereignisse    # Breva-Abende aus Sentinel-1 + Breva-Tage aus Samolaco
  python training/breva_events.py analyse       # welche Wettergrößen trennen Breva-Tage von ruhigen Tagen (ERA5)
  python training/breva_events.py lang          # was macht einen langen Breva (um 19:15 noch Wind auf dem See)
  python training/breva_events.py vorlauf       # ab wie vielen Tagen vorher ist der Breva vorhersagbar

Voraussetzung: results/sar_spots.csv (sar_lake.py stations) und data/arpa/samolaco_wind.csv.

Idee
  1. Satellit allein: Abendüberflug (ganzes Jahr) mit Wind auf dem oberen See ≥ X kn aus Süd = Breva-Abend.
     Für mehr Tage zusätzlich Samolaco, mit dem Satellitenfaktor auf den See umgerechnet
     (≥ 2 h am Stück ≥ X kn aus Süd, 11–20 Uhr).
  2. Wetter, wie es war (ERA5): Einstrahlung, Wolken, Temperaturgefälle Po-Ebene – Alpentäler,
     Druckgefälle Mailand – Chiavenna (thermisches Tief im Tal) und Zürich – Mailand (Nordföhn), Wind, Regen.
     Ein Modell mit diesen Größen zeigt, wie gut der Breva im besten Fall (perfekte Vorhersage) zu treffen ist.
  3. Dieselben Größen aus den Vorhersageläufen 1–7 Tage vorher: Trefferquote (AUC) nach Vorlauf.
"""
import argparse, json, os, ssl, sys, time, urllib.error, urllib.parse, urllib.request
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RES = os.path.join(ROOT, "results")
TZ = "Europe/Rome"

POINTS = {                      # lat, lon
    "milano": (45.46, 9.19),     # Po-Ebene
    "see": (46.07, 9.29),        # oberer See (Dervio/Bellano)
    "chiavenna": (46.32, 9.40),  # Tal im Norden (Breva-Ziel)
    "sondrio": (46.17, 9.87),    # Veltlin
    "zurich": (47.38, 8.54),     # Alpennordseite (Föhn-Index)
}
VARS = ["temperature_2m", "dew_point_2m", "pressure_msl", "shortwave_radiation", "cloud_cover",
        "precipitation", "wind_speed_10m", "wind_direction_10m"]
LEADS = range(1, 8)
MONTHS = list(range(1, 13))
SUED = (112, 202)               # Samolaco: Breva aus SSO–S


def _ctx():
    try:
        import certifi; return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def get_json(base, q, tries=6):
    url = base + "?" + urllib.parse.urlencode(q)
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=180, context=_ctx()) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="ignore")[:200]
            if e.code == 429 or "limit" in body.lower():
                wait = 60 * (i + 1); print(f"   Limit ({body.strip()}), warte {wait} s", flush=True); time.sleep(wait)
            elif e.code == 400:
                raise RuntimeError(body)
            else:
                print("  ", e.code, body); time.sleep(20 * (i + 1))
        except Exception as e:
            print("  ", e); time.sleep(20 * (i + 1))
    raise RuntimeError("keine Antwort: " + url)


# ---------------------------------------------------------------- Daten

def wetter(start=2014):
    out = os.path.join(DATA, "era5"); os.makedirs(out, exist_ok=True)
    yesterday = pd.Timestamp.today().normalize() - pd.Timedelta(days=1)
    for p, (la, lo) in POINTS.items():
        for y in range(start, yesterday.year + 1):
            f = f"{out}/{p}_{y}.csv"
            if os.path.exists(f) and y < yesterday.year:
                continue
            end = min(pd.Timestamp(f"{y}-12-31"), yesterday)
            j = get_json("https://archive-api.open-meteo.com/v1/archive",
                         dict(latitude=la, longitude=lo, models="era5", hourly=",".join(VARS), timezone=TZ,
                              wind_speed_unit="kn", start_date=f"{y}-01-01", end_date=end.strftime("%Y-%m-%d")))
            pd.DataFrame(j["hourly"]).to_csv(f, index=False)
            print(f"  ERA5 {p} {y}", flush=True); time.sleep(1)


def laeufe(model="ecmwf_ifs025", start="2024-01-01"):
    out = os.path.join(DATA, "prev"); os.makedirs(out, exist_ok=True)
    yesterday = pd.Timestamp.today().normalize() - pd.Timedelta(days=1)
    cols = [f"{v}_previous_day{d}" for v in VARS for d in LEADS] + VARS
    for p, (la, lo) in POINTS.items():
        for y in range(pd.Timestamp(start).year, yesterday.year + 1):
            f = f"{out}/{model}_{p}_{y}.csv"
            if os.path.exists(f) and y < yesterday.year:
                continue
            s = max(pd.Timestamp(start), pd.Timestamp(f"{y}-01-01")); e = min(pd.Timestamp(f"{y}-12-31"), yesterday)
            parts = []
            for i in range(0, len(cols), 14):                 # Anfrage in Stücken (Variablenzahl je Abfrage begrenzen)
                try:
                    j = get_json("https://previous-runs-api.open-meteo.com/v1/forecast",
                             dict(latitude=la, longitude=lo, models=model, hourly=",".join(cols[i:i + 14]),
                                  timezone=TZ, wind_speed_unit="kn",
                                  start_date=s.strftime("%Y-%m-%d"), end_date=e.strftime("%Y-%m-%d")))
                except RuntimeError as err:
                    print(f"  {model} {p} {y}: {err}"); continue
                parts.append(pd.DataFrame(j["hourly"]).set_index("time")); time.sleep(1)
            if not parts:
                continue
            pd.concat(parts, axis=1).reset_index().to_csv(f, index=False)
            print(f"  Läufe {model} {p} {y}", flush=True)


def load_hourly(kind, lead=0, model="ecmwf_ifs025"):
    """dict Punkt -> stündlicher DataFrame (Ortszeit) mit Spalten VARS. kind: era5 | prev."""
    import glob
    res = {}
    for p in POINTS:
        pat = f"{DATA}/era5/{p}_*.csv" if kind == "era5" else f"{DATA}/prev/{model}_{p}_*.csv"
        fs = sorted(glob.glob(pat))
        if not fs:
            continue
        d = pd.concat(pd.read_csv(f) for f in fs)
        d["time"] = pd.to_datetime(d.time); d = d.drop_duplicates("time").set_index("time").sort_index()
        if kind == "prev" and lead > 0:
            d = d[[f"{v}_previous_day{lead}" for v in VARS if f"{v}_previous_day{lead}" in d]]
            d.columns = [c.replace(f"_previous_day{lead}", "") for c in d.columns]
        else:
            d = d[[v for v in VARS if v in d]]
        res[p] = d
    return res


# ---------------------------------------------------------------- Merkmale je Tag

def features(H):
    """Tagesmerkmale (Ortszeit) aus stündlichen Punktdaten."""
    def win(p, v, h0, h1, how):
        x = H[p][v]; x = x[(x.index.hour >= h0) & (x.index.hour <= h1)]
        return getattr(x.groupby(x.index.normalize()), how)()
    def at(p, v, h):
        x = H[p][v]; x = x[x.index.hour == h]; x.index = x.index.normalize(); return x
    F = pd.DataFrame({
        "rad_see": win("see", "shortwave_radiation", 9, 17, "sum") / 1000,          # kWh/m² 9–17 Uhr
        "rad_milano": win("milano", "shortwave_radiation", 9, 17, "sum") / 1000,
        "rad_chiavenna": win("chiavenna", "shortwave_radiation", 9, 17, "sum") / 1000,
        "wolken_see": win("see", "cloud_cover", 9, 17, "mean"),
        "wolken_chiavenna": win("chiavenna", "cloud_cover", 9, 17, "mean"),
        "tmax_milano": win("milano", "temperature_2m", 12, 17, "max"),
        "tmax_chiavenna": win("chiavenna", "temperature_2m", 12, 17, "max"),
        "tmax_sondrio": win("sondrio", "temperature_2m", 12, 17, "max"),
        "tmin_milano": win("milano", "temperature_2m", 3, 8, "min"),
        "tmin_chiavenna": win("chiavenna", "temperature_2m", 3, 8, "min"),
        "regen_see": win("see", "precipitation", 11, 19, "sum"),
        "regen_chiavenna": win("chiavenna", "precipitation", 11, 19, "sum"),
        "dp_po_tal_15": at("milano", "pressure_msl", 15) - at("chiavenna", "pressure_msl", 15),
        "dp_po_tal_06": at("milano", "pressure_msl", 6) - at("chiavenna", "pressure_msl", 6),
        "dp_nord_sued_12": at("zurich", "pressure_msl", 12) - at("milano", "pressure_msl", 12),
        "dp_po_tal_18": at("milano", "pressure_msl", 18) - at("chiavenna", "pressure_msl", 18),
        "rad_spaet_see": win("see", "shortwave_radiation", 15, 18, "sum") / 1000,       # Sonne am späten Nachmittag
        "rad_spaet_chiavenna": win("chiavenna", "shortwave_radiation", 15, 18, "sum") / 1000,
        "wolken_spaet_see": win("see", "cloud_cover", 15, 19, "mean"),
        "wolken_morgen_see": win("see", "cloud_cover", 6, 11, "mean"),
        "t18_chiavenna_minus_milano": at("chiavenna", "temperature_2m", 18) - at("milano", "temperature_2m", 18),
        "taupunktdiff_milano": at("milano", "temperature_2m", 13) - at("milano", "dew_point_2m", 13),
        "wind_see_15": at("see", "wind_speed_10m", 15),
        "wind_milano_12": at("milano", "wind_speed_10m", 12),
        "wind_zurich_12": at("zurich", "wind_speed_10m", 12),
    })
    wd = at("see", "wind_direction_10m", 15)
    F["wind_see_15_sued"] = F.wind_see_15 * np.cos(np.radians(wd - 200))        # Komponente aus SSW (+) / NNO (−)
    F["dt_tal_po"] = F.tmax_chiavenna - F.tmax_milano
    F["amp_tal_minus_po"] = (F.tmax_chiavenna - F.tmin_chiavenna) - (F.tmax_milano - F.tmin_milano)
    F["dp_tag_minus_nacht"] = F.dp_po_tal_15 - F.dp_po_tal_06                  # thermisches Tief bildet sich tagsüber
    doy = F.index.dayofyear
    F["doy_sin"], F["doy_cos"] = np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25)
    F.index = pd.DatetimeIndex(F.index).tz_localize(None)
    return F


# ---------------------------------------------------------------- Ereignisse

def sat_factor(S):
    """See (19:15) / Samolaco-Nachmittagsmaximum bei Breva-Abenden. Bewusst gegen das Maximum und nicht gegen die
    Überflugstunde: in Samolaco ist der Breva um 19:15 oft schon abgeflaut, auf dem See nicht – der Faktor zur
    Überflugstunde (~2) würde die Breva-Tage stark überschätzen."""
    x = S[S.breva & (S.see >= 10) & (S.max_samolaco >= 5)]
    return float((x.see / x.max_samolaco).median()) if len(x) >= 10 else 1.0, len(x)


def load_sat():
    f = os.path.join(RES, "sar_spots.csv")
    if not os.path.exists(f):
        return None
    S = pd.read_csv(f, parse_dates=["time", "t_exakt"]).sort_values("t_exakt")
    S = S[S.t_exakt.diff().fillna(pd.Timedelta(hours=1)) > pd.Timedelta(minutes=5)]    # Kacheln desselben Überflugs
    up = [k for k in ("colico", "gera_lario", "sorico_punta", "domaso") if k in S]
    S["see"] = S[up].mean(axis=1)
    lt = S.t_exakt.dt.tz_convert(TZ)
    S["datum"] = lt.dt.tz_localize(None).dt.normalize()
    S["abend"] = (lt.dt.hour >= 12) & lt.dt.month.isin(MONTHS)
    rg = regen_abend()
    S["regen"] = S.datum.map(rg).fillna(0) if rg is not None else 0.0
    S["breva"] = S.abend & (S.dir == 200) & (S.regen < 0.5)          # ohne Regen/Gewitter am Abend
    return S


def samolaco_days(factor, thresholds=(10, 12, 14, 18)):
    x = pd.read_csv(os.path.join(DATA, "arpa", "samolaco_wind.csv"), parse_dates=["time"]).set_index("time")
    x.index = x.index.tz_convert(TZ)
    x = x[x.index.month.isin(MONTHS) & (x.index.hour >= 11) & (x.index.hour <= 20)]
    ok = (x.dir >= SUED[0]) & (x.dir <= SUED[1])
    see = x.kn * factor
    day = x.index.tz_localize(None).normalize()
    out = {"n_std": x.kn.groupby(day).count(), "max_see": see.where(ok).groupby(day).max()}
    for thr in thresholds:
        m = ((see >= thr) & ok).astype(int)
        grp = (m != m.shift()).cumsum()
        run = m.groupby([day, grp]).sum().groupby(level=0).max()
        out[f"breva{thr}"] = (run >= 2).astype(int)
    D = pd.DataFrame(out)
    return D[D.n_std >= 8]                       # genug Stunden am Tag


def regen_abend():
    """ERA5-Regen 17–19 Uhr (See + Chiavenna) je Tag: Regen und Gewitter hellen das Radarbild auf (falscher Starkwind)."""
    try:
        H = load_hourly("era5")
    except Exception:
        return None
    r = 0
    for p in ("see", "chiavenna"):
        x = H[p]["precipitation"]; x = x[(x.index.hour >= 17) & (x.index.hour <= 19)]
        r = r + x.groupby(x.index.normalize()).sum()
    r.index = pd.DatetimeIndex(r.index).tz_localize(None)
    return r


def ereignisse(thr=12):
    S = load_sat()
    if S is None:
        sys.exit("results/sar_spots.csv fehlt – erst sar_lake.py stations laufen lassen")
    f, n = sat_factor(S)
    print(f"Satellitenfaktor See/Samolaco (Breva-Abende, See ≥ 10 kn, n={n}): {f:.2f}")
    A = S[S.abend].copy()
    A["sat_breva"] = (A.breva & (A.see >= thr)).astype(int)
    A["sat_ruhig"] = ((A.see < 6) | (A.dir == 20)).astype(int)
    print(f"Abendüberflüge ganzes Jahr: {len(A)}, Breva ≥ {thr} kn: {A.sat_breva.sum()}, ruhig/Nord: {A.sat_ruhig.sum()}, "
          f"mit Regen am Abend (ausgeschlossen): {int((A.regen >= 0.5).sum())}")
    for t in (10, 12, 14, 18):
        print(f"   See ≥ {t:2d} kn aus Süd: {int((A.breva & (A.see >= t)).sum())} Abende")
    D = samolaco_days(f)
    j = A.set_index("datum").join(D, how="left")
    both = j.dropna(subset=[f"breva{thr}"])
    if len(both):
        tp = int(((both.sat_breva == 1) & (both[f"breva{thr}"] == 1)).sum())
        print(f"Abgleich mit Samolaco×{f:.2f}: von {int(both.sat_breva.sum())} Satelliten-Breva-Abenden zeigt Samolaco {tp} "
              f"auch (≥2 h); an {int(((both.sat_breva == 0) & (both[f'breva{thr}'] == 1)).sum())} Abenden nur Samolaco.")
    os.makedirs(RES, exist_ok=True)
    A.drop(columns=[c for c in A if c.startswith("max_") or c == "file"], errors="ignore").to_csv(f"{RES}/breva_sat_abende.csv", index=False)
    D.to_csv(f"{RES}/breva_samolaco_tage.csv")
    print("\nBreva-Tage je Jahr (Samolaco × Faktor, ≥ 2 h am Stück aus Süd):")
    yrs = D.index.year.nunique()
    print("  " + ", ".join(f"≥ {t} kn: {D[f'breva{t}'].sum() / yrs:.1f}" for t in (10, 12, 14, 18)))
    print(f"\ngeschrieben: results/breva_sat_abende.csv, results/breva_samolaco_tage.csv")


# ---------------------------------------------------------------- Analyse

def _xgb():
    from xgboost import XGBClassifier
    return XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                         min_child_weight=3, eval_metric="logloss", verbosity=0)


def loyo_auc(X, y):
    from sklearn.metrics import roc_auc_score
    p = pd.Series(np.nan, index=X.index)
    for yr in sorted(set(X.index.year)):
        te = X.index.year == yr
        if y[~te].nunique() < 2:
            continue
        m = _xgb().fit(X[~te], y[~te]); p[te] = m.predict_proba(X[te])[:, 1]
    ok = p.notna()
    return roc_auc_score(y[ok], p[ok]) if y[ok].nunique() == 2 else np.nan, p


def analyse(thr=12):
    from sklearn.metrics import roc_auc_score
    F = features(load_hourly("era5"))
    F = F[F.index.month.isin(MONTHS)]
    S = load_sat(); f, _ = sat_factor(S) if S is not None else (1.0, 0)
    D = samolaco_days(f)
    lines = []
    p = lambda s="": (print(s), lines.append(s))
    for name, lab in (("Satellit", None), ("Samolaco", f"breva{thr}")):
        if name == "Satellit":
            if S is None:
                continue
            A = S[S.abend].set_index("datum")
            y = (A.breva & (A.see >= thr)).astype(int); y = y[~y.index.duplicated()]
        else:
            y = D[lab]
        X = F.reindex(y.index).dropna(thresh=len(F.columns) - 3)
        y = y.reindex(X.index)
        p(f"\n=== {name}: Breva ≥ {thr} kn auf dem See, {int(y.sum())} von {len(y)} Tagen (ERA5 = Wetter, wie es war) ===")
        rows = []
        for c in X.columns:
            if c.startswith("doy"):
                continue
            ok = X[c].notna()
            a = roc_auc_score(y[ok], X[c][ok]) if y[ok].nunique() == 2 else np.nan
            rows.append(dict(merkmal=c, breva=X[c][y == 1].median(), kein_breva=X[c][y == 0].median(),
                             auc=a, trennkraft=abs(a - 0.5) * 2))
        T = pd.DataFrame(rows).sort_values("trennkraft", ascending=False).round(2)
        p(T.to_string(index=False))
        a, _ = loyo_auc(X, y)
        p(f"Modell mit allen Merkmalen (XGBoost, je Jahr ausgelassen): AUC {a:.2f}  – Obergrenze bei perfekter Vorhersage")
    p("\nauc > 0,5: höher an Breva-Tagen; < 0,5: niedriger. trennkraft 0 = nutzlos, 1 = trennt perfekt.")
    open(f"{RES}/breva_merkmale.txt", "w").write("\n".join(lines) + "\n")


def lang(thr=14, calm=10, day_thr=10):
    """Langer Breva: an Tagen mit Breva (Samolaco-Nachmittagsmax ≥ day_thr kn) – weht er um 19:15 noch auf dem See?
    lang = Seewind beim Abendüberflug ≥ thr, kurz = < calm. Welche Wettergrößen unterscheiden die beiden?"""
    from sklearn.metrics import roc_auc_score
    S = load_sat()
    if S is None:
        sys.exit("results/sar_spots.csv fehlt")
    A = S[S.breva].drop_duplicates("datum").set_index("datum")
    A = A[A.max_samolaco >= day_thr]
    A = A[(A.see >= thr) | (A.see < calm)]
    y = (A.see >= thr).astype(int)
    F = features(load_hourly("era5"))
    X = F.reindex(y.index).dropna(thresh=len(F.columns) - 3); y = y.reindex(X.index)
    lines = []
    p = lambda s="": (print(s), lines.append(s))
    p(f"Breva-Tage (Samolaco ≥ {day_thr} kn nachmittags) mit Abendüberflug: {len(y)} – "
      f"um 19:15 noch ≥ {thr} kn auf dem See: {int(y.sum())} (lang), < {calm} kn: {int((y == 0).sum())} (kurz)")
    if y.nunique() < 2 or len(y) < 15:
        p("zu wenige Fälle"); return
    st = A.reindex(X.index)
    p(f"Samolaco: Nachmittagsmax lang {st.max_samolaco[y == 1].median():.1f} / kurz {st.max_samolaco[y == 0].median():.1f} kn, "
      f"zur Überflugstunde lang {st.st_samolaco[y == 1].median():.1f} / kurz {st.st_samolaco[y == 0].median():.1f} kn")
    rows = []
    for c in X.columns:
        if c.startswith("doy"):
            continue
        ok = X[c].notna()
        a = roc_auc_score(y[ok], X[c][ok])
        rows.append(dict(merkmal=c, lang=X[c][y == 1].median(), kurz=X[c][y == 0].median(), auc=a, trennkraft=abs(a - .5) * 2))
    T = pd.DataFrame(rows).sort_values("trennkraft", ascending=False).round(2)
    p(T.to_string(index=False))
    mon = pd.crosstab(X.index.month, y).rename(columns={0: "kurz", 1: "lang"})
    # stetig: Rangkorrelation jeder Größe mit dem Seewind um 19:15 an allen Breva-Tagen (braucht keine Klassen)
    Aall = S[S.breva].drop_duplicates("datum").set_index("datum")
    Aall = Aall[Aall.max_samolaco >= day_thr]
    Xa = F.reindex(Aall.index).dropna(thresh=len(F.columns) - 3)
    sp = Xa.drop(columns=["doy_sin", "doy_cos"]).corrwith(Aall.see.reindex(Xa.index), method="spearman")
    p(f"\nRangkorrelation mit dem Seewind um 19:15 an {len(Xa)} Breva-Tagen (+ = mehr Abendwind):")
    p(sp.reindex(sp.abs().sort_values(ascending=False).index).round(2).head(12).to_string())
    p("\nnach Monat:\n" + mon.to_string())
    if len(y) >= 40:
        a, _ = loyo_auc(X, y); p(f"Modell (XGBoost, je Jahr ausgelassen): AUC {a:.2f}")
    open(f"{RES}/breva_lang.txt", "w").write("\n".join(lines) + "\n")


def vorlauf(thr=(12, 14), model="ecmwf_ifs025", train_until=2023):
    """Modell an ERA5 + Samolaco bis train_until, getestet ab train_until+1 mit Vorhersagen 0–7 Tage vorher."""
    from sklearn.metrics import roc_auc_score, brier_score_loss
    S = load_sat(); f, _ = sat_factor(S) if S is not None else (1.0, 0)
    D = samolaco_days(f)
    FE = features(load_hourly("era5")); FE = FE[FE.index.month.isin(MONTHS)]
    sat = None
    if S is not None:
        A = S[S.abend].set_index("datum"); sat = A[~A.index.duplicated()]
    rows = []
    for t in thr:
        y = D[f"breva{t}"]
        tr = FE.index.year <= train_until
        Xtr = FE[tr].reindex(y.index.intersection(FE[tr].index)); ytr = y.reindex(Xtr.index)
        m = _xgb().fit(Xtr, ytr)
        tests = [("ERA5 (perfekt)", FE[~tr])]
        for L in [0] + list(LEADS):
            H = load_hourly("prev", L, model)
            if not H:
                break
            Fp = features(H); Fp = Fp[Fp.index.month.isin(MONTHS) & (Fp.index.year > train_until)]
            tests.append((f"{L} Tage vorher" if L else "Analyse (Tag 0)", Fp))
        for name, X in tests:
            X = X[Xtr.columns].dropna(thresh=len(Xtr.columns) - 3)
            yy = y.reindex(X.index).dropna(); X = X.loc[yy.index]
            if yy.nunique() < 2:
                continue
            pr = m.predict_proba(X)[:, 1]
            r = dict(schwelle=f"≥{t}", vorlauf=name, tage=len(yy), breva=int(yy.sum()),
                     auc=round(roc_auc_score(yy, pr), 2), brier=round(brier_score_loss(yy, pr), 3))
            if sat is not None:                           # Gegenprobe an Satelliten-Abenden
                s = sat.reindex(X.index).dropna(subset=["see"])
                ys = (s.breva & (s.see >= t)).astype(int)
                if ys.nunique() == 2:
                    r["auc_satellit"] = round(roc_auc_score(ys, m.predict_proba(X.loc[s.index])[:, 1]), 2)
                    r["sat_abende"] = len(s)
            rows.append(r)
    R = pd.DataFrame(rows)
    print(f"Modell an ERA5 bis {train_until}, getestet {train_until + 1}–heute mit {model}-Vorhersagen:")
    print(R.to_string(index=False))
    print("\nauc: 1 = perfekt, 0,5 = Zufall. Brier: kleiner ist besser. auc_satellit: gegen Breva-Abende im Satellitenbild.")
    R.to_csv(f"{RES}/breva_vorlauf.csv", index=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["wetter", "laeufe", "ereignisse", "analyse", "lang", "vorlauf"])
    ap.add_argument("--schwelle", type=float, default=None)
    ap.add_argument("--modell", default="ecmwf_ifs025")
    a = ap.parse_args()
    if a.step == "wetter":
        wetter()
    elif a.step == "laeufe":
        laeufe(a.modell)
    elif a.step == "ereignisse":
        ereignisse(a.schwelle or 12)
    elif a.step == "analyse":
        analyse(a.schwelle or 12)
    elif a.step == "lang":
        lang(a.schwelle or 14)
    else:
        vorlauf(model=a.modell)
