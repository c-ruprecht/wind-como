"""Sauberer Breva-Datensatz und Faktoren, die einen echten Breva vorhersagen.

  python training/breva_daten.py wetter      # ERA5 an 11 Punkten (See, Täler, Po-Ebene, Alpen, Großwetterlage), 2014 – gestern
  python training/breva_daten.py laeufe      # ECMWF-Läufe 1–7 Tage vorher an denselben Punkten, 2024 – gestern
  python training/breva_daten.py tage        # Tagesklassen Apr–Sep: Breva / schwach / ruhig / Regen-Gewitter / Nordföhn / synoptisch
  python training/breva_daten.py faktoren    # was macht einen Breva-Tag (nur Schönwettertage) + Modell auf allen Tagen
  python training/breva_daten.py vorlauf     # Trefferquote nach Vorlauf 1–7 Tage

Bereinigung (Schritt tage)
  Ein Breva ist thermisch: morgens ruhig, ab Mittag Wind aus Süd, gleichmäßig (kleiner Böenfaktor), kein Regen,
  kein Nordföhn. Tage, die das nicht erfüllen, bekommen eine eigene Klasse und verfälschen die Faktoren nicht.
  Stärke auf dem See: Samolaco × Satellitenfaktor (Abendüberflüge), Gegenprobe mit dem Satellitenbild, wo es eins gibt.

Wettergrößen (Schritt faktoren), alles aus Modellen, die es auch als Vorhersage gibt
  Thermik     Einstrahlung, Sonnenstunden, Wolken (gesamt/tief/morgens), Grenzschichthöhe, Bodenfeuchte
  Gefälle     Temperatur und Druck Po-Ebene (Mailand, Bergamo) – Täler (Chiavenna, Sondrio) – Engadin (1800 m)
  Großlage    Druckgefälle Zürich–Mailand, München–Genua (Föhn), Lyon–Venedig; geostrophischer Wind aus 7 Punkten;
              Drucktendenz 24 h (Front im Anmarsch)
  Labilität   CAPE (Gewitter), Regen am Vortag
  See         Ersatz für die Wassertemperatur: 30-Tage-Mittel der Lufttemperatur am See (der See hinkt der Luft
              hinterher) und Unterschied Tageshöchstwert – 30-Tage-Mittel
  Schnee      Schneehöhe Engadin (kalte Hochlagen im Frühjahr)
"""
import argparse, json, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from breva_events import get_json, _xgb, loyo_auc  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RES = os.path.join(ROOT, "results")
TZ = "Europe/Rome"
MONTHS = [4, 5, 6, 7, 8, 9]
ERA = os.path.join(DATA, "era5v2")
PREV = os.path.join(DATA, "prevv2")
LEADS = range(1, 8)

BASIC = ["temperature_2m", "dew_point_2m", "pressure_msl", "shortwave_radiation", "cloud_cover",
         "precipitation", "wind_speed_10m", "wind_direction_10m"]
EXTRA = ["cloud_cover_low", "sunshine_duration", "boundary_layer_height", "cape", "soil_moisture_0_to_7cm"]
SYN = ["pressure_msl", "temperature_2m"]
POINTS = {
    "milano":    (45.46, 9.19, BASIC + EXTRA),
    "bergamo":   (45.70, 9.67, BASIC),
    "see":       (46.07, 9.29, BASIC + EXTRA),
    "chiavenna": (46.32, 9.40, BASIC + EXTRA),
    "sondrio":   (46.17, 9.87, BASIC),
    "engadin":   (46.50, 9.84, BASIC + ["snow_depth"]),
    "zurich":    (47.38, 8.54, SYN),
    "muenchen":  (48.14, 11.58, SYN),
    "genova":    (44.41, 8.93, SYN),
    "venezia":   (45.44, 12.33, SYN),
    "lyon":      (45.76, 4.84, SYN),
}
SYN_POINTS = ["lyon", "zurich", "muenchen", "genova", "venezia", "milano", "bergamo"]   # für den geostrophischen Wind

