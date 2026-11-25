"""Breva-Modell für die App: Chance auf mind. 2 h am Stück ≥ 14 / ≥ 18 kn auf dem oberen See, 7 Tage voraus.

  python training/train_breva.py

Voraussetzung: breva_daten.py wetter, laeufe, tage.

- Ziel: Tagesklassen (results/breva_tage.csv) – Breva ≥ 14 / ≥ 18 kn; Störungstage (Regen, Föhn, …) zählen als 0.
- Merkmale: nur Größen, die die ECMWF-Vorhersage für 7 Tage liefert (FEATS), berechnet wie in breva_daten.features().
- Modell: XGBoost auf ERA5 2014–heute (Wetter, wie es war).
- Eichung je Vorlauftag: ein zweites Modell nur bis 2023 sagt die Tage ab 2024 aus den echten ECMWF-Läufen
  (1–7 Tage vorher) voraus; daraus eine isotone Kurve je Vorlauf (Vorhersagefehler der Läufe eingerechnet).
- Export nach app/model/: breva_14.json, breva_18.json (Bäume), manifest.json (Merkmale, Eichung, Prüfwerte).
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402

ROOT = B.ROOT
OUT = os.path.join(ROOT, "app", "model")
MODEL = "ecmwf_ifs025"
TRAIN_UNTIL = 2023
FEATS = ["wind_see_15_sued", "wind_see_15", "wind_milano_12", "taupunktdiff_milano",
         "dp_po_tal_06", "dp_po_tal_15", "dp_po_tal_18", "dp_tag_minus_nacht", "dp_bergamo_sondrio_15",
         "dp_zurich_milano_12", "dp_muenchen_genova_12", "dp_lyon_venezia_12",
         "geo_staerke", "geo_aus_sued", "geo_aus_west", "drucktendenz_24h",
         "rad_see", "rad_chiavenna", "rad_spaet_chiavenna", "wolken_see", "wolken_morgen_see", "wolken_chiavenna",
         "tmax_milano", "tmax_bergamo", "tmax_sondrio", "tmax_chiavenna", "tmax_engadin", "tmin_chiavenna",
         "dt_tal_po", "dt_engadin_po", "regen_see", "regen_chiavenna", "regen_vortag",
         "see_t30", "luft_minus_see_t30", "doy_sin", "doy_cos"]
LEAD_GROUPS = {14: [[1], [2], [3], [4], [5], [6], [7]], 18: [[1, 2], [3, 4], [5, 6, 7]]}


def xgb_model():
    from xgboost import XGBClassifier
    return XGBClassifier(n_estimators=250, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                         min_child_weight=5, eval_metric="logloss", verbosity=0)


def compact(m):
    """Bäume als kompaktes JSON (wie wingst/export_app_models.py)."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json") as f:
        m.save_model(f.name)
        j = json.load(open(f.name))
    L = j["learner"]
    base = float(L["learner_model_param"]["base_score"].strip("[]"))
    trees = [[t["split_indices"], [float(np.float32(v)) for v in t["split_conditions"]], t["left_children"],
              t["right_children"], t["default_left"]] for t in L["gradient_booster"]["model"]["trees"]]
    return {"base": float(np.log(base / (1 - base))), "trees": trees}


def iso_curve(p, y):
    from sklearn.isotonic import IsotonicRegression
    ir = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(p, y)
    xs, ys = ir.X_thresholds_, ir.y_thresholds_
    return [np.round(xs, 4).tolist(), np.round(ys, 4).tolist()]


