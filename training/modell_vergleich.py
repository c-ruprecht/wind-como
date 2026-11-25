"""Welches Wettermodell liefert die besten Eingangsgrößen für die 7-Tage-Breva-Vorhersage?

Bisher: Modell an ERA5 trainiert, mit ECMWF IFS 0.25° (previous runs) geeicht und live mit ECMWF gefüttert.
Hier werden alle Modelle der Open-Meteo Previous-Runs-API verglichen, die den Comer See abdecken – global (7 Tage)
und hochaufgelöst-regional (2–5 Tage).

Schritte (der Reihe nach):
  python training/modell_vergleich.py pruefen
      fragt je Modell ab: gültige Kennung, ab wann archiviert, wie viele Tage voraus (wenige Abrufe)
  python training/modell_vergleich.py laden --modelle icon_seamless,meteoswiss_icon_ch2
      lädt nur die 8 Größen an den 11 Punkten, die das App-Modell braucht, für die Vorlauftage --leads.
      Bricht beim Tageslimit sauber ab; am nächsten Tag einfach erneut starten (fertige Jahre werden übersprungen).
  python training/modell_vergleich.py vergleich
      a) Merkmale: wie gut trifft jedes Modell die 37 Merkmale (gegen ERA5, gewichtet mit der Wichtigkeit)
      b) Ergebnis: AUC der Breva-Vorhersage je Modell und Vorlauf auf denselben Tagen, mit und ohne
         Quantil-Angleichung an ERA5; Bootstrap-Bereich der Differenz zu ECMWF IFS 0.25°
      c) Kombinationen: Mittel mehrerer Modelle; je Merkmal das beste Modell
      -> results/modellvergleich.md, results/modellvergleich.csv

Wichtig zur Einordnung: Die „Wahrheit“ in a) ist ERA5 (31 km). Ein feines Regionalmodell kann näher an der
Wirklichkeit und trotzdem weiter von ERA5 weg liegen. Entscheidend ist deshalb b) – trifft der Breva-Tag ein?
"""
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402
import train_breva as T  # noqa: E402
from breva_events import _ctx  # noqa: E402

RES = B.RES
# Kennung -> (Bezeichnung, Vorlauf laut Anbieter in Tagen, Auflösung)
CANDIDATES = {
    "ecmwf_ifs025":                ("ECMWF IFS 0.25° (bisher)", 7, "25 km"),
    "ecmwf_ifs":                   ("ECMWF IFS HRES", 7, "9 km"),
    "ecmwf_aifs025_single":        ("ECMWF AIFS (KI)", 7, "25 km"),
    "icon_seamless":               ("DWD ICON Seamless", 7, "2–11 km"),
    "icon_global":                 ("DWD ICON Global", 7, "11 km"),
    "icon_eu":                     ("DWD ICON-EU", 5, "7 km"),
    "icon_d2":                     ("DWD ICON-D2", 2, "2 km"),
    "meteoswiss_icon_ch2":         ("MeteoSwiss ICON-CH2", 5, "2 km"),
    "meteoswiss_icon_ch1":         ("MeteoSwiss ICON-CH1", 2, "1 km"),
    "italia_meteo_arpae_icon_2i":  ("ItaliaMeteo ICON-2I", 3, "2 km"),
    "meteofrance_seamless":        ("Météo-France Seamless", 4, "1–25 km"),
    "meteofrance_arome_france_hd": ("Météo-France AROME HD", 2, "1.5 km"),
    "ukmo_seamless":               ("UK Met Office Seamless", 7, "10 km"),
    "gfs_seamless":                ("NOAA GFS Seamless", 7, "13–25 km"),
    "gem_seamless":                ("GEM Canada Seamless", 7, "15 km"),
    "jma_seamless":                ("JMA Seamless", 7, "55 km"),
    "cma_grapes_global":           ("CMA GRAPES", 7, "15 km"),
}
REF = "ecmwf_ifs025"
AVAIL = os.path.join(RES, "modelle_verfuegbar.csv")


