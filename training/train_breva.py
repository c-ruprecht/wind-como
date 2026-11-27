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


# Wirkungsrichtungen (model_analyse.py Teil 4: bessere AUC bei 3–5 Tagen Vorlauf und gegen den Satelliten)
MONO = {"wind_see_15_sued": 1, "taupunktdiff_milano": 1, "dp_po_tal_15": 1, "dp_po_tal_18": 1,
        "dp_bergamo_sondrio_15": 1, "dp_tag_minus_nacht": 1, "dp_zurich_milano_12": -1, "regen_see": -1,
        "regen_chiavenna": -1, "regen_vortag": -1, "rad_chiavenna": 1, "rad_spaet_chiavenna": 1, "rad_see": 1,
        "wolken_see": -1, "wolken_chiavenna": -1, "wolken_morgen_see": -1}
OPT = {"ziel": os.environ.get("BREVA_ZIEL", "B"), "monoton": os.environ.get("BREVA_MONOTON", "0") == "1"}


def target(D, thr):
    """Ziel B (Standard): nur aus Stationen – Breva auf dem See, morgens ruhig, kein Nordwind; Regen zählt nicht.
    Trifft den Satelliten besser (0,81 statt 0,72, model_analyse Teil 5). Ziel A: Störtage inkl. ERA5-Regen = 0."""
    if OPT["ziel"] == "B":
        return ((D[f"breva{thr}"] == 1) & (D.sam_morgen < 6) & (D.sam_nord_std < 2)).astype(int)
    return D[f"breva{thr}"].where(D.klasse.isin(["Breva", "Breva schwach", "ruhig"]), 0).astype(int)


def xgb_model(feats=None):
    from xgboost import XGBClassifier
    kw = {}
    if os.environ.get("BREVA_XGB_THREADS"):
        kw["n_jobs"] = int(os.environ["BREVA_XGB_THREADS"])
    if OPT["monoton"] and feats is not None:
        kw["monotone_constraints"] = "(" + ",".join(str(MONO.get(f, 0)) for f in feats) + ")"
    return XGBClassifier(n_estimators=250, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                         min_child_weight=5, eval_metric="logloss", verbosity=0, **kw)


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


