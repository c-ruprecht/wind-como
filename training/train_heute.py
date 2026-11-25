"""Heute-Modell: „Lohnt es sich heute loszufahren?“ – Chance auf Breva ≥ 14 / ≥ 18 kn am selben Tag,
neu gerechnet um 9, 11 und 13 Uhr mit allem, was bis dahin bekannt ist.

  python training/train_heute.py

Merkmale
  - Vorhersage für heute: dieselben Größen wie das 7-Tage-Modell (train_breva.FEATS), im Training aus ERA5
  - Messungen bis zur Uhrzeit: Breva-Komponente (Wind in Breva-Richtung) in Samolaco, Colico, Vercana, Morbegno –
    letzte Stunde, Mittel der letzten 2 Stunden, Maximum ab 10 Uhr; Tivano am Morgen (Samolaco Nord 5–9 Uhr)
  - Vortag: Breva gestern ja/nein und Stärke (aus Samolaco, gleiche Regel wie in der App: brevaDay)
Ziel: Tagesklasse Breva ≥ 14 / ≥ 18 kn (results/breva_tage.csv), Störungstage = 0.
Eichung: Modell bis 2023, geprüft 2024–heute mit den ECMWF-Läufen vom Vortag als „Vorhersage für heute“
(etwas schlechter als der Lauf vom selben Morgen – die Chancen sind also eher vorsichtig).
Export: app/model/heute_<stunde>_<schwelle>.json, app/model/heute.json
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402
import train_breva as T  # noqa: E402

HOURS = [9, 11, 13]
AXIS = {"samolaco": 157, "colico": 270, "vercana": 225, "morbegno": 245}     # Breva-Richtung je Station (Grad)
OBS = [f"{st}_{k}" for st in AXIS for k in ("jetzt", "mittel2h", "max_ab10")] + ["tivano_samolaco"]
VORTAG = ["gestern_breva", "gestern_max"]


def hourly_obs():
    """{station: DataFrame(kn, dir) mit Index Ortszeit, Stunde endet zur vollen Stunde}"""
    out = {}
    for st in AXIS:
        x = pd.read_csv(os.path.join(B.DATA, "arpa", f"{st}_wind.csv"), parse_dates=["time"]).set_index("time")
        x.index = pd.DatetimeIndex(x.index).tz_convert(B.TZ).tz_localize(None)
        out[st] = x[["kn", "dir"]]
    return out


def obs_features(O, days, hour):
    """wie BrevaModel.obsFeatures (app/breva_model.js)"""
    rows = {}
    comp = {st: O[st].kn * np.cos(np.radians(O[st].dir - ax)) for st, ax in AXIS.items()}
    tiv = O["samolaco"].kn * np.cos(np.radians(O["samolaco"].dir - 337))
    for d in days:
        r = {}
        for st in AXIS:
            c = comp[st]
            g = lambda h: c.get(d + pd.Timedelta(hours=h), np.nan)
            last, prev = g(hour), g(hour - 1)
            seq = [g(h) for h in range(10, hour + 1)]
            seq = [v for v in seq if np.isfinite(v)]
            r[f"{st}_jetzt"] = last
            r[f"{st}_mittel2h"] = (last + prev) / 2 if np.isfinite(last) and np.isfinite(prev) else last
            r[f"{st}_max_ab10"] = max(seq) if seq else np.nan
        tv = [tiv.get(d + pd.Timedelta(hours=h), np.nan) for h in range(5, 10)]
        tv = [v for v in tv if np.isfinite(v)]
        r["tivano_samolaco"] = max(tv) if tv else np.nan
        rows[d] = r
    return pd.DataFrame.from_dict(rows, orient="index")


def breva_day(O, factor):
    """wie BrevaModel.brevaDay: Samolaco × Faktor ≥ 14 kn, ≥ 2 h am Stück aus SSO–S (11–20 Uhr), morgens < 6 kn"""
    s = O["samolaco"]
    out = {}
    for d, g in s.groupby(s.index.normalize()):
        h = g.index.hour
        nm = g[(h >= 11) & (h <= 20)]
        if len(nm) < 8:
            continue
        ok = ((nm.kn * factor >= 14) & (nm.dir >= 112) & (nm.dir <= 202)).astype(int)
        # Lücken (fehlende Stunden) unterbrechen die Folge wie in der App
        full = ok.reindex(pd.date_range(d + pd.Timedelta(hours=11), d + pd.Timedelta(hours=20), freq="h")).fillna(0)
        run = (full.groupby((full != full.shift()).cumsum()).cumsum() * full).max()
        m = g[(h >= 6) & (h <= 10)].kn.mean()
        out[d] = {"breva": int(run >= 2 and (m if np.isfinite(m) else 0) < 6), "max": nm.kn.max() * factor}
    return pd.DataFrame.from_dict(out, orient="index")


def main():
    from sklearn.metrics import roc_auc_score, brier_score_loss
    D = pd.read_csv(f"{B.RES}/breva_tage.csv", index_col=0, parse_dates=True)
    factor = float((D.see_max_est / D.sam_max).median())                # Satellitenfaktor, mit dem tage() gerechnet hat
    O = hourly_obs()
    BD = breva_day(O, factor)
    V = pd.DataFrame({"gestern_breva": BD.breva.shift(1, freq="D"), "gestern_max": BD["max"].shift(1, freq="D")}).reindex(D.index)
    FE = B.features(B.load("era5")).reindex(D.index)[T.FEATS]
    L1 = B.features(B.load("prev", 1, T.MODEL)).reindex(D.index)
    for c in T.FEATS:
        if c not in L1:
            L1[c] = np.nan
    L1 = L1[T.FEATS]
    out = {"version": 1, "hours": HOURS, "features": T.FEATS + OBS + VORTAG, "obs": OBS, "vortag": VORTAG,
           "faktor": round(factor, 3), "axis": AXIS, "files": {}, "calib": {}, "skill": {}}
    os.makedirs(T.OUT, exist_ok=True)
    test = D.index.year > T.TRAIN_UNTIL
    rows_all = []
    for hour in HOURS:
        X = pd.concat([FE, obs_features(O, D.index, hour), V], axis=1)[out["features"]]
        Xl = pd.concat([L1, obs_features(O, D.index, hour), V], axis=1)[out["features"]]
        for thr in (14, 18):
            y = D[f"breva{thr}"].where(D.klasse.isin(["Breva", "Breva schwach", "ruhig"]), 0).astype(int)
            ok = X.notna().mean(axis=1) > 0.7
            final = T.xgb_model().fit(X[ok], y[ok])
            fn = f"heute_{hour}_{thr}.json"
            json.dump(T.compact(final), open(f"{T.OUT}/{fn}", "w"), separators=(",", ":"))
            out["files"][f"{hour}_{thr}"] = fn
            m = T.xgb_model().fit(X[ok & ~test], y[ok & ~test])
            good = test & (Xl.notna().mean(axis=1) > 0.7)
            p = m.predict_proba(Xl[good])[:, 1]; yy = y[good].values
            curve = T.iso_curve(p, yy)
            out["calib"][f"{hour}_{thr}"] = curve
            # Vergleich: nur Vorhersage (7-Tage-Merkmale) und nur Messungen
            mf = T.xgb_model().fit(FE[ok & ~test], y[ok & ~test])
            obs_only = [c for c in out["features"] if c not in T.FEATS]
            mo = T.xgb_model().fit(X.loc[ok & ~test, obs_only], y[ok & ~test])
            r = dict(uhr=hour, schwelle=thr, tage=int(good.sum()), breva=int(yy.sum()),
                     auc=round(roc_auc_score(yy, p), 3),
                     auc_nur_vorhersage=round(roc_auc_score(yy, mf.predict_proba(L1[good])[:, 1]), 3),
                     auc_nur_messungen=round(roc_auc_score(yy, mo.predict_proba(X.loc[good, obs_only])[:, 1]), 3),
                     brier=round(brier_score_loss(yy, np.interp(p, *curve)), 3))
            imp = T.xgb_model().fit(X[ok], y[ok]).get_booster().get_score(importance_type="gain")
            r["wichtig"] = ", ".join(k for k, _ in sorted(imp.items(), key=lambda kv: -kv[1])[:5])
            rows_all.append(r)
            out["skill"][f"{hour}_{thr}"] = {k: v for k, v in r.items() if k != "wichtig"}
    pd.set_option("display.width", 220)
    R = pd.DataFrame(rows_all)
    print(f"Heute-Modell, geprüft {T.TRAIN_UNTIL + 1}–heute (Vorhersage = ECMWF-Lauf vom Vortag):")
    print(R.drop(columns="wichtig").to_string(index=False))
    print("\nwichtigste Größen (Gain):")
    for r in rows_all:
        print(f"  {r['uhr']} Uhr ≥{r['schwelle']}: {r['wichtig']}")
    V2 = V.join(D[["klasse"]])
    pb = V2.groupby("gestern_breva").klasse.apply(lambda k: (k == "Breva").mean())
    out["vortag_stat"] = {str(int(k)): round(float(v), 3) for k, v in pb.items()}
    print(f"\nBreva heute, wenn gestern Breva: {pb.get(1.0, np.nan):.0%}, wenn nicht: {pb.get(0.0, np.nan):.0%}")
    json.dump(out, open(f"{T.OUT}/heute.json", "w"), separators=(",", ":"))
    R.to_csv(f"{B.RES}/heute_skill.csv", index=False)
    print("geschrieben: app/model/heute.json + heute_<uhr>_<schwelle>.json, results/heute_skill.csv")


if __name__ == "__main__":
    main()