class Tageslimit(Exception):
    pass


def fetch(q):
    url = B.PREV_URL + "?" + urllib.parse.urlencode(q)
    for i in range(4):
        try:
            with urllib.request.urlopen(url, timeout=180, context=_ctx()) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="ignore")[:300]
            if "daily" in body.lower():
                raise Tageslimit(body)
            if e.code == 429 or "limit" in body.lower():
                time.sleep(65 * (i + 1)); continue
            if e.code == 400:
                raise ValueError(body)
            time.sleep(15 * (i + 1))
        except (TimeoutError, urllib.error.URLError) as e:
            print("  ", e); time.sleep(15 * (i + 1))
    raise RuntimeError("keine Antwort")


# ------------------------------------------------------------------ 1. Verfügbarkeit

def has_data(model, day, leads=range(1, 8)):
    cols = [f"temperature_2m_previous_day{L}" for L in leads]
    j = fetch(dict(latitude=46.07, longitude=9.29, models=model, hourly=",".join(cols),
                   start_date=day, end_date=day))
    return {L: any(x is not None for x in j["hourly"].get(c, [])) for L, c in zip(leads, cols)}


def pruefen():
    rows = []
    recent = (pd.Timestamp.today().normalize() - pd.Timedelta(days=3)).strftime("%Y-%m-%d")
    months = pd.date_range("2024-01-01", pd.Timestamp.today(), freq="MS")
    for m, (name, hor, res) in CANDIDATES.items():
        try:
            h = has_data(m, recent)
        except ValueError as e:
            print(f"{m:30s} unbekannt/abgelehnt: {str(e)[:80]}"); rows.append(dict(modell=m, name=name, ok=False)); continue
        except Tageslimit:
            sys.exit("Tageslimit erreicht – morgen erneut.")
        leads = [L for L, v in h.items() if v]
        if not leads:
            print(f"{m:30s} keine Daten am See"); rows.append(dict(modell=m, name=name, ok=False)); continue
        # Archivbeginn: binäre Suche über Monate (Vorlauf 1)
        lo, hi = 0, len(months) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if has_data(m, (months[mid] + pd.Timedelta(days=14)).strftime("%Y-%m-%d"), [min(leads)])[min(leads)]:
                hi = mid
            else:
                lo = mid + 1
            time.sleep(0.3)
        start = months[lo].strftime("%Y-%m-%d")
        rows.append(dict(modell=m, name=name, ok=True, aufloesung=res, max_vorlauf=max(leads), ab=start))
        print(f"{m:30s} ok  Vorlauf 1–{max(leads)}  ab {start}  ({name}, {res})", flush=True)
    pd.DataFrame(rows).to_csv(AVAIL, index=False)
    print("geschrieben:", AVAIL)


# ------------------------------------------------------------------ 2. Laden

def needed():
    """Nur was das App-Modell braucht: BASIC an den 6 Regionalpunkten, Druck+Temperatur an den 5 Fernpunkten."""
    return {p: [v for v in vs if v in B.BASIC] for p, (la, lo, vs) in B.POINTS.items()}