ERA_URL = "https://archive-api.open-meteo.com/v1/archive"
PREV_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"


# ---------------------------------------------------------------- Daten holen

def supported(kind, model, cand, suffix=""):
    """Welche Variablen liefert die Quelle? (einmal geprüft, gespeichert)"""
    out = ERA if kind == "era5" else PREV
    os.makedirs(out, exist_ok=True)
    f = os.path.join(out, f"supported_{model}.json")
    have = json.load(open(f)) if os.path.exists(f) else {}
    url = ERA_URL if kind == "era5" else PREV_URL
    day = "2024-06-01"
    for v in cand:
        if v in have:
            continue
        try:
            j = get_json(url, dict(latitude=46.07, longitude=9.29, models=model, hourly=v + suffix,
                                   start_date=day, end_date=day), tries=2)
            vals = j["hourly"][v + suffix]
            have[v] = any(x is not None for x in vals)
        except Exception:
            have[v] = False
        json.dump(have, open(f, "w"), indent=1)
    return [v for v in cand if have.get(v)]


def wetter(start=2014):
    allv = sorted({v for *_, vs in POINTS.values() for v in vs})
    ok = set(supported("era5", "era5", allv))
    print("ERA5 liefert nicht:", sorted(set(allv) - ok) or "–")
    yesterday = pd.Timestamp.today().normalize() - pd.Timedelta(days=1)
    for p, (la, lo, vs) in POINTS.items():
        vs = [v for v in vs if v in ok]
        for y in range(start, yesterday.year + 1):
            f = f"{ERA}/{p}_{y}.csv"
            if os.path.exists(f) and y < yesterday.year:
                continue
            end = min(pd.Timestamp(f"{y}-12-31"), yesterday)
            j = get_json(ERA_URL, dict(latitude=la, longitude=lo, models="era5", hourly=",".join(vs), timezone=TZ,
                                       wind_speed_unit="kn", start_date=f"{y}-01-01", end_date=end.strftime("%Y-%m-%d")))
            pd.DataFrame(j["hourly"]).to_csv(f, index=False)
            print(f"  ERA5 {p} {y}", flush=True); time.sleep(0.5)


def laeufe(model="ecmwf_ifs025", start="2024-01-01"):
    allv = sorted({v for *_, vs in POINTS.values() for v in vs})
    ok = set(supported("prev", model, allv, suffix="_previous_day1"))
    print(f"{model}-Läufe liefern nicht:", sorted(set(allv) - ok) or "–")
    yesterday = pd.Timestamp.today().normalize() - pd.Timedelta(days=1)
    for p, (la, lo, vs) in POINTS.items():
        cols = [f"{v}_previous_day{d}" for v in vs if v in ok for d in LEADS]
        for y in range(pd.Timestamp(start).year, yesterday.year + 1):
            f = f"{PREV}/{model}_{p}_{y}.csv"
            if os.path.exists(f) and y < yesterday.year:
                continue
            s = max(pd.Timestamp(start), pd.Timestamp(f"{y}-01-01")); e = min(pd.Timestamp(f"{y}-12-31"), yesterday)
            parts = []
            for i in range(0, len(cols), 14):
                try:
                    j = get_json(PREV_URL, dict(latitude=la, longitude=lo, models=model, hourly=",".join(cols[i:i + 14]),
                                                timezone=TZ, wind_speed_unit="kn",
                                                start_date=s.strftime("%Y-%m-%d"), end_date=e.strftime("%Y-%m-%d")))
                except RuntimeError as err:
                    print(f"  {p} {y}: {err}"); continue
                parts.append(pd.DataFrame(j["hourly"]).set_index("time")); time.sleep(0.5)
            if parts:
                pd.concat(parts, axis=1).reset_index().to_csv(f, index=False)
                print(f"  Läufe {model} {p} {y}", flush=True)


