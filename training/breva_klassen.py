"""Kein Breva / Grenzfall / kurzer Breva / langer Breva: Was unterscheidet sie, und lohnt ein anderes Trainingsziel?

Klassen (März–Oktober, aus breva_daten.tage):
  ruhig      kein Breva und nie mehr als 10 kn auf dem See (Schätzung aus Samolaco/Colico)
  grenzfall  kein Breva-Tag, aber Wind aus Breva-Richtung (1 h ≥ 14 kn oder Maximum ≥ 10 kn)
  kurz       Breva-Tag mit 2–4 h ≥ 14 kn
  lang       Breva-Tag mit ≥ 5 h ≥ 14 kn

1. Satellit je Klasse: Rauigkeit im Nordbecken um 19:15 (sat_kategorien/abende.csv). Bestätigt der Satellit
   „lang“? Wie oft widerspricht er (kurz, aber rau um 19:15 / lang, aber glatt)?
2. Merkmale (ERA5, alle Größen aus breva_daten.features): Trennschärfe ruhig→kurz und kurz→lang.
   „Mehr vom Gleichen“ (lang = stärker ausgeprägte Breva-Faktoren) zeigt sich daran, dass dieselben Größen in
   dieselbe Richtung trennen; eigene Faktoren für „lang“ daran, dass eine Größe kurz→lang trennt, ruhig→kurz nicht.
3. Trainingsvarianten für das 7-Tage-Modell, je Testjahr out-of-fold, geprüft mit den echten Läufen (Vorlauf 1–3):
   V0 wie bisher (Breva ja/nein, alle Tage)
   V1 Grenzfälle nicht als „nein“ lernen (nur ruhige Tage als Gegenbeispiel), bewertet auf allen Tagen
   V2 Grenzfälle halb gewichtet
   V3 Stufen 0/1/2 (kein, kurz, lang) als Regression – eine Zahl für „Breva“ und „lang“
   V4 Stunden ≥ 14 kn als Regression
   Bewertet: AUC für Breva-Tag und für langen Breva (März–Oktober), Unterschied zu V0 mit Bootstrap über Wochen.

  python training/breva_klassen.py   -> results/breva_klassen.md, results/breva_klassen_merkmale.csv, results/breva_klassen.png
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402
import train_breva as T  # noqa: E402
from modell_vergleich import auc, block_boot  # noqa: E402

KL = ["ruhig", "grenzfall", "kurz", "lang"]


def klassen(D):
    k = pd.Series("grenzfall", index=D.index)
    k[(D.breva == 0) & (D.see_max_stunde < 10) & (D.breva_lauf == 0)] = "ruhig"
    k[(D.breva == 1) & (D.breva_lang == 0)] = "kurz"
    k[D.breva_lang == 1] = "lang"
    return k


def xgb_reg(feats):
    from xgboost import XGBRegressor
    return XGBRegressor(n_estimators=250, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                        min_child_weight=5, verbosity=0)


def main():
    D = pd.read_csv(f"{B.RES}/breva_tage.csv", index_col=0, parse_dates=True)
    if "breva_lang" not in D:
        sys.exit("breva_tage.csv ohne breva_lang – erst breva_daten.py tage")
    D["kl"] = klassen(D)
    S = D[D.index.month.isin(range(3, 11))]
    md = ["# Kein Breva, Grenzfall, kurzer und langer Breva\n",
          "März–Oktober " + f"{S.index.year.min()}–{S.index.year.max()}. Tage je Klasse und Jahr:\n", "```",
          (S.kl.value_counts().reindex(KL) / S.index.year.nunique()).round(1).to_string(), "```",
          "\nWind auf dem See (Schätzung aus Samolaco/Colico, stärkste Stunde 11–20 Uhr) und Ende des Breva:\n", "```",
          S.groupby("kl")[["see_max_stunde", "breva_h", "breva_start", "breva_ende"]].median().reindex(KL).round(1).to_string(), "```"]

    # 1. Satellit
    fa = f"{B.RES}/sat_kategorien/abende.csv"
    if os.path.exists(fa):
        A = pd.read_csv(fa, index_col=0, parse_dates=True)
        A = A[A.richtung == 200].join(D[["kl"]], how="inner")
        A = A[A.index.month.isin(range(3, 11))]
        t = A.groupby("kl")[["nord", "mitte", "sued", "anstieg", "rau_nord"]].median().reindex(KL).round(2)
        t["abende"] = A.kl.value_counts().reindex(KL)
        t["anteil_nord_ab_4dB"] = A.groupby("kl").nord.apply(lambda x: (x >= 4).mean()).reindex(KL).round(2)
        md += ["\n## 1. Satellit um 19:15 je Klasse (Rauigkeit über ruhig, dB; nur Abende mit Südrichtung)\n", "```",
               t.to_string(), "```",
               f"\nWidersprüche: kurz, aber Nordbecken ≥ 4 dB um 19:15: {((A.kl == 'kurz') & (A.nord >= 4)).sum()} "
               f"von {(A.kl == 'kurz').sum()}; lang, aber < 3 dB: {((A.kl == 'lang') & (A.nord < 3)).sum()} von "
               f"{(A.kl == 'lang').sum()}; ruhig, aber ≥ 4 dB: {((A.kl == 'ruhig') & (A.nord >= 4)).sum()} von "
               f"{(A.kl == 'ruhig').sum()}.",
               "Ein kurzer Breva, der um 19:15 noch rau ist, ist entweder spät gekommen oder an den Stationen "
               "unterschätzt; ein langer, der glatt ist, war vor 19 Uhr vorbei.\n"]

    # 2. Merkmale
    FE = B.features(B.load("era5"))
    X = FE.reindex(S.index)
    rows = []
    for c in X.columns:
        x = X[c]
        def a(k0, k1):
            m = S.kl.isin([k0, k1]) & x.notna()
            return auc((S.kl[m] == k1).astype(int), x[m]) if m.sum() > 50 else np.nan
        r = dict(groesse=c, im_modell=c in T.FEATS, ruhig_kurz=a("ruhig", "kurz"), kurz_lang=a("kurz", "lang"),
                 ruhig_grenzfall=a("ruhig", "grenzfall"), grenzfall_kurz=a("grenzfall", "kurz"))
        for k in KL:
            r[f"median_{k}"] = x[S.kl == k].median()
        rows.append(r)
    M = pd.DataFrame(rows).dropna(subset=["ruhig_kurz", "kurz_lang"])
    M["eff_ruhig_kurz"] = 2 * M.ruhig_kurz - 1; M["eff_kurz_lang"] = 2 * M.kurz_lang - 1
    M.round(3).to_csv(f"{B.RES}/breva_klassen_merkmale.csv", index=False)
    r_eff = np.corrcoef(M.eff_ruhig_kurz, M.eff_kurz_lang)[0, 1]
    strong = M[M.eff_ruhig_kurz.abs() >= 0.2]
    same = (np.sign(strong.eff_ruhig_kurz) == np.sign(strong.eff_kurz_lang)).mean() if len(strong) else np.nan
    eig = M[(M.eff_kurz_lang.abs() >= 0.15) & (M.eff_ruhig_kurz.abs() < 0.1)]
    cols = ["groesse", "im_modell", "ruhig_kurz", "kurz_lang", "median_ruhig", "median_grenzfall", "median_kurz", "median_lang"]
    md += ["\n## 2. Mehr Breva-Faktoren oder eigene Faktoren?\n",
           "AUC > 0,5: Größe ist in der zweiten Klasse höher; < 0,5: tiefer; 0,5: kein Unterschied.\n",
           f"- Korrelation der Wirkungen (ruhig→kurz gegen kurz→lang) über alle {len(M)} Größen: **{r_eff:.2f}**",
           f"- Von den {len(strong)} Größen, die Breva deutlich von ruhig trennen, zeigen {100 * same:.0f} % von kurz nach "
           "lang in dieselbe Richtung.",
           f"- Größen, die nur lang von kurz trennen (eigene Faktoren): {', '.join(eig.groesse) if len(eig) else 'keine'}\n",
           "Stärkste Trenner ruhig → kurz:", "```",
           M.reindex(M.eff_ruhig_kurz.abs().sort_values(ascending=False).index)[cols].head(15).round(2).to_string(index=False), "```",
           "Stärkste Trenner kurz → lang:", "```",
           M.reindex(M.eff_kurz_lang.abs().sort_values(ascending=False).index)[cols].head(15).round(2).to_string(index=False), "```"]
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6.5, 6))
        ax.scatter(M.eff_ruhig_kurz, M.eff_kurz_lang, s=18, c=np.where(M.im_modell, "#0b6e8a", "#bbbbbb"))
        for r in M[(M.eff_ruhig_kurz.abs() >= 0.3) | (M.eff_kurz_lang.abs() >= 0.15)].itertuples():
            ax.annotate(r.groesse, (r.eff_ruhig_kurz, r.eff_kurz_lang), fontsize=7)
        ax.axhline(0, color="grey", lw=0.6); ax.axvline(0, color="grey", lw=0.6)
        ax.set_xlabel("Wirkung ruhig → kurzer Breva (2·AUC − 1)"); ax.set_ylabel("Wirkung kurzer → langer Breva (2·AUC − 1)")
        ax.set_title(f"Gleiche Faktoren, nur stärker? r = {r_eff:.2f}\nblau = im Modell", fontsize=10)
        fig.tight_layout(); fig.savefig(f"{B.RES}/breva_klassen.png", dpi=110); plt.close(fig)
        md += ["![](breva_klassen.png)\n"]
    except Exception as e:
        print("Bild übersprungen:", e)

    # 3. Trainingsvarianten
    F = T.FEATS
    XE = FE.reindex(D.index)[F]
    okE = XE.notna().mean(axis=1) > 0.7
    leads = {L: B.features(B.load("prev", L, T.MODEL)).reindex(D.index).reindex(columns=F) for L in (1, 2, 3)}
    test_years = sorted(set(D.index[D.index.year > T.TRAIN_UNTIL].year))
    yb = D.breva.astype(int); yl = D.breva_lang.astype(int)
    stufe = yb + yl                       # 0 kein, 1 kurz, 2 lang
    grenz = (D.kl == "grenzfall")
    V = {"V0 ja/nein (bisher)": ("clf", yb, None, None),
         "V1 ohne Grenzfälle als nein": ("clf", yb, ~grenz, None),
         "V2 Grenzfälle halb gewichtet": ("clf", yb, None, np.where(grenz, 0.5, 1.0)),
         "V3 Stufen 0/1/2": ("reg", stufe, None, None),
         "V4 Stunden ≥ 14 kn": ("reg", D.breva_h.fillna(0).clip(upper=10), None, None),
         "nur lang (ja/nein)": ("clf", yl, None, None)}
    P = {}
    for name, (kind, yv, keep, w) in V.items():
        out = {L: pd.Series(np.nan, index=D.index) for L in leads}
        for yr in test_years:
            tr = okE & (D.index.year != yr) & yv.notna()
            if keep is not None:
                tr &= keep
            m = T.xgb_model(F) if kind == "clf" else xgb_reg(F)
            kw = {"sample_weight": pd.Series(w, index=D.index)[tr].values} if w is not None else {}
            m.fit(XE[tr], yv[tr], **kw)
            te = D.index.year == yr
            for L, XL in leads.items():
                g = te & (XL.notna().mean(axis=1) > 0.7)
                if g.any():
                    out[L][g] = m.predict_proba(XL[g])[:, 1] if kind == "clf" else m.predict(XL[g])
        P[name] = out
        print(" ", name, flush=True)
    rows = []
    for L in leads:
        base = P["V0 ja/nein (bisher)"][L]
        ok = base.notna() & D.index.month.isin(range(3, 11))
        days = D.index[ok]
        for name in V:
            p = P[name][L][ok].values
            r = dict(vorlauf=L, variante=name, tage=int(ok.sum()),
                     auc_breva=round(auc(yb[ok], p), 3), auc_lang=round(auc(yl[ok], p), 3),
                     auc_lang_unter_breva=round(auc(yl[ok & (yb == 1)], P[name][L][ok & (yb == 1)].values), 3))
            if name != "V0 ja/nein (bisher)":
                lo, hi = block_boot(yb[ok].values, p, base[ok].values, days)
                r["delta_breva"] = round(r["auc_breva"] - auc(yb[ok], base[ok]), 3); r["bereich_90"] = f"{lo:+.3f} … {hi:+.3f}"
            rows.append(r)
    R = pd.DataFrame(rows)
    R.to_csv(f"{B.RES}/breva_klassen_varianten.csv", index=False)
    md += ["\n## 3. Trainingsvarianten (7-Tage-Modell, echte Läufe 2024–heute, März–Oktober)\n",
           "auc_breva: Breva-Tag ja/nein; auc_lang: langer Breva gegen alle anderen Tage; auc_lang_unter_breva: nur "
           "unter den Breva-Tagen – erkennt die Variante, ob er lang wird? delta_breva/bereich_90: gegen V0, Bootstrap "
           "über Wochen (schließt der Bereich 0 aus, ist der Unterschied belastbar).\n", "```",
           R.to_string(index=False), "```"]
    open(f"{B.RES}/breva_klassen.md", "w").write("\n".join(md) + "\n")
    print("\n".join(md))
    print("\ngeschrieben: results/breva_klassen.md, breva_klassen_merkmale.csv, breva_klassen_varianten.csv, breva_klassen.png")


if __name__ == "__main__":
    main()
