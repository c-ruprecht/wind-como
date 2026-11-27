"""Heute-Modell: „Lohnt es sich heute loszufahren?“ – Chance auf einen Breva-Tag und auf einen langen Breva,
neu gerechnet um 7, 9, 11, 13 und 15 Uhr mit allem, was bis dahin bekannt ist.

  python training/train_heute.py

Merkmale
  - Vorhersage für heute: dieselben Größen wie das 7-Tage-Modell (train_breva.FEATS), im Training aus ERA5
  - Messungen bis zur Uhrzeit: Breva-Komponente (Wind in Breva-Richtung) in Samolaco, Colico, Vercana, Morbegno –
    letzte Stunde, Mittel der letzten 2 Stunden, Maximum ab 10 Uhr; Tivano am Morgen (Samolaco Nord 5–9 Uhr)
  - Vortag: Breva gestern ja/nein und Stärke (aus Samolaco, gleiche Regel wie in der App: brevaDay)
  - Seewind-Schätzung aus Samolaco ODER Colico (× Satellitenfaktor, nur Breva-Sektor, wie das Ziel): jetzt,
    Stunden ≥ 14 kn seit 11 Uhr, laufende Folge; Morgenwind aus Nicht-Breva-Richtung (6–10 Uhr, bis zur Stunde)
Ziele (results/breva_tage.csv, breva_daten.tage): „14“ = breva (≥ 14 kn ≥ 2 h), „lang“ = breva_lang (≥ 5 h ≥ 14 kn).
Eichung: Modell bis 2023, geprüft 2024–heute mit den ECMWF-Läufen vom Vortag als „Vorhersage für heute“
(etwas schlechter als der Lauf vom selben Morgen – die Chancen sind also eher vorsichtig).
Export: app/model/heute_<stunde>_<ziel>.json, app/model/heute.json; results/oof_heute.csv (für pr_kurven.py)
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402
import train_breva as T  # noqa: E402

HOURS = [7, 9, 11, 13, 15]
ZIELE = {"14": ("breva", "Breva-Tag (≥ 14 kn, ≥ 2 h)"), "lang": ("breva_lang", "langer Breva (≥ 5 h ≥ 14 kn)")}
# feste Richtungen auch für die Messungen: mehr Wind in Breva-Richtung / Breva gestern -> nie weniger Chance
T.MONO.update({f"{st}_{k}": 1 for st in ("samolaco", "colico", "vercana", "morbegno") for k in ("jetzt", "mittel2h", "max_ab10")})
T.MONO.update({"gestern_breva": 1, "see_jetzt": 1, "see_stunden": 1, "see_lauf": 1, "morgen_nicht_breva": -1})
AXIS = {"samolaco": 157, "colico": 270, "vercana": 225, "morbegno": 245}     # Breva-Richtung je Station (Grad)
OBS = ([f"{st}_{k}" for st in AXIS for k in ("jetzt", "mittel2h", "max_ab10")] + ["tivano_samolaco"]
       + ["see_jetzt", "see_stunden", "see_lauf", "morgen_nicht_breva"])
VORTAG = ["gestern_breva", "gestern_max"]


def hourly_obs():
    """{station: DataFrame(kn, dir) mit Index Ortszeit, Stunde endet zur vollen Stunde}"""
    out = {}
    for st in AXIS:
        x = pd.read_csv(os.path.join(B.DATA, "arpa", f"{st}_wind.csv"), parse_dates=["time"]).set_index("time")
        x.index = pd.DatetimeIndex(x.index).tz_convert(B.TZ).tz_localize(None)
        x = x[~x.index.duplicated(keep="first")]      # Herbst-Zeitumstellung: doppelte Ortszeit-Stunde
        out[st] = x[["kn", "dir"]]
    return out


def see_series(O, fs, fc):
    """Seewind-Schätzung je Stunde wie das Ziel (breva_daten.see_hourly): max(Samolaco × fs, Colico × fc), nur Breva-Sektor"""
    ins = lambda x, st: (x.dir >= B.SEKTOR[st][0]) & (x.dir <= B.SEKTOR[st][1])  # noqa: E731
    s, c = O["samolaco"], O["colico"]
    ls = (s.kn * fs).where(ins(s, "samolaco"), 0); lc = (c.kn * fc).where(ins(c, "colico"), 0)
    see = pd.concat([ls.rename("s"), lc.rename("c")], axis=1, sort=True).max(axis=1)
    mor = s.kn.where(~ins(s, "samolaco"), 0)
    return see, mor


def obs_features(O, days, hour, fs=1.41, fc=2.66):
    """wie BrevaModel.obsFeatures (app/breva_model.js)"""
    rows = {}
    comp = {st: O[st].kn * np.cos(np.radians(O[st].dir - ax)) for st, ax in AXIS.items()}
    tiv = O["samolaco"].kn * np.cos(np.radians(O["samolaco"].dir - 337))
    see, mor = see_series(O, fs, fc)
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
        tv = [tiv.get(d + pd.Timedelta(hours=h), np.nan) for h in range(5, min(9, hour) + 1)]
        tv = [v for v in tv if np.isfinite(v)]
        r["tivano_samolaco"] = max(tv) if tv else np.nan
        gs = lambda h: see.get(d + pd.Timedelta(hours=h), np.nan)  # noqa: E731
        r["see_jetzt"] = gs(hour)
        n = run = 0
        for h in range(11, hour + 1):                  # wie das Ziel: 11–20 Uhr, Lücke unterbricht die Folge
            v = gs(h); ok = np.isfinite(v) and v >= 14
            n += ok; run = run + 1 if ok else 0
        r["see_stunden"] = n if hour >= 11 else np.nan
        r["see_lauf"] = run if hour >= 11 else np.nan
        mv = [mor.get(d + pd.Timedelta(hours=h), np.nan) for h in range(6, min(10, hour) + 1)]
        mv = [v for v in mv if np.isfinite(v)]
        r["morgen_nicht_breva"] = float(np.mean(mv)) if mv else np.nan
        rows[d] = r
    return pd.DataFrame.from_dict(rows, orient="index")


def main():
    from sklearn.metrics import roc_auc_score, brier_score_loss
    D = pd.read_csv(f"{B.RES}/breva_tage.csv", index_col=0, parse_dates=True)
    if "breva" not in D:
        sys.exit("breva_tage.csv ohne Spalte breva – erst python training/breva_daten.py tage")
    fs, fc = float(D.faktor_sam.iloc[0]), float(D.faktor_col.iloc[0])
    O = hourly_obs()
    # Vortag direkt aus dem Ziel (die App rechnet ihn genauso: BrevaModel.brevaDay)
    full = D.reindex(pd.date_range(D.index.min(), D.index.max(), freq="D"))
    V = pd.DataFrame({"gestern_breva": full.breva.shift(1), "gestern_max": full.see_max_stunde.shift(1)}).reindex(D.index)
    FE = B.features(B.load("era5")).reindex(D.index)[T.FEATS]
    L1 = B.features(B.load("prev", 1, T.MODEL)).reindex(D.index)
    for c in T.FEATS:
        if c not in L1:
            L1[c] = np.nan
    L1 = L1[T.FEATS]
    out = {"version": 2, "ziel": "C", "ziele": {k: v[1] for k, v in ZIELE.items()}, "lang_h": B.LANG_H,
           "monoton": T.OPT["monoton"], "hours": HOURS, "features": T.FEATS + OBS + VORTAG, "obs": OBS, "vortag": VORTAG,
           "faktor": round(fs, 3), "faktor_col": round(fc, 3), "sektor": B.SEKTOR, "axis": AXIS,
           "files": {}, "calib": {}, "skill": {}, "call": {}}
    os.makedirs(T.OUT, exist_ok=True)
    for old in os.listdir(T.OUT):                       # alte Dateien (heute_9_18.json …) entfernen
        if old.startswith("heute_") and old.endswith(".json"):
            os.remove(os.path.join(T.OUT, old))
    test = D.index.year > T.TRAIN_UNTIL
    saison = (D.index.month >= 3) & (D.index.month <= 10)
    rows_all, OOF = [], []
    obs_only = [c for c in out["features"] if c not in T.FEATS]
    for hour in HOURS:
        Ob = obs_features(O, D.index, hour, fs, fc)
        X = pd.concat([FE, Ob, V], axis=1)[out["features"]]
        Xl = pd.concat([L1, Ob, V], axis=1)[out["features"]]
        for key, (col, name) in ZIELE.items():
            y = D[col].fillna(0).astype(int)
            ok = X.notna().mean(axis=1) > 0.7
            final = T.xgb_model(out["features"]).fit(X[ok], y[ok])
            fn = f"heute_{hour}_{key}.json"
            json.dump(T.compact(final), open(f"{T.OUT}/{fn}", "w"), separators=(",", ":"))
            out["files"][f"{hour}_{key}"] = fn
            good = test & (Xl.notna().mean(axis=1) > 0.7)

            def oof(feats, Xtr, Xte):
                """je Testjahr: Modell an ERA5/Messungen aller anderen Jahre, Vorhersage dieses Jahres"""
                pr = pd.Series(np.nan, index=D.index)
                for yr in sorted(set(D.index[good].year)):
                    tr = ok & (D.index.year != yr); te = good & (D.index.year == yr)
                    m = T.xgb_model(feats).fit(Xtr.loc[tr, feats], y[tr])
                    pr[te] = m.predict_proba(Xte.loc[te, feats])[:, 1]
                return pr
            P = oof(out["features"], X, Xl)
            Pf = oof(T.FEATS, FE, L1)                 # nur Vorhersage
            Po = oof(obs_only, X, X)                  # nur Messungen
            p = P[good].values; yy = y[good].values
            curve = T.iso_curve(p, yy)
            out["calib"][f"{hour}_{key}"] = curve
            pc = np.interp(p, *curve)
            cut = T.precision_cut(pc, yy)
            out["call"][f"{hour}_{key}"] = cut
            print(f"   Call {hour} Uhr, {name}: " +
                  (f"ab {100 * cut['schwelle']:.0f} % – Präzision {100 * cut['praezision']:.0f} %, "
                   f"erwischt {100 * cut['trefferquote']:.0f} % ({cut['calls']} Calls)" if cut else f"{100 * T.CALL_PRAEZISION:.0f} % Präzision nie erreicht"), flush=True)
            OOF.append(pd.DataFrame({"tag": D.index[good], "ziel": key, "stunde": hour, "p_roh": p, "p": pc, "y": yy}))
            gs = good & saison
            ys = y[gs].values
            r = dict(uhr=hour, ziel=key, tage=int(good.sum()), ja=int(yy.sum()),
                     auc=round(roc_auc_score(yy, p), 3),
                     auc_saison=round(roc_auc_score(ys, P[gs]), 3),
                     auc_saison_nur_vorhersage=round(roc_auc_score(ys, Pf[gs]), 3),
                     auc_saison_nur_messungen=round(roc_auc_score(ys, Po[gs]), 3),
                     brier=round(brier_score_loss(yy, pc), 3))
            imp = T.xgb_model().fit(X[ok], y[ok]).get_booster().get_score(importance_type="gain")
            r["wichtig"] = ", ".join(k for k, _ in sorted(imp.items(), key=lambda kv: -kv[1])[:5])
            rows_all.append(r)
            out["skill"][f"{hour}_{key}"] = {k: v for k, v in r.items() if k != "wichtig"}
    pd.set_option("display.width", 220)
    R = pd.DataFrame(rows_all)
    print(f"\nHeute-Modell, geprüft {T.TRAIN_UNTIL + 1}–heute je Jahr out-of-fold (Vorhersage = ECMWF-Lauf vom Vortag):")
    print(R.drop(columns="wichtig").to_string(index=False))
    print("\nwichtigste Größen (Gain):")
    for r in rows_all:
        print(f"  {r['uhr']} Uhr {r['ziel']}: {r['wichtig']}")
    pb = D.breva.groupby(V.gestern_breva).mean()
    out["vortag_stat"] = {str(int(k)): round(float(v), 3) for k, v in pb.items()}
    print(f"\nBreva heute, wenn gestern Breva: {pb.get(1.0, np.nan):.0%}, wenn nicht: {pb.get(0.0, np.nan):.0%}")
    sa = D[saison & D.breva.astype(bool)]
    print(f"Anteil lange Breva (≥ {B.LANG_H} h) an Breva-Tagen März–Oktober: {sa.breva_lang.mean():.0%}")
    json.dump(out, open(f"{T.OUT}/heute.json", "w"), separators=(",", ":"))
    R.to_csv(f"{B.RES}/heute_skill.csv", index=False)
    pd.concat(OOF).round(4).to_csv(f"{B.RES}/oof_heute.csv", index=False)
    print("geschrieben: app/model/heute.json + heute_<uhr>_<ziel>.json, results/heute_skill.csv, results/oof_heute.csv")


if __name__ == "__main__":
    main()