def load(kind="era5", lead=0, model="ecmwf_ifs025"):
    import glob
    H = {}
    for p in POINTS:
        fs = sorted(glob.glob(f"{ERA}/{p}_*.csv" if kind == "era5" else f"{PREV}/{model}_{p}_*.csv"))
        if not fs:
            continue
        d = pd.concat(pd.read_csv(f) for f in fs)
        d["time"] = pd.to_datetime(d.time); d = d.drop_duplicates("time").set_index("time").sort_index()
        if kind == "prev":
            suf = f"_previous_day{lead}"
            d = d[[c for c in d if c.endswith(suf)]]; d.columns = [c[:-len(suf)] for c in d.columns]
        H[p] = d
    return H


# ---------------------------------------------------------------- Merkmale

def features(H):
    idx = None

    def ser(p, v):
        return H[p][v] if p in H and v in H[p] else None

    def win(p, v, h0, h1, how):
        x = ser(p, v)
        if x is None:
            return np.nan
        x = x[(x.index.hour >= h0) & (x.index.hour <= h1)]
        return getattr(x.groupby(x.index.normalize()), how)()

    def at(p, v, h):
        x = ser(p, v)
        if x is None:
            return np.nan
        x = x[x.index.hour == h]; x.index = x.index.normalize(); return x

    F = pd.DataFrame({
        # Thermik
        "rad_see": win("see", "shortwave_radiation", 9, 17, "sum") / 1000,
        "rad_chiavenna": win("chiavenna", "shortwave_radiation", 9, 17, "sum") / 1000,
        "rad_milano": win("milano", "shortwave_radiation", 9, 17, "sum") / 1000,
        "rad_spaet_chiavenna": win("chiavenna", "shortwave_radiation", 15, 18, "sum") / 1000,
        "sonne_see_h": win("see", "sunshine_duration", 9, 17, "sum") / 3600,
        "wolken_see": win("see", "cloud_cover", 9, 17, "mean"),
        "wolken_tief_see": win("see", "cloud_cover_low", 9, 17, "mean"),
        "wolken_morgen_see": win("see", "cloud_cover", 6, 11, "mean"),
        "wolken_chiavenna": win("chiavenna", "cloud_cover", 9, 17, "mean"),
        "grenzschicht_milano": win("milano", "boundary_layer_height", 12, 17, "max"),
        "grenzschicht_chiavenna": win("chiavenna", "boundary_layer_height", 12, 17, "max"),
        "bodenfeuchte_milano": win("milano", "soil_moisture_0_to_7cm", 0, 23, "mean"),
        "bodenfeuchte_chiavenna": win("chiavenna", "soil_moisture_0_to_7cm", 0, 23, "mean"),
        # Temperaturen
        "tmax_milano": win("milano", "temperature_2m", 12, 17, "max"),
        "tmax_bergamo": win("bergamo", "temperature_2m", 12, 17, "max"),
        "tmax_chiavenna": win("chiavenna", "temperature_2m", 12, 17, "max"),
        "tmax_sondrio": win("sondrio", "temperature_2m", 12, 17, "max"),
        "tmax_engadin": win("engadin", "temperature_2m", 12, 17, "max"),
        "tmin_milano": win("milano", "temperature_2m", 3, 8, "min"),
        "tmin_chiavenna": win("chiavenna", "temperature_2m", 3, 8, "min"),
        "tmean_see": win("see", "temperature_2m", 0, 23, "mean"),
        "tmax_see": win("see", "temperature_2m", 12, 17, "max"),
        "taupunktdiff_milano": at("milano", "temperature_2m", 13) - at("milano", "dew_point_2m", 13),
        # Druck
        "dp_po_tal_06": at("milano", "pressure_msl", 6) - at("chiavenna", "pressure_msl", 6),
        "dp_po_tal_15": at("milano", "pressure_msl", 15) - at("chiavenna", "pressure_msl", 15),
        "dp_po_tal_18": at("milano", "pressure_msl", 18) - at("chiavenna", "pressure_msl", 18),
        "dp_bergamo_sondrio_15": at("bergamo", "pressure_msl", 15) - at("sondrio", "pressure_msl", 15),
        "dp_zurich_milano_12": at("zurich", "pressure_msl", 12) - at("milano", "pressure_msl", 12),
        "dp_muenchen_genova_12": at("muenchen", "pressure_msl", 12) - at("genova", "pressure_msl", 12),
        "dp_lyon_venezia_12": at("lyon", "pressure_msl", 12) - at("venezia", "pressure_msl", 12),
        "p_milano_12": at("milano", "pressure_msl", 12),
        # Labilität, Regen, Schnee, Wind
        "cape_max": win("milano", "cape", 12, 19, "max"),
        "cape_see": win("see", "cape", 12, 19, "max"),
        "regen_see": win("see", "precipitation", 11, 19, "sum"),
        "regen_chiavenna": win("chiavenna", "precipitation", 11, 19, "sum"),
        "schnee_engadin": win("engadin", "snow_depth", 0, 23, "mean"),
        "wind_see_15": at("see", "wind_speed_10m", 15),
        "wind_milano_12": at("milano", "wind_speed_10m", 12),
    })
    wd = at("see", "wind_direction_10m", 15)
    F["wind_see_15_sued"] = F.wind_see_15 * np.cos(np.radians(wd - 200))
    F["dt_tal_po"] = F.tmax_chiavenna - F.tmax_milano
    F["dt_engadin_po"] = F.tmax_engadin - F.tmax_milano                      # Erwärmung der Hochalpen gegen die Ebene
    F["amp_tal_minus_po"] = (F.tmax_chiavenna - F.tmin_chiavenna) - (F.tmax_milano - F.tmin_milano)
    F["dp_tag_minus_nacht"] = F.dp_po_tal_15 - F.dp_po_tal_06
    F["drucktendenz_24h"] = F.p_milano_12.diff()
    F["regen_vortag"] = (F.regen_see + F.regen_chiavenna).shift(1)
    F["see_t30"] = F.tmean_see.rolling(30, min_periods=20).mean()          # Ersatz Wassertemperatur
    F["luft_minus_see_t30"] = F.tmax_see - F.see_t30                         # warme Luft über kühlem See
    # geostrophischer Wind: Ebene durch den Druck an 7 Punkten (Gradient in hPa/100 km)
    pts = [p for p in SYN_POINTS if p in H and "pressure_msl" in H[p]]
    if len(pts) >= 4:
        P = pd.concat([at(p, "pressure_msl", 12).rename(p) for p in pts], axis=1)
        lat0 = np.mean([POINTS[p][0] for p in pts])
        xy = np.array([[(POINTS[p][1] - 9.2) * 111.2 * np.cos(np.radians(lat0)) / 100, (POINTS[p][0] - lat0) * 111.2 / 100]
                       for p in pts])
        A = np.c_[np.ones(len(pts)), xy]
        ok = P.notna().all(axis=1)
        coef = np.full((len(P), 3), np.nan)
        coef[ok.values] = np.linalg.lstsq(A, P[ok].values.T, rcond=None)[0].T
        gx, gy = coef[:, 1], coef[:, 2]                                       # hPa/100 km nach Ost / Nord
        F.loc[P.index, "geo_staerke"] = np.hypot(gx, gy)
        # geostrophischer Wind (Nordhalbkugel, tiefer Druck links): nach Nord ∝ +gx, nach Ost ∝ −gy
        F.loc[P.index, "geo_aus_sued"] = gx                                   # >0: Strömung aus Süd (Druck im Osten höher)
        F.loc[P.index, "geo_aus_west"] = -gy                                  # >0: Strömung aus West (Druck im Norden tiefer)
    doy = F.index.dayofyear
    F["doy_sin"], F["doy_cos"] = np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25)
    F.index = pd.DatetimeIndex(F.index).tz_localize(None)
    return F.drop(columns=["p_milano_12", "tmean_see"])


