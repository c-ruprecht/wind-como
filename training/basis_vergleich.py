"""Trainingsbasis ERA5 (25 km, ab 2014) oder ECMWF IFS 9 km (ab 2017)?

Je Testjahr ab 2024 (out-of-fold) wird das 7-Tage-Modell auf der Basis aller anderen Jahre trainiert und mit den
echten, archivierten Vorhersagen dieses Jahres gefüttert:
  - ecmwf_ifs025   Previous-Runs-Archiv 0.25° (bisheriger App-Eingang), Vorlauf 1–7
  - ecmwf_ifs00z   00-UTC-Läufe 9 km aus einzellaeufe.py (nach `einzellaeufe.py umformen`), Vorlauf 0–7
                   (Vorlauf 0 = Lauf vom selben Morgen, der Eingang für das Heute-Modell)
Basen: ERA5 ab 2014, ERA5 ab 2017 (gleich lang wie IFS – trennt „mehr Jahre“ von „feineres Raster“), IFS 9 km ab 2017,
und ERA5+IFS zusammen (beide Zeilen je Tag als eigene Fälle).
Alle Basen werden je Vorlauf auf genau denselben Tagen bewertet; Unterschied zu ERA5 mit Wochen-Bootstrap.

  python training/breva_daten.py wetter_ifs        (vorher, einmalig)
  python training/basis_vergleich.py               -> results/basis_vergleich.md / .csv
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402
import train_breva as T  # noqa: E402
from modell_vergleich import auc, block_boot  # noqa: E402

SOURCES = {"ecmwf_ifs025": range(1, 8), "ecmwf_ifs00z": range(0, 8)}
FIRST_TEST = 2024


def main(thr_list=(14, 18)):
    D = pd.read_csv(f"{B.RES}/breva_tage.csv", index_col=0, parse_dates=True)
    F = T.FEATS
    E5 = B.features(B.load("era5")).reindex(D.index).reindex(columns=F)
    HI = B.load("ifs9")
    if not HI:
        sys.exit("keine IFS-9-km-Daten – erst: python training/breva_daten.py wetter_ifs")
    I9 = B.features(HI).reindex(D.index).reindex(columns=F)
    ok5 = E5.notna().mean(axis=1) > 0.7; ok9 = I9.notna().mean(axis=1) > 0.7
    print(f"ERA5 {ok5.sum()} Tage ab {E5[ok5].index.min().date()}, IFS 9 km {ok9.sum()} Tage ab {I9[ok9].index.min().date()}")
    # Merkmale, die IFS 9 km gar nicht liefert
    miss = [c for c in F if I9[c].notna().mean() < 0.5]
    if miss:
        print("IFS 9 km ohne:", miss)
    X = {}
    for src, leads in SOURCES.items():
        for L in leads:
            H = B.load("prev", L, src)
            if not H or not any(len(h.columns) for h in H.values()):
                continue
            fx = B.features(H).reindex(D.index).reindex(columns=F)
            fx = fx[(fx.notna().mean(axis=1) > 0.7) & (fx.index.year >= FIRST_TEST)]
            if len(fx) > 100:
                X[(src, L)] = fx
    if not X:
        sys.exit("keine Vorhersagen ab 2024 gefunden")
    years = sorted({d.year for fx in X.values() for d in fx.index})
    rows, lines = [], ["# Trainingsbasis: ERA5 oder ECMWF IFS 9 km\n",
                       f"Out-of-fold je Testjahr {years[0]}–{years[-1]}, Ziel {T.OPT['ziel']}. Alle Basen je Zeile auf "
                       "denselben Tagen. Δ: Unterschied zu „ERA5 ab 2014“ (Wochen-Bootstrap, 90 %-Bereich).\n"]
    for thr in thr_list:
        y_all = T.target(D, thr)
        bases = {
            "ERA5 ab 2014": [(E5, ok5)],
            "ERA5 ab 2017": [(E5, ok5 & (D.index.year >= 2017))],
            "IFS 9 km ab 2017": [(I9, ok9)],
            "ERA5 + IFS 9 km": [(E5, ok5 & (D.index.year >= 2017)), (I9, ok9)],
        }
        M = {}
        for name, parts in bases.items():
            for yr in years:
                Xt = pd.concat([x[m & (D.index.year != yr)] for x, m in parts])
                yt = pd.concat([y_all[m & (D.index.year != yr)] for x, m in parts])
                M[(name, yr)] = T.xgb_model(F).fit(Xt, yt)
        for (src, L), fx in sorted(X.items()):
            c = fx.index
            y = y_all.loc[c].values; season = c.month.isin(range(3, 11))
            P = {}
            for name in bases:
                p = np.full(len(c), np.nan)
                for yr in years:
                    i = c.year == yr
                    if i.any():
                        p[i] = M[(name, yr)].predict_proba(fx[i])[:, 1]
                P[name] = p
            ref = P["ERA5 ab 2014"]
            for name, p in P.items():
                r = dict(schwelle=thr, quelle=src, vorlauf=L, basis=name, tage=len(c), breva=int(y.sum()),
                         auc=round(auc(y, p), 3), auc_saison=round(auc(y[season], p[season]), 3))
                if name != "ERA5 ab 2014":
                    lo, hi = block_boot(y, p, ref, c)
                    r["delta"] = round(auc(y, p) - auc(y, ref), 3); r["bereich_90"] = f"{lo:+.3f} … {hi:+.3f}"
                rows.append(r)
            print(f"  ≥{thr} {src} Vorlauf {L}: " + "  ".join(f"{k} {auc(y, v):.3f}" for k, v in P.items()), flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(f"{B.RES}/basis_vergleich.csv", index=False)
    for thr in thr_list:
        S = R[R.schwelle == thr]
        W = S.pivot_table(index=["quelle", "vorlauf"], columns="basis", values="auc").round(3)
        Dl = S[S.basis != "ERA5 ab 2014"][["quelle", "vorlauf", "basis", "delta", "bereich_90"]]
        lines += [f"\n## ≥ {thr} kn – AUC\n", "```", W.to_string(), "```",
                  "\nUnterschied zu ERA5 ab 2014:\n", "```", Dl.to_string(index=False), "```"]
    open(f"{B.RES}/basis_vergleich.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\ngeschrieben: results/basis_vergleich.md, results/basis_vergleich.csv")


if __name__ == "__main__":
    main()