def laden(modelle, leads, start):
    A = pd.read_csv(AVAIL).set_index("modell") if os.path.exists(AVAIL) else None
    os.makedirs(B.PREV, exist_ok=True)
    yesterday = pd.Timestamp.today().normalize() - pd.Timedelta(days=1)
    for m in modelle:
        if A is not None and m in A.index and not A.loc[m, "ok"]:
            print(f"{m}: laut pruefen nicht verfügbar – übersprungen"); continue
        s0 = pd.Timestamp(start)
        L = list(leads)
        if A is not None and m in A.index:
            s0 = max(s0, pd.Timestamp(A.loc[m, "ab"])); L = [x for x in L if x <= A.loc[m, "max_vorlauf"]]
        cost = 0
        for p, vs in needed().items():
            ncol = len(vs) * len(L)
            for y in range(s0.year, yesterday.year + 1):
                days = (min(pd.Timestamp(f"{y}-12-31"), yesterday) - max(s0, pd.Timestamp(f"{y}-01-01"))).days + 1
                cost += sum(max(1, min(14, ncol - i) / 10) * max(1, days / 14) for i in range(0, ncol, 14))
        print(f"{m}: Vorlauf {L}, ab {s0.date()}, etwa {cost:.0f} gewichtete Abrufe (Tageslimit 10 000)", flush=True)
        try:
            for p, vs in needed().items():
                la, lo, _ = B.POINTS[p]
                cols = [f"{v}_previous_day{d}" for v in vs for d in L]
                for y in range(s0.year, yesterday.year + 1):
                    f = f"{B.PREV}/{m}_{p}_{y}.csv"
                    if os.path.exists(f) and y < yesterday.year:
                        have = set(pd.read_csv(f, nrows=1).columns)
                        if all(c in have for c in cols):
                            continue
                    s = max(s0, pd.Timestamp(f"{y}-01-01")); e = min(pd.Timestamp(f"{y}-12-31"), yesterday)
                    parts = []
                    for i in range(0, len(cols), 14):
                        j = fetch(dict(latitude=la, longitude=lo, models=m, hourly=",".join(cols[i:i + 14]),
                                       timezone=B.TZ, wind_speed_unit="kn",
                                       start_date=s.strftime("%Y-%m-%d"), end_date=e.strftime("%Y-%m-%d")))
                        parts.append(pd.DataFrame(j["hourly"]).set_index("time")); time.sleep(0.4)
                    pd.concat(parts, axis=1).reset_index().to_csv(f, index=False)
                    print(f"  {m} {p} {y}", flush=True)
        except Tageslimit:
            sys.exit("Tageslimit erreicht – morgen denselben Befehl erneut starten, Fertiges bleibt.")


# ------------------------------------------------------------------ 3. Vergleich

def auc(y, p):
    from sklearn.metrics import roc_auc_score
    y = np.asarray(y); p = np.asarray(p)
    return roc_auc_score(y, p) if len(set(y)) == 2 else np.nan


def qmap(X, E, years):
    """Quantil-Angleichung je Merkmal an ERA5, über Jahre kreuzangepasst (kein Blick auf das Testjahr)."""
    out = X.copy()
    qs = np.linspace(0.01, 0.99, 50)
    for c in X.columns:
        if c.startswith("doy_"):
            continue
        for y in np.unique(years):
            tr = (years != y) & X[c].notna().values & E[c].notna().values
            te = years == y
            if tr.sum() < 60:
                continue
            xq = np.nanquantile(X.loc[tr, c], qs); eq = np.nanquantile(E.loc[tr, c], qs)
            xq, idx = np.unique(xq, return_index=True)
            if len(xq) < 5:
                continue
            out.loc[te, c] = np.interp(X.loc[te, c], xq, eq[idx])
    return out


def block_boot(y, pa, pb, days, n=1000, seed=0):
    """Differenz AUC(a) − AUC(b), Bootstrap über ganze Wochen (benachbarte Tage hängen zusammen)."""
    rng = np.random.default_rng(seed)
    wk = pd.Index(days).to_period("W").astype(str).values
    groups = {w: np.where(wk == w)[0] for w in np.unique(wk)}; keys = list(groups)
    d = []
    for _ in range(n):
        i = np.concatenate([groups[k] for k in rng.choice(keys, len(keys))])
        if len(set(y[i])) == 2:
            d.append(auc(y[i], pa[i]) - auc(y[i], pb[i]))
    return np.percentile(d, [5, 95])