# ---------------------------------------------------------------- Tagesklassen

def station(st):
    x = pd.read_csv(os.path.join(DATA, "arpa", f"{st}_wind.csv"), parse_dates=["time"]).set_index("time")
    x.index = x.index.tz_convert(TZ).tz_localize(None)
    return x


def run2(mask, day):
    m = mask.astype(int); g = (m != m.shift()).cumsum()
    return m.groupby([day, g]).sum().groupby(level=0).max()


def sat_evenings():
    f = os.path.join(RES, "sar_spots.csv")
    if not os.path.exists(f):
        return None
    S = pd.read_csv(f, parse_dates=["t_exakt"]).sort_values("t_exakt")
    S = S[S.t_exakt.diff().fillna(pd.Timedelta(hours=1)) > pd.Timedelta(minutes=5)]
    lt = S.t_exakt.dt.tz_convert(TZ)
    S = S[(lt.dt.hour >= 12)].copy()
    S["datum"] = lt[S.index].dt.tz_localize(None).dt.normalize()
    up = [k for k in ("colico", "gera_lario", "sorico_punta", "domaso") if k in S]
    S["sat_see"] = S[up].mean(axis=1)
    S["sat_mitte"] = S[[k for k in ("dervio", "cremia") if k in S]].mean(axis=1)
    return S.drop_duplicates("datum").set_index("datum")[["sat_see", "sat_mitte", "dir"]]