def main():
    from sklearn.metrics import roc_auc_score, brier_score_loss
    D = pd.read_csv(f"{B.RES}/breva_tage.csv", index_col=0, parse_dates=True)
    FE = B.features(B.load("era5")).reindex(D.index)
    missing = [c for c in FEATS if c not in FE]
    if missing:
        sys.exit(f"Merkmale fehlen in ERA5: {missing}")
    X = FE[FEATS]
    leads = {L: B.features(B.load("prev", L, MODEL)).reindex(D.index) for L in B.LEADS}
    for L in leads:
        for c in FEATS:
            if c not in leads[L]:
                leads[L][c] = np.nan
    os.makedirs(OUT, exist_ok=True)
    man = {"version": 1, "features": FEATS, "model": MODEL, "points": {p: [la, lo] for p, (la, lo, _) in B.POINTS.items()},
           "trained": f"ERA5 {D.index.year.min()}–{D.index.year.max()}", "calib": {}, "skill": {}, "files": {}}
    test_rows = X.dropna(thresh=len(FEATS) - 5).sample(150, random_state=1)
    man["test"] = {"rows": test_rows.astype(float).where(test_rows.notna(), None).values.tolist(), "p": {}}
    for thr in (14, 18):
        y = D[f"breva{thr}"].where(D.klasse.isin(["Breva", "Breva schwach", "ruhig"]), 0).astype(int)
        ok = X.notna().mean(axis=1) > 0.7
        final = xgb_model().fit(X[ok], y[ok])
        fn = f"breva_{thr}.json"
        json.dump(compact(final), open(f"{OUT}/{fn}", "w"), separators=(",", ":"))
        man["files"][str(thr)] = fn
        man["test"]["p"][str(thr)] = final.predict_proba(test_rows)[:, 1].round(6).tolist()
        # Eichung je Vorlauf: Modell bis TRAIN_UNTIL, Vorhersagen aus den Läufen danach
        tr = ok & (X.index.year <= TRAIN_UNTIL)
        m = xgb_model().fit(X[tr], y[tr])
        test_days = D.index[D.index.year > TRAIN_UNTIL]
        cal, skill = {}, []
        for grp in LEAD_GROUPS[thr]:
            ps, ys = [], []
            for L in grp:
                Xt = leads[L].loc[test_days, FEATS]
                good = Xt.notna().mean(axis=1) > 0.7
                if good.sum() == 0:
                    continue
                ps.append(m.predict_proba(Xt[good])[:, 1]); ys.append(y[test_days][good].values)
            if not ps:
                continue
            p, yy = np.concatenate(ps), np.concatenate(ys)
            curve = iso_curve(p, yy)
            for L in grp:
                cal[str(L)] = curve
            from sklearn.isotonic import IsotonicRegression
            pc = np.interp(p, curve[0], curve[1])
            mon = np.concatenate([test_days[(leads[L].loc[test_days, FEATS].notna().mean(axis=1) > 0.7).values].month
                                  for L in grp])
            sa = (mon >= 3) & (mon <= 10)
            skill.append(dict(vorlauf="+".join(map(str, grp)), tage=len(yy), breva=int(yy.sum()),
                              auc=round(roc_auc_score(yy, p), 3),
                              auc_saison=round(roc_auc_score(yy[sa], p[sa]), 3), brier_roh=round(brier_score_loss(yy, p), 3),
                              brier_geeicht=round(brier_score_loss(yy, pc), 3), mittel_roh=round(float(p.mean()), 3),
                              mittel_geeicht=round(float(pc.mean()), 3), anteil_echt=round(float(yy.mean()), 3)))
        cal["0"] = cal.get("1")
        man["calib"][str(thr)] = cal
        man["skill"][str(thr)] = skill
        print(f"\n≥ {thr} kn: {int(y[ok].sum())} Breva-Tage von {int(ok.sum())} (ERA5); Prüfung {TRAIN_UNTIL + 1}–heute mit {MODEL}:")
        print(pd.DataFrame(skill).to_string(index=False))
    json.dump(man, open(f"{OUT}/manifest.json", "w"), separators=(",", ":"))
    print(f"\ngeschrieben: app/model/manifest.json, breva_14.json, breva_18.json ({len(FEATS)} Merkmale)")


if __name__ == "__main__":
    main()
