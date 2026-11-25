"""Ausführliche Analyse des Breva-Modells: Leckage, Verfeinerung, Verkleinerung, lokales Wissen.

  python training/model_analyse.py            # alles, Bericht nach results/modell_analyse.md
  python training/model_analyse.py --schnell  # weniger Varianten (zum Ausprobieren)

Prüfprotokoll (überall gleich, damit die Zahlen vergleichbar sind)
  Training: ERA5 2014–2023.  Prüfung: 2024–heute mit den echten ECMWF-Läufen 1, 3 und 5 Tage vorher,
  einmal über das ganze Jahr und einmal nur März–Oktober („Saison“). Dazu eine unabhängige Gegenprobe:
  Abende mit Satellitenbild (Seewind ≥ 14 kn aus Süd) – die hängen nicht an Samolaco und nicht an ERA5.

1. Leckage – sagt das Modell vorher oder „kennt“ es die Antwort?
   a) Zielgröße: die Störtage (Regen) sind aus ERA5-Regen bestimmt, und ERA5-Regen ist ein Merkmal.
      Vergleich mit einer Zielgröße nur aus Stationen.
   b) Verschiebung: Merkmale vom Vortag statt vom Zieltag – fällt die AUC nicht, lernt das Modell Jahreszeit/Persistenz.
   c) Zufällige statt jahresweise Aufteilung – großer Unterschied heißt: benachbarte Tage verraten sich gegenseitig.
   d) ERA5 gegen Vorhersage je Merkmal: Merkmale, die nur in ERA5 trennen (z. B. weil ERA5 Messungen enthält),
      tragen in der echten Vorhersage nicht.
   e) Satellit als unabhängige Wahrheit.
   f) Heute-Modell: Stationsmessung um 13 Uhr liegt im Zeitfenster des Ziels (11–20 Uhr) – Vergleich mit dem Satelliten.
2. Verfeinerung – Hyperparameter, logistische Regression als Vergleich.
3. Verkleinerung – wie viele Merkmale braucht es für dieselbe Trefferquote?
4. Lokales Wissen – feste Wirkungsrichtungen (monoton), Jahreszeit als Vorwissen, entsaisonalisierte Temperaturen,
   physikalische Kombinationen, Gewichtung der Saison.
"""
import argparse, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402
import train_breva as T  # noqa: E402

TEST_LEADS = [1, 3, 5]
# Wirkungsrichtung aus Physik und Prüfung (+1: mehr -> mehr Breva, -1: mehr -> weniger Breva)
MONO = {"wind_see_15_sued": 1, "taupunktdiff_milano": 1, "dp_po_tal_15": 1, "dp_po_tal_18": 1,
        "dp_bergamo_sondrio_15": 1, "dp_tag_minus_nacht": 1, "dp_zurich_milano_12": -1, "regen_see": -1,
        "regen_chiavenna": -1, "regen_vortag": -1, "rad_chiavenna": 1, "rad_spaet_chiavenna": 1, "rad_see": 1,
        "wolken_see": -1, "wolken_chiavenna": -1, "wolken_morgen_see": -1}


def xgb(**kw):
    from xgboost import XGBClassifier
    p = dict(n_estimators=250, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
             min_child_weight=5, eval_metric="logloss", verbosity=0)
    p.update(kw)
    return XGBClassifier(**p)


def auc(y, p):
    from sklearn.metrics import roc_auc_score
    y, p = np.asarray(y), np.asarray(p)
    ok = np.isfinite(p)
    return round(roc_auc_score(y[ok], p[ok]), 3) if len(set(y[ok])) == 2 else np.nan