def tage():
    F = features(load("era5"))
    sam = station("samolaco"); col = station("colico")
    day = sam.index.normalize()
    hh = sam.index.hour
    sued = (sam.dir >= 112) & (sam.dir <= 202)
    nord = (sam.dir >= 315) | (sam.dir <= 45)
    nm = (hh >= 11) & (hh <= 20)
    D = pd.DataFrame({
        "sam_morgen": sam.kn[(hh >= 6) & (hh <= 10)].groupby(day[(hh >= 6) & (hh <= 10)]).mean(),
        "sam_max": sam.kn[nm].groupby(day[nm]).max(),
        "sam_sued_anteil": sued[nm & (sam.kn >= 5)].groupby(day[nm & (sam.kn >= 5)]).mean(),
        "sam_boe": (sam.gust_kn / sam.kn.clip(lower=3))[nm & (sam.kn >= 5)].groupby(day[nm & (sam.kn >= 5)]).median(),
        "sam_nord_std": (nord & (sam.kn >= 8))[nm].groupby(day[nm]).sum(),
        "sam_std": sam.kn[nm].groupby(day[nm]).count(),
    })
    cd = col.index.normalize(); ch = col.index.hour; cn = (ch >= 11) & (ch <= 20)
    D["col_max"] = col.kn[cn].groupby(cd[cn]).max()
    D = D[D.index.month.isin(MONTHS) & (D.sam_std >= 8)]
    # Satellitenfaktor: See am Abend / Samolaco-Nachmittagsmax an sauberen Breva-Abenden
    S = sat_evenings()
    D = D.join(S, how="left")
    W = F.reindex(D.index)
    regen = (W.regen_see.fillna(0) + W.regen_chiavenna.fillna(0))
    clean_eve = (D.dir == 200) & (regen < 1) & (D.sam_morgen < 6) & (D.sat_see >= 10) & (D.sam_max >= 5)
    f = float((D.sat_see / D.sam_max)[clean_eve].median()) if clean_eve.sum() >= 15 else 1.5
    print(f"Satellitenfaktor See/Samolaco-Max (saubere Breva-Abende, n={int(clean_eve.sum())}): {f:.2f}")
    # Stärke auf dem See: Samolaco × f, ≥ 2 h am Stück aus Süd
    sx = sam[nm & sam.index.month.isin(MONTHS)]
    sd = sx.index.normalize(); ss = (sx.dir >= 112) & (sx.dir <= 202)
    for thr in (10, 12, 14, 18):
        D[f"breva{thr}"] = (run2((sx.kn * f >= thr) & ss, sd).reindex(D.index) >= 2).astype(int)
    D["see_max_est"] = D.sam_max * f
    D["regen"] = regen
    D["cape"] = W.cape_max
    # Klassen
    k = np.full(len(D), "ruhig", dtype=object)
    thermisch = np.ones(len(D), bool)
    gew = (D.regen >= 1).values
    foehn = ((D.sam_nord_std >= 2) | (W.dp_zurich_milano_12 >= 4)).values
    syn = (D.sam_morgen >= 6).values | ((D.sam_boe >= 2.3) & (D.sam_max >= 10)).values
    k[D.breva10.values == 1] = "Breva schwach"
    k[D.breva14.values == 1] = "Breva"
    k[syn] = "synoptisch"; k[foehn] = "Nordföhn"; k[gew] = "Regen/Gewitter"
    D["klasse"] = k
    # Gegenprobe Satellit (wo Abendüberflug)
    has = D.sat_see.notna()
    D["sat_widerspruch"] = ""
    D.loc[has & (D.klasse == "Breva") & (D.sat_see < 6), "sat_widerspruch"] = "Satellit ruhig"
    D.loc[has & (D.klasse == "ruhig") & (D.sat_see >= 14) & (D.dir == 200), "sat_widerspruch"] = "Satellit Breva"
    D["sauber"] = D.klasse.isin(["Breva", "Breva schwach", "ruhig"]) & (D.sat_widerspruch == "")
    os.makedirs(RES, exist_ok=True)
    D.round(2).to_csv(f"{RES}/breva_tage.csv")
    yrs = D.index.year.nunique()
    print(f"\n{len(D)} Tage Apr–Sep {D.index.year.min()}–{D.index.year.max()}, je Saison:")
    print((D.klasse.value_counts() / yrs).round(1).to_string())
    print(f"\nBreva ≥ 18 kn (sauber) je Saison: {((D.breva18 == 1) & D.sauber).sum() / yrs:.1f}")
    print(f"Widerspruch zum Satellitenbild: {(D.sat_widerspruch != '').sum()} von {has.sum()} Tagen mit Abendüberflug")
    print(D[D.sat_widerspruch != ""][["klasse", "sam_morgen", "sam_max", "see_max_est", "sat_see", "regen", "sat_widerspruch"]]
          .round(1).to_string())
    if has.any():
        print("\nSatellit am Abend je Klasse (Median Seewind kn, Anzahl):")
        print(D[has].groupby("klasse").sat_see.agg(["median", "count"]).round(1).to_string())
    print(f"\ngeschrieben: results/breva_tage.csv")