def precision_cut(pc, y, target=0.8, min_calls=8):
    """Kleinste Schwelle auf der geeichten Chance, ab der die Calls (pc ≥ Schwelle) mindestens `target` Präzision haben.
    Gibt Schwelle, Präzision, Trefferquote (Anteil aller Breva-Tage, die gecallt wurden) und Zahl der Calls zurück."""
    pc = np.asarray(pc, float); y = np.asarray(y, int)
    best = None
    for c in sorted(set(np.round(pc, 4)), reverse=True):
        sel = pc >= c
        if sel.sum() < min_calls:
            continue
        prec = y[sel].mean()
        if prec >= target:
            best = dict(schwelle=round(float(c), 4), praezision=round(float(prec), 3),
                        trefferquote=round(float(y[sel].sum() / max(y.sum(), 1)), 3), calls=int(sel.sum()))
    return best


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
    print(f"Ziel {OPT['ziel']}, {'monoton' if OPT['monoton'] else 'ohne feste Richtungen'}")
    man = {"version": 1, "features": FEATS, "ziel": OPT["ziel"], "monoton": OPT["monoton"], "model": MODEL, "points": {p: [la, lo] for p, (la, lo, _) in B.POINTS.items()},
           "trained": f"ERA5 {D.index.year.min()}–{D.index.year.max()}", "calib": {}, "skill": {}, "files": {}}
    test_rows = X.dropna(thresh=len(FEATS) - 5).sample(150, random_state=1)
    man["test"] = {"rows": test_rows.astype(float).where(test_rows.notna(), None).values.tolist(), "p": {}}
    OOF = []
    for thr in (14, 18):
        y = target(D, thr)
        ok = X.notna().mean(axis=1) > 0.7
        final = xgb_model(FEATS).fit(X[ok], y[ok])
        fn = f"breva_{thr}.json"
        json.dump(compact(final), open(f"{OUT}/{fn}", "w"), separators=(",", ":"))
        man["files"][str(thr)] = fn
        man["test"]["p"][str(thr)] = final.predict_proba(test_rows)[:, 1].round(6).tolist()
        # Eichung je Vorlauf, out-of-fold: für jedes Jahr mit archivierten Vorhersagen ein Modell an ERA5 aller
        # ANDEREN Jahre; damit dieses Jahr aus den echten Läufen vorhersagen. So sieht jede Eichungs-Vorhersage ein
        # Modell mit fast allen Daten (wie das Endmodell), aber nie das eigene Jahr.
        test_days = D.index[D.index.year > TRAIN_UNTIL]
        oof = {}
        for yr in sorted(set(test_days.year)):
            m = xgb_model(FEATS).fit(X[ok & (X.index.year != yr)], y[ok & (X.index.year != yr)])
            for L in B.LEADS:
                d = test_days[test_days.year == yr]; Xt = leads[L].loc[d, FEATS]
                good = Xt.notna().mean(axis=1) > 0.7
                if good.sum():
                    oof.setdefault(L, []).append(pd.Series(m.predict_proba(Xt[good])[:, 1], index=d[good.values]))
        cal, skill, calls = {}, [], {}
        for grp in LEAD_GROUPS[thr]:
            ps, ys = [], []
            for L in grp:
                if L not in oof:
                    continue
                pr = pd.concat(oof[L])
                ps.append(pr.values); ys.append(y[pr.index].values)
            if not ps:
                continue
            p, yy = np.concatenate(ps), np.concatenate(ys)
            curve = iso_curve(p, yy)
            for L in grp:
                cal[str(L)] = curve
            from sklearn.isotonic import IsotonicRegression
            pc = np.interp(p, curve[0], curve[1])
            cut = precision_cut(pc, yy)
            for L in grp:
                calls[str(L)] = cut
            print(f"   Breva-Call ≥ {thr} kn, Vorlauf {'+'.join(map(str, grp))}: " +
                  (f"ab {100 * cut['schwelle']:.0f} % – Präzision {100 * cut['praezision']:.0f} %, "
                   f"erwischt {100 * cut['trefferquote']:.0f} % der Breva-Tage ({cut['calls']} Calls)" if cut else "80 % Präzision nie erreicht"))
            mon = np.concatenate([pd.concat(oof[L]).index.month for L in grp if L in oof])
            sa = (mon >= 3) & (mon <= 10)
            skill.append(dict(vorlauf="+".join(map(str, grp)), tage=len(yy), breva=int(yy.sum()),
                              auc=round(roc_auc_score(yy, p), 3),
                              auc_saison=round(roc_auc_score(yy[sa], p[sa]), 3), brier_roh=round(brier_score_loss(yy, p), 3),
                              brier_geeicht=round(brier_score_loss(yy, pc), 3), mittel_roh=round(float(p.mean()), 3),
                              mittel_geeicht=round(float(pc.mean()), 3), anteil_echt=round(float(yy.mean()), 3)))
        cal["0"] = cal.get("1"); calls["0"] = calls.get("1")
        for L, parts in oof.items():                       # out-of-fold-Vorhersagen für PR-Kurven (pr_kurven.py)
            pr = pd.concat(parts)
            if str(L) in cal and cal[str(L)]:
                OOF.append(pd.DataFrame({"tag": pr.index, "schwelle": thr, "vorlauf": L, "p_roh": pr.values,
                                         "p": np.interp(pr.values, *cal[str(L)]), "y": y[pr.index].values}))
        man["calib"][str(thr)] = cal
        man.setdefault("call", {})[str(thr)] = calls
        man["skill"][str(thr)] = skill
        print(f"\n≥ {thr} kn: {int(y[ok].sum())} Breva-Tage von {int(ok.sum())} (ERA5); Prüfung {TRAIN_UNTIL + 1}–heute mit {MODEL}, je Jahr out-of-fold:")
        print(pd.DataFrame(skill).to_string(index=False))
    json.dump(man, open(f"{OUT}/manifest.json", "w"), separators=(",", ":"))
    if OOF:
        pd.concat(OOF).round(4).to_csv(f"{B.RES}/oof_7tage.csv", index=False)
        print("geschrieben: results/oof_7tage.csv (out-of-fold je Tag, Vorlauf, Schwelle)")
    print(f"\ngeschrieben: app/model/manifest.json, breva_14.json, breva_18.json ({len(FEATS)} Merkmale)")


if __name__ == "__main__":
    main()