class Daten:
    def __init__(self):
        self.D = pd.read_csv(f"{B.RES}/breva_tage.csv", index_col=0, parse_dates=True)
        D = self.D
        self.FE = B.features(B.load("era5")).reindex(D.index)
        self.L = {}
        for L in TEST_LEADS:
            F = B.features(B.load("prev", L, T.MODEL)).reindex(D.index)
            self.L[L] = F
        sch = D.klasse.isin(["Breva", "Breva schwach", "ruhig"])
        self.y = {
            # A: wie in der App (Störtage aus Stationen UND ERA5-Regen/Föhnindex)
            "A": D.breva14.where(sch, 0).astype(int),
            # B: nur aus Stationen – Breva ≥ 14, morgens ruhig, kein Nordwind in Samolaco
            "B": ((D.breva14 == 1) & (D.sam_morgen < 6) & (D.sam_nord_std < 2)).astype(int),
            "A18": D.breva18.where(sch, 0).astype(int),
        }
        self.train = D.index.year <= T.TRAIN_UNTIL
        self.test = ~self.train
        self.saison = (D.index.month >= 3) & (D.index.month <= 10)
        sat = D.sat_see.notna() & self.test
        self.sat_idx = D.index[sat]
        self.y_sat = ((D.sat_see >= 14) & (D.dir == 200)).astype(int)[sat]

    def X(self, F, feats):
        X = F.reindex(columns=feats)
        return X

    def evaluate(self, fit_predict, feats, ylab="A", transform=None):
        """fit_predict(Xtr, ytr, Xte_dict) -> {key: p}; gibt Kennzahlen zurück."""
        y = self.y[ylab]
        Xtr = self.X(self.FE, feats)
        if transform:
            Xtr = transform(Xtr)
        ok = self.train & (Xtr.notna().mean(axis=1) > 0.7)
        tests = {}
        for L in TEST_LEADS:
            Xt = self.X(self.L[L], feats)
            if transform:
                Xt = transform(Xt)
            tests[L] = Xt[self.test]
        preds = fit_predict(Xtr[ok], y[ok], tests)
        r = {}
        for L in TEST_LEADS:
            p = pd.Series(preds[L], index=tests[L].index)
            yy = y[self.test]
            r[f"auc_{L}"] = auc(yy, p)
            r[f"saison_{L}"] = auc(yy[self.saison[self.test]], p[self.saison[self.test]])
        p1 = pd.Series(preds[1], index=tests[1].index)
        r["satellit_1"] = auc(self.y_sat, p1.reindex(self.sat_idx))
        return r


def fp_xgb(**kw):
    def f(Xtr, ytr, tests):
        m = xgb(**kw).fit(Xtr, ytr)
        return {L: m.predict_proba(X)[:, 1] for L, X in tests.items()}
    return f


def fp_logreg(Xtr, ytr, tests):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.impute import SimpleImputer
    m = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(C=0.3, max_iter=2000))
    m.fit(Xtr, ytr)
    return {L: m.predict_proba(X)[:, 1] for L, X in tests.items()}


def fp_mono(feats, **kw):
    cons = "(" + ",".join(str(MONO.get(f, 0)) for f in feats) + ")"
    return fp_xgb(monotone_constraints=cons, **kw)


def fp_prior(D, **kw):
    """Jahreszeit als Vorwissen: Startwert je Tag = Logit der Breva-Häufigkeit im Monat (Trainingsjahre)."""
    def f(Xtr, ytr, tests):
        clim = ytr.groupby(ytr.index.month).mean().clip(0.005, 0.995)
        bm = lambda idx: np.log(clim.reindex(idx.month).values / (1 - clim.reindex(idx.month).values))
        m = xgb(**kw)
        m.fit(Xtr, ytr, base_margin=bm(Xtr.index))
        import xgboost as xg
        out = {}
        for L, X in tests.items():
            dm = xg.DMatrix(X, base_margin=bm(X.index))
            out[L] = m.get_booster().predict(dm)
        return out
    return f


def fp_weighted(w_off=0.3, **kw):
    def f(Xtr, ytr, tests):
        w = np.where((Xtr.index.month >= 3) & (Xtr.index.month <= 10), 1.0, w_off)
        m = xgb(**kw).fit(Xtr, ytr, sample_weight=w)
        return {L: m.predict_proba(X)[:, 1] for L, X in tests.items()}
    return f


def deseason(cols, clim_src):
    """Abweichung vom mittleren Jahresgang (Tag des Jahres, 31 Tage geglättet), Klima aus den Trainingsjahren (ERA5)."""
    clim = {}
    for c in cols:
        s = clim_src[c]
        g = s.groupby(s.index.day_of_year).mean().reindex(range(1, 367))
        g = pd.concat([g.iloc[-15:], g, g.iloc[:15]]).rolling(31, center=True, min_periods=5).mean().iloc[15:-15]
        clim[c] = g

    def tr(X):
        X = X.copy()
        for c in cols:
            if c in X:
                X[c + "_anom"] = X[c] - clim[c].reindex(X.index.day_of_year).values
        return X
    return tr