# ---------------------------------------------------------------- Faktoren

def shap_importance(m, X):
    import xgboost as xgb
    c = m.get_booster().predict(xgb.DMatrix(X), pred_contribs=True)[:, :-1]
    return pd.Series(np.abs(c).mean(axis=0), index=X.columns).sort_values(ascending=False)


def faktoren(thr=14):
    from sklearn.metrics import roc_auc_score
    D = pd.read_csv(f"{RES}/breva_tage.csv", index_col=0, parse_dates=True)
    F = features(load("era5"))
    X = F.reindex(D.index)
    lines = []
    p = lambda s="": (print(s), lines.append(s))
    y_all = D[f"breva{thr}"].where(D.klasse.isin(["Breva", "Breva schwach", "ruhig"]), 0).astype(int)
    for name, m in (("Schönwettertage (Breva / schwach / ruhig, ohne Widerspruch)", D.sauber),
                    ("alle Tage (Störungen zählen als kein Breva)", D.index == D.index)):
        y = (D[f"breva{thr}"] if "Schön" in name else y_all)[m]
        Xm = X[m]
        p(f"\n=== {name}: Breva ≥ {thr} kn, {int(y.sum())} von {len(y)} Tagen ===")
        if "Schön" in name:
            rows = []
            for c in Xm.columns:
                if c.startswith("doy"):
                    continue
                ok = Xm[c].notna()
                if ok.sum() < 50 or y[ok].nunique() < 2:
                    continue
                a = roc_auc_score(y[ok], Xm[c][ok])
                rows.append(dict(merkmal=c, breva=Xm[c][ok & (y == 1)].median(), kein=Xm[c][ok & (y == 0)].median(),
                                 auc=a, trennkraft=abs(a - .5) * 2))
            p(pd.DataFrame(rows).sort_values("trennkraft", ascending=False).round(2).to_string(index=False))
        a, _ = loyo_auc(Xm, y)
        mdl = _xgb().fit(Xm, y)
        imp = shap_importance(mdl, Xm)
        p(f"Modell (XGBoost, je Jahr ausgelassen): AUC {a:.3f}")
        p("wichtigste Größen im Modell (mittlerer |SHAP|-Beitrag):")
        p((imp / imp.sum() * 100).round(1).head(15).to_string())
    # Klassen nach Monat
    p("\nKlassen je Monat (Tage je Saison):")
    p((pd.crosstab(D.index.month, D.klasse) / D.index.year.nunique()).round(1).to_string())
    open(f"{RES}/breva_faktoren_{thr}.txt", "w").write("\n".join(lines) + "\n")


