"""Daten für die Modell-Seite (app/modell.html): Prüfwerte, PR-Kurven, Eichung, Faktoren.

Grundlage (alles aus results/ und app/model/, keine Wetterdaten nötig):
  results/oof_7tage.csv, results/oof_heute.csv     out-of-fold-Vorhersagen 2024–heute (train_breva / train_heute)
  results/breva_tage.csv                            Ziel (breva, breva_lang)
  results/heute_skill.csv                           Heute-Modell: nur Vorhersage / nur Messungen
  results/breva_klassen_merkmale.csv                Faktoren ruhig → kurz → lang (breva_klassen.py)
  app/model/manifest.json, heute.json               Merkmale, Eichung (auch „lang“)

  python training/export_modell.py   -> app/modell.json
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402

RES = B.RES
APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
SAISON = range(3, 11)


def rnd(v, n=3):
    return None if v is None or not np.isfinite(v) else round(float(v), n)


def auc(y, p):
    from sklearn.metrics import roc_auc_score
    return rnd(roc_auc_score(y, p)) if len(set(y)) == 2 else None


def pr(y, p, n=70):
    from sklearn.metrics import precision_recall_curve, average_precision_score
    prec, rec, thr = precision_recall_curve(y, p)
    keep = np.unique(np.linspace(0, len(prec) - 1, min(n, len(prec))).astype(int))
    pts = [[rnd(rec[i]), rnd(prec[i]), rnd(thr[min(i, len(thr) - 1)])] for i in keep]
    return {"ap": rnd(average_precision_score(y, p)), "anteil": rnd(np.mean(y)), "punkte": pts,
            "r70": rnd(max([r for P, r in zip(prec, rec) if P >= 0.7], default=np.nan))}


def calib(y, p, edges=np.linspace(0, 1, 11)):
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (p >= a) & ((p < b) if b < 1 else (p <= b))
        if m.sum() >= 5:
            out.append([rnd(p[m].mean()), rnd(y[m].mean()), int(m.sum())])
    return out


def main():
    D = pd.read_csv(f"{RES}/breva_tage.csv", index_col=0, parse_dates=True)
    man = json.load(open(f"{APP}/model/manifest.json"))
    H = json.load(open(f"{APP}/model/heute.json"))
    out = {"stand": pd.Timestamp.today().strftime("%Y-%m-%d"), "features7": man["features"],
           "features_heute": [f for f in H["features"] if f not in man["features"]], "lang_h": H.get("lang_h", 5),
           "trainiert": man.get("trained"), "faktor_sam": H.get("faktor"), "faktor_col": H.get("faktor_col")}
    S = D[D.index.month.isin(SAISON)]
    out["anteil"] = {"breva": rnd(S.breva.mean()), "lang": rnd(S.breva_lang.mean()),
                     "tage_jahr_breva": rnd(S.breva.sum() / S.index.year.nunique(), 1),
                     "tage_jahr_lang": rnd(S.breva_lang.sum() / S.index.year.nunique(), 1)}

    # 7 Tage
    O = pd.read_csv(f"{RES}/oof_7tage.csv", parse_dates=["tag"])
    O = O[(O.schwelle == 14) & O.tag.dt.month.isin(SAISON)]
    cl = man.get("calib_lang", {})
    seven = {}
    for L, x in O.groupby("vorlauf"):
        yb = x.y.values.astype(int); pb = x.p.values
        yl = D.breva_lang.reindex(x.tag).fillna(0).values.astype(int)
        r = {"tage": int(len(x)), "breva": {"auc": auc(yb, pb), **pr(yb, pb), "eichung": calib(yb, pb)}}
        if str(L) in cl and cl[str(L)]:
            pl = np.minimum(np.interp(x.p_roh.values, *cl[str(L)]), pb)
            r["lang"] = {"auc": auc(yl, pl), **pr(yl, pl), "eichung": calib(yl, pl)}
        seven[str(L)] = r
    out["sieben"] = seven

    # Heute
    fh = f"{RES}/oof_heute.csv"
    if os.path.exists(fh):
        J = pd.read_csv(fh, parse_dates=["tag"])
        J = J[J.tag.dt.month.isin(SAISON)]
        J["ziel"] = J.ziel.astype(str)
        heute = {}
        for (z, h), x in J.groupby(["ziel", "stunde"]):
            y = x.y.values.astype(int); p = x.p.values
            heute.setdefault(z, {})[str(h)] = {"auc": auc(y, p), **pr(y, p), "eichung": calib(y, p)}
        out["heute"] = heute
    fs = f"{RES}/heute_skill.csv"
    if os.path.exists(fs):
        K = pd.read_csv(fs)
        K["ziel"] = K.ziel.astype(str)
        out["heute_quellen"] = {z: {str(int(r.uhr)): {"alles": rnd(r.auc_saison), "vorhersage": rnd(r.auc_saison_nur_vorhersage),
                                                    "messungen": rnd(r.auc_saison_nur_messungen)} for r in g.itertuples()}
                                for z, g in K.groupby("ziel")}
        out["heute_wichtig"] = {f"{int(r.uhr)}_{r.ziel}": r.wichtig.split(", ") for r in K.itertuples()}

    # Faktoren ruhig → kurz → lang
    fk = f"{RES}/breva_klassen_merkmale.csv"
    if os.path.exists(fk):
        M = pd.read_csv(fk)
        M = M[M.groesse.isin(man["features"] + ["rad_milano", "bodenfeuchte_milano", "tmax_see"])]
        M["staerke"] = M.eff_ruhig_kurz.abs() + M.eff_kurz_lang.abs()
        eigen = M[(M.eff_kurz_lang.abs() >= 0.15) & (M.eff_ruhig_kurz.abs() < 0.1)].groesse.tolist()
        immer = eigen + [c for c in ("dp_zurich_milano_12", "regen_chiavenna", "wolken_chiavenna") if c in set(M.groesse)]
        top = [c for c in M.sort_values("staerke", ascending=False).groesse if c not in immer][:13]
        M = M[M.groesse.isin(top + immer)].sort_values("eff_ruhig_kurz", ascending=False)
        out["faktoren"] = [{"f": r.groesse, "ruhig_kurz": rnd(r.eff_ruhig_kurz), "kurz_lang": rnd(r.eff_kurz_lang),
                            "im_modell": bool(r.im_modell), "eigen_lang": r.groesse in eigen,
                            "med": [rnd(getattr(r, f"median_{k}"), 2) for k in ("ruhig", "grenzfall", "kurz", "lang")]}
                           for r in M.itertuples()]
    json.dump(out, open(f"{APP}/modell.json", "w"), separators=(",", ":"), ensure_ascii=False)
    print(f"geschrieben: app/modell.json ({os.path.getsize(f'{APP}/modell.json') // 1024} kB)")


if __name__ == "__main__":
    main()