def vergleich(thr_list=(14, 18), train_until=2023):
    D = pd.read_csv(f"{RES}/breva_tage.csv", index_col=0, parse_dates=True)
    F = T.FEATS
    E = B.features(B.load("era5")).reindex(D.index).reindex(columns=F)
    test = D.index[D.index.year > train_until]
    import glob
    models = sorted({os.path.basename(f).split("_milano_")[0] for f in glob.glob(f"{B.PREV}/*_milano_*.csv")})
    print("Modelle mit Daten:", models)
    X = {}
    for m in models:
        for L in B.LEADS:
            H = B.load("prev", L, m)
            if not H or not any(len(h.columns) for h in H.values()):
                continue
            fx = B.features(H).reindex(test).reindex(columns=F)
            ok = fx.notna().mean(axis=1) > 0.7
            if ok.sum() > 60:
                X[(m, L)] = fx[ok]
    if not X:
        sys.exit("keine Läufe – erst laden")
    lines = ["# Wettermodelle als Eingang für die 7-Tage-Breva-Vorhersage\n",
             f"Modell an ERA5 bis {train_until} trainiert (Ziel {T.OPT['ziel']}), getestet ab {train_until + 1} "
             "mit den echten, archivierten Vorhersagen jedes Modells. Vergleich je Vorlauf nur auf den Tagen, "
             "die alle Modelle dieses Vorlaufs haben.\n"]
    rows = []
    for thr in thr_list:
        y_all = T.target(D, thr)
        tr = D.index.year <= train_until
        okE = E.notna().mean(axis=1) > 0.7
        mdl = T.xgb_model(F).fit(E[tr & okE], y_all[tr & okE])
        gain = pd.Series(mdl.get_booster().get_score(importance_type="gain")).reindex(F).fillna(0)
        gain = gain / gain.sum()
        for L in B.LEADS:
            ms = [m for m in models if (m, L) in X]
            if not ms:
                continue
            # gemeinsame Tage: Referenz zuerst, dann Modelle nach Archivlänge, solange ≥ 150 Tage bleiben
            ms.sort(key=lambda m: (m != REF, -len(X[(m, L)])))
            common = X[(ms[0], L)].index; keep = [ms[0]]
            for m in ms[1:]:
                c2 = common.intersection(X[(m, L)].index)
                if len(c2) >= 150:
                    common, keep = c2, keep + [m]
                else:
                    print(f"  Vorlauf {L}: {m} zu kurz überlappend ({len(c2)} Tage) – hier weggelassen")
            ms = keep
            common = common[E.loc[common].notna().mean(axis=1) > 0.7]
            y = y_all.loc[common].values; yrs = common.year.values
            season = common.month.isin(range(3, 11))
            Ec = E.loc[common]
            P = {}
            for m in ms:
                Xm = X[(m, L)].loc[common]
                Xq = qmap(Xm, Ec, yrs)
                r = Xm.corrwith(Ec)                      # Merkmal-Treue gegen ERA5
                nmae = (Xm - Ec).abs().mean() / Ec.std()
                p = mdl.predict_proba(Xm)[:, 1]; pq = mdl.predict_proba(Xq)[:, 1]
                P[m] = p; P[m + "|q"] = pq
                rows.append(dict(schwelle=thr, vorlauf=L, modell=m, tage=len(common), breva=int(y.sum()),
                                 merkmal_r=round((r.fillna(0) * gain).sum(), 3),
                                 merkmal_nmae=round((nmae.fillna(1) * gain).sum(), 3),
                                 auc=round(auc(y, p), 3), auc_saison=round(auc(y[season], p[season]), 3),
                                 auc_angeglichen=round(auc(y, pq), 3),
                                 **{f"r_{c}": round(r.get(c, np.nan), 3) for c in F}))
            # Kombinationen
            if len(ms) > 1:
                for tag, keys in (("Mittel aller", ms), ("Mittel aller, angeglichen", [m + "|q" for m in ms])):
                    pm = np.mean([P[k] for k in keys], axis=0); P[tag] = pm
                    rows.append(dict(schwelle=thr, vorlauf=L, modell=tag, tage=len(common), breva=int(y.sum()),
                                     auc=round(auc(y, pm), 3), auc_saison=round(auc(y[season], pm[season]), 3)))
                # je Merkmal das beste Modell, gewählt im ersten Jahr, bewertet danach
                y0 = yrs.min(); sel = yrs == y0
                best = {c: max(ms, key=lambda m: np.nan_to_num(X[(m, L)].loc[common[sel], c].corr(Ec.loc[sel, c]), nan=-1))
                        for c in F}
                mix = pd.DataFrame({c: X[(best[c], L)].loc[common, c] for c in F})
                pmix = mdl.predict_proba(mix)[:, 1]; after = ~sel
                rows.append(dict(schwelle=thr, vorlauf=L, modell=f"je Merkmal bestes (gewählt {y0}, bewertet danach)",
                                 tage=int(after.sum()), breva=int(y[after].sum()),
                                 auc=round(auc(y[after], pmix[after]), 3),
                                 auc_saison=round(auc(y[after & season], pmix[after & season]), 3),
                                 ref_auc_gleiche_tage=round(auc(y[after], P[ms[0]][after]), 3) if REF not in ms
                                 else round(auc(y[after], P[REF][after]), 3)))
                if thr == thr_list[0] and L in (1, 3):
                    lines.append(f"\n**Bestes Modell je Merkmal, Vorlauf {L} (gewählt {y0}):** " +
                                 ", ".join(f"{c} → {best[c]}" for c in gain.sort_values(ascending=False).index[:12]))
            if REF in ms:
                for k in [m for m in ms if m != REF] + [m + "|q" for m in ms] + ["Mittel aller"]:
                    if k in P:
                        lo_, hi_ = block_boot(y, P[k], P[REF], common)
                        rows.append(dict(schwelle=thr, vorlauf=L, modell=f"Δ {k} − {REF}", tage=len(common),
                                         auc=round(auc(y, P[k]) - auc(y, P[REF]), 3),
                                         bereich_90=f"{lo_:+.3f} … {hi_:+.3f}"))
    R = pd.DataFrame(rows)
    R.to_csv(f"{RES}/modellvergleich.csv", index=False)
    base = ["schwelle", "vorlauf", "modell", "tage", "breva", "merkmal_r", "merkmal_nmae", "auc", "auc_saison",
            "auc_angeglichen", "ref_auc_gleiche_tage", "bereich_90"]
    for thr in thr_list:
        S = R[(R.schwelle == thr) & ~R.modell.str.startswith("Δ")][[c for c in base if c in R]]
        lines += [f"\n## ≥ {thr} kn\n", "merkmal_r: Übereinstimmung der Merkmale mit ERA5 (Korrelation, gewichtet mit "
                  "der Wichtigkeit im Modell); auc_angeglichen: Merkmale vorher per Quantil-Angleichung auf "
                  "ERA5-Verteilung gebracht.\n", "```", S.to_string(index=False), "```"]
        Dl = R[(R.schwelle == thr) & R.modell.str.startswith("Δ")][["vorlauf", "modell", "tage", "auc", "bereich_90"]]
        if len(Dl):
            lines += [f"\nUnterschied zu {REF} (Bootstrap über Wochen, 90 %-Bereich; schließt er 0 aus, "
                      "ist der Unterschied belastbar):\n", "```", Dl.to_string(index=False), "```"]
    open(f"{RES}/modellvergleich.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\ngeschrieben: results/modellvergleich.md, results/modellvergleich.csv")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["pruefen", "laden", "vergleich"])
    ap.add_argument("--modelle", default="icon_seamless,meteoswiss_icon_ch2,ecmwf_aifs025_single,ukmo_seamless,gfs_seamless")
    ap.add_argument("--leads", default="1,2,3,5,7")
    ap.add_argument("--start", default="2024-01-01")
    a = ap.parse_args()
    if a.step == "pruefen":
        pruefen()
    elif a.step == "laden":
        laden(a.modelle.split(","), [int(x) for x in a.leads.split(",")], a.start)
    else:
        vergleich()