def engineered(X):
    X = X.copy()
    X["thermik"] = X.rad_chiavenna * (X.dp_bergamo_sondrio_15 + 3).clip(lower=0)          # Sonne × Sog ins Tal
    X["foehn_flag"] = (X.dp_zurich_milano_12 >= 3).astype(float)
    X["regen_tag"] = X.regen_see.fillna(0) + X.regen_chiavenna.fillna(0)
    X["gefaelle_mittel"] = X[["dp_po_tal_15", "dp_bergamo_sondrio_15"]].mean(axis=1)
    X["heiss_ebene"] = (X.tmax_bergamo - 28).clip(lower=0)                                  # Hitze dämpft
    return X


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schnell", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    S = Daten()
    F = list(T.FEATS)
    out = []
    p = lambda s="": (print(s, flush=True), out.append(s))
    fmt = lambda rows: "```\n" + pd.DataFrame(rows).to_string(index=False) + "\n```"
    p(f"# Analyse Breva-Modell (≥ 14 kn)\n\nTraining ERA5 2014–{T.TRAIN_UNTIL}, Prüfung {T.TRAIN_UNTIL + 1}–heute mit ECMWF-Läufen "
      f"{TEST_LEADS} Tage vorher. Breva-Tage im Test: {int(S.y['A'][S.test].sum())} von {int(S.test.sum())}, "
      f"Satellitenabende im Test: {len(S.sat_idx)} (davon Breva {int(S.y_sat.sum())}).\n")
    base = S.evaluate(fp_xgb(), F)

    # ---------------- 1. Leckage
    p("## 1. Leckage\n")
    rows = [dict(test="Basis (Ziel A, wie App)", **base)]
    rows.append(dict(test="a) Ziel B: nur Stationen (ohne ERA5-Regen)", **S.evaluate(fp_xgb(), F, "B")))
    noregen = [f for f in F if not f.startswith("regen")]
    rows.append(dict(test="a) Ziel A ohne Regen-Merkmale", **S.evaluate(fp_xgb(), noregen)))
    shift = lambda X: X.shift(1, freq="D").reindex(X.index)
    rows.append(dict(test="b) Merkmale vom Vortag", **S.evaluate(fp_xgb(), F, transform=shift)))
    only_season = ["doy_sin", "doy_cos"]
    rows.append(dict(test="b) nur Jahreszeit (doy)", **S.evaluate(fp_xgb(), only_season)))
    p(fmt(rows))
    # c) zufällige gegen jahresweise Aufteilung (ERA5, Trainingsjahre)
    from sklearn.model_selection import KFold
    X = S.FE[F][S.train]; y = S.y["A"][S.train]; okk = X.notna().mean(axis=1) > 0.7; X, y = X[okk], y[okk]
    pr_rand, pr_year = pd.Series(np.nan, index=X.index), pd.Series(np.nan, index=X.index)
    for tr, te in KFold(5, shuffle=True, random_state=1).split(X):
        pr_rand.iloc[te] = xgb().fit(X.iloc[tr], y.iloc[tr]).predict_proba(X.iloc[te])[:, 1]
    for yr in sorted(set(X.index.year)):
        te = X.index.year == yr
        pr_year[te] = xgb().fit(X[~te], y[~te]).predict_proba(X[te])[:, 1]
    p(f"\nc) Kreuzvalidierung ERA5 2014–{T.TRAIN_UNTIL}: zufällige Aufteilung AUC {auc(y, pr_rand)}, "
      f"jahresweise {auc(y, pr_year)}  (großer Abstand = benachbarte Tage verraten sich)\n")
    # d) Merkmal einzeln: ERA5 gegen Vorhersage (Saison, Testjahre)
    rows = []
    yt = S.y["A"][S.test & S.saison]
    for c in F:
        if c.startswith("doy"):
            continue
        ae = auc(yt, S.FE.loc[yt.index, c]); af = auc(yt, S.L[1].loc[yt.index, c]) if c in S.L[1] else np.nan
        if np.isfinite(ae):
            rows.append(dict(merkmal=c, auc_era5=ae, auc_vorhersage_1=af, abstand=round(abs(ae - 0.5) - abs((af if np.isfinite(af) else 0.5) - 0.5), 3)))
    R = pd.DataFrame(rows).sort_values("abstand", ascending=False)
    p("d) Merkmale, die nur in ERA5 trennen (Saison, Testjahre; abstand > 0,1 verdächtig):")
    p(fmt(R.head(12)))
    # f) Heute: Station im Zielfenster
    try:
        import train_heute as TH
        O = TH.hourly_obs()
        ob = TH.obs_features(O, S.D.index, 13)
        rows = []
        for c in ["samolaco_jetzt", "vercana_jetzt", "colico_jetzt", "morbegno_jetzt"]:
            rows.append(dict(merkmal=c + " (13 Uhr)", auc_ziel_A=auc(S.y["A"][S.saison], ob.loc[S.saison, c]),
                             auc_satellit=auc(((S.D.sat_see >= 14) & (S.D.dir == 200)).astype(int)[S.D.sat_see.notna()],
                                              ob.loc[S.D.sat_see.notna(), c])))
        p("\nf) Heute-Modell: Stationen um 13 Uhr gegen Ziel A (Samolaco 11–20 Uhr) und gegen den Satelliten:")
        p(fmt(rows))
        p("   Liegt Samolaco gegen Ziel A deutlich höher als gegen den Satelliten, ist das Überlappung, keine Vorhersage.")
    except Exception as e:
        p(f"\nf) übersprungen: {e}")

    # ---------------- 2. Verfeinerung
    p("\n## 2. Verfeinerung\n")
    rows = [dict(modell="XGB Basis (250 Bäume, Tiefe 3)", **base),
            dict(modell="Logistische Regression", **S.evaluate(fp_logreg, F))]
    grid = [dict(max_depth=2, n_estimators=400), dict(max_depth=4, n_estimators=200), dict(max_depth=3, n_estimators=600, learning_rate=0.02),
            dict(max_depth=3, min_child_weight=15), dict(max_depth=2, n_estimators=800, learning_rate=0.02, min_child_weight=10),
            dict(max_depth=5, n_estimators=150, min_child_weight=10)]
    if a.schnell:
        grid = grid[:2]
    for g in grid:
        rows.append(dict(modell="XGB " + ", ".join(f"{k}={v}" for k, v in g.items()), **S.evaluate(fp_xgb(**g), F)))
    p(fmt(rows))

    # ---------------- 3. Verkleinerung
    p("\n## 3. Verkleinerung\n")
    import xgboost as xg
    Xa = S.FE[F][S.train]; ya = S.y["A"][S.train]; ok = Xa.notna().mean(axis=1) > 0.7
    m = xgb().fit(Xa[ok], ya[ok])
    contrib = m.get_booster().predict(xg.DMatrix(Xa[ok]), pred_contribs=True)[:, :-1]
    rank = pd.Series(np.abs(contrib).mean(axis=0), index=F).sort_values(ascending=False)
    p("Rangfolge (mittlerer |SHAP|): " + ", ".join(f"{k} {v:.2f}" for k, v in rank.head(15).items()))
    rows = []
    for k in ([len(F), 25, 20, 15, 12, 10, 8, 6, 5, 4, 3] if not a.schnell else [len(F), 12, 6, 3]):
        fs = list(rank.index[:k])
        rows.append(dict(merkmale=k, **S.evaluate(fp_xgb(), fs)))
    R = pd.DataFrame(rows)
    p(fmt(R))
    best = R.saison_1.max()
    small = R[R.saison_1 >= best - 0.005].merkmale.min()
    p(f"\nKleinstes Modell mit Saison-AUC (1 Tag) höchstens 0,005 unter dem besten: **{small} Merkmale** – "
      + ", ".join(rank.index[:int(small)]))

    # ---------------- 4. Lokales Wissen
    p("\n## 4. Lokales Wissen im Modell\n")
    ds = deseason(["tmax_milano", "tmax_bergamo", "tmax_sondrio", "tmax_chiavenna", "tmax_engadin", "taupunktdiff_milano",
                   "rad_chiavenna", "dp_po_tal_15", "dp_bergamo_sondrio_15"], S.FE[S.train])
    rows = [dict(variante="Basis", **base),
            dict(variante="monotone Wirkungsrichtungen (Physik)", **S.evaluate(fp_mono(F), F)),
            dict(variante="Jahreszeit als Vorwissen (Monats-Klima als Startwert)", **S.evaluate(fp_prior(S.D), F)),
            dict(variante="Saison stärker gewichtet (Winter ×0,3)", **S.evaluate(fp_weighted(), F)),
            dict(variante="+ entsaisonalisierte Temperaturen/Gefälle", **S.evaluate(fp_xgb(), F, transform=ds)),
            dict(variante="+ physikalische Kombinationen (Thermik, Föhn, Hitze)", **S.evaluate(fp_xgb(), F, transform=engineered))]
    comb = lambda X: engineered(ds(X))
    fs_small = list(rank.index[:int(small)])
    rows.append(dict(variante=f"alles + monoton + Vorwissen", **S.evaluate(fp_prior(S.D, monotone_constraints="(" + ",".join(
        str(MONO.get(f, 0)) for f in list(F) + [c + "_anom" for c in ["tmax_milano", "tmax_bergamo", "tmax_sondrio", "tmax_chiavenna",
        "tmax_engadin", "taupunktdiff_milano", "rad_chiavenna", "dp_po_tal_15", "dp_bergamo_sondrio_15"]] +
        ["thermik", "foehn_flag", "regen_tag", "gefaelle_mittel", "heiss_ebene"]) + ")"), F, transform=comb)))
    rows.append(dict(variante=f"klein ({int(small)}) + monoton", **S.evaluate(fp_mono(fs_small), fs_small)))
    p(fmt(rows))
    p("\nauc_L: ganzes Jahr, L Tage vorher; saison_L: nur März–Oktober; satellit_1: gegen Breva im Satellitenbild (1 Tag vorher).")
    p(f"\nLaufzeit {time.time() - t0:.0f} s")
    open(f"{B.RES}/modell_analyse.md", "w").write("\n".join(out) + "\n")
    print("\ngeschrieben: results/modell_analyse.md")


if __name__ == "__main__":
    main()