def vorlauf(thr=(14, 18), model="ecmwf_ifs025", train_until=2023):
    from sklearn.metrics import roc_auc_score, brier_score_loss
    D = pd.read_csv(f"{RES}/breva_tage.csv", index_col=0, parse_dates=True)
    FE = features(load("era5")).reindex(D.index)
    leads = {L: features(load("prev", L, model)).reindex(D.index) for L in LEADS}
    if not any(len(v.dropna(how="all")) for v in leads.values()):
        sys.exit("keine Läufe – erst: python training/breva_daten.py laeufe")
    test_days = D.index[D.index.year > train_until]
    cols = [c for c in FE.columns if leads[1].loc[test_days, c].notna().mean() > 0.5]
    print(f"{len(cols)} von {len(FE.columns)} Größen auch in den {model}-Läufen; fehlend:",
          sorted(set(FE.columns) - set(cols)))
    rows = []
    for t in thr:
        y = D[f"breva{t}"].where(D.klasse.isin(["Breva", "Breva schwach", "ruhig"]), 0).astype(int)
        tr = D.index.year <= train_until
        m = _xgb().fit(FE.loc[tr, cols], y[tr])
        for name, X in [("ERA5 (perfekt)", FE)] + [(f"{L} Tage vorher", leads[L]) for L in LEADS]:
            Xt = X.loc[test_days, cols]; ok = Xt.notna().mean(axis=1) > 0.7
            yy = y[test_days][ok]; pr = m.predict_proba(Xt[ok])[:, 1]
            if yy.nunique() < 2:
                continue
            rows.append(dict(schwelle=f"≥{t}", vorlauf=name, tage=len(yy), breva=int(yy.sum()),
                             auc=round(roc_auc_score(yy, pr), 3), brier=round(brier_score_loss(yy, pr), 3)))
    R = pd.DataFrame(rows)
    print(f"Modell an ERA5 bis {train_until}, getestet {train_until + 1}–heute mit {model}-Vorhersagen:")
    print(R.to_string(index=False))
    R.to_csv(f"{RES}/breva_vorlauf_v2.csv", index=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["wetter", "laeufe", "tage", "faktoren", "vorlauf"])
    ap.add_argument("--schwelle", type=int, default=14)
    ap.add_argument("--modell", default="ecmwf_ifs025")
    a = ap.parse_args()
    {"wetter": wetter, "laeufe": lambda: laeufe(a.modell), "tage": tage,
     "faktoren": lambda: faktoren(a.schwelle), "vorlauf": lambda: vorlauf(model=a.modell)}[a.step]()
