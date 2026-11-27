"""Die unsicheren Tage: Was unterscheidet Breva von Nicht-Breva, wenn das 7-Tage-Modell ~50 % sagt?

Grundlage: results/oof_7tage.csv (out-of-fold, echte Läufe 2024–heute). Band: geeichte Chance 35–65 %,
März–Oktober, Vorlauf 1 (zusätzlich 1–3 zusammen für mehr Fälle).

Je Kandidat die Trennschärfe innerhalb des Bandes (AUC, 0.5 = trennt nicht; Richtung egal, siehe „richtung“):
  A  Wetter, wie es war (ERA5): alle Größen aus breva_daten.features – auch die, die das Modell (noch) nicht nutzt.
     Hoch und nicht im Modell -> Kandidat für ein neues Merkmal.
  B  Vorhersagefehler (Lauf vom Vortag − ERA5) der Modellgrößen: hoch -> an diesen Tagen lag die Vorhersage daneben;
     helfen würde dann eine bessere Vorhersage (Ensemble), nicht ein besseres Modell.
  C  Vorhersagearchiv mit Höhenwerten (ab 2022, Lauf vom selben Tag): 850/700 hPa, Labilität.
  D  Gemessen (ARPA, falls arpa_extra gelaufen): Strahlung, Regen, Temperatur am Tag selbst.
  E  Ziel-Rauschen: wie viele Nicht-Breva-Tage im Band knapp verpasst haben (1 h, 12–14 kn) und wie viele
     Breva-Tage nur knapp gezählt wurden (genau 2 h).

  python training/unsichere_tage.py   -> results/unsichere_tage.md, results/unsichere_tage.csv, results/unsichere_tage.png
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402
import train_breva as T  # noqa: E402

LO, HI = 0.35, 0.65


def auc(y, x):
    from scipy.stats import mannwhitneyu
    ok = np.isfinite(x)
    y, x = np.asarray(y)[ok], np.asarray(x)[ok]
    if len(set(y)) < 2 or ok.sum() < 30 or np.nanstd(x) == 0:
        return np.nan, np.nan, int(ok.sum())
    u, p = mannwhitneyu(x[y == 1], x[y == 0], alternative="two-sided")
    return u / ((y == 1).sum() * (y == 0).sum()), p, int(ok.sum())


def table(XF, days, y, days_all, y_all, label, in_model=None):
    """XF: Größen für alle Tage; days/y: Band; days_all/y_all: alle Tage (Vergleich)"""
    rows = []
    X = XF.reindex(days)
    for c in X.columns:
        a, p, n = auc(y, X[c].values)
        if np.isnan(a):
            continue
        aa = auc(y_all, XF[c].reindex(days_all).values)[0]
        rows.append(dict(gruppe=label, groesse=c, im_modell=(c in in_model) if in_model is not None else "",
                         n=n, auc_band=round(max(a, 1 - a), 3), richtung="Breva höher" if a >= 0.5 else "Breva tiefer",
                         p=p, auc_alle=round(max(aa, 1 - aa), 3) if np.isfinite(aa) else np.nan,
                         median_breva=round(float(np.nanmedian(X[c][y == 1])), 2),
                         median_kein=round(float(np.nanmedian(X[c][y == 0])), 2)))
    return pd.DataFrame(rows)


def main():
    O = pd.read_csv(f"{B.RES}/oof_7tage.csv", parse_dates=["tag"])
    O = O[(O.schwelle == 14) & O.tag.dt.month.between(3, 10)]
    D = pd.read_csv(f"{B.RES}/breva_tage.csv", index_col=0, parse_dates=True)
    o1 = O[O.vorlauf == 1].set_index("tag")
    band = o1[(o1.p >= LO) & (o1.p <= HI)]
    days, y = band.index, band.y.values
    alle = o1.index
    md = ["# Die unsicheren Tage\n",
          f"7-Tage-Modell, Vorlauf 1, März–Oktober 2024–heute: {len(o1)} Tage, davon {len(band)} mit geeichter Chance "
          f"{100 * LO:.0f}–{100 * HI:.0f} % ({int(y.sum())} Breva, {int((1 - y).sum())} kein Breva).\n",
          "auc_band: wie gut die Größe innerhalb des Bandes Breva von Nicht-Breva trennt (0,5 = gar nicht). "
          "auc_alle: dieselbe Größe über alle Tage. p: Mann-Whitney (bei ~150 Tagen und vielen Größen ist p < 0,01 "
          "ein Hinweis, kein Beweis).\n"]
    R = []
    # A: ERA5
    FE = B.features(B.load("era5"))
    R.append(table(FE, days, y, alle, o1.y.values, "A ERA5 (Wetter wie es war)", set(T.FEATS)))
    # B: Vorhersagefehler Vorlauf 1
    L1 = B.features(B.load("prev", 1, T.MODEL))
    common = [c for c in T.FEATS if c in L1 and c in FE]
    ERR = (L1[common] - FE[common]).add_suffix("_fehler")
    R.append(table(ERR, days, y, alle, o1.y.values, "B Vorhersagefehler Vortag (Lauf − ERA5)"))
    # Vorhersage selbst (was das Modell sah) – zum Vergleich
    R.append(table(L1[common].add_suffix("_vorhersage"), days, y, alle, o1.y.values, "B' Vorhersage Vortag"))
    # C: Archiv mit Höhenwerten
    try:
        HA = B.load("archiv", model="ecmwf_ifs025")
        if not HA:
            HA = B.load("archiv")
        if HA:
            FA = B.features(HA)
            new = [c for c in FA.columns if c not in FE.columns or c.startswith(("t850", "t700", "rh", "wind850", "wind700", "lifted"))]
            R.append(table(FA[new].add_suffix("_archiv"), days, y, alle, o1.y.values, "C Vorhersagearchiv (ab 2022)"))
    except Exception as e:
        print("Archiv übersprungen:", e)
    # D: ARPA gemessen
    f = os.path.join(B.DATA, "arpa", "messungen_stunde.csv")
    if os.path.exists(f):
        M = pd.read_csv(f, parse_dates=["time"]).set_index("time")
        M.index = pd.DatetimeIndex(M.index).tz_convert(B.TZ).tz_localize(None) if M.index.tz is not None else M.index.tz_localize("UTC").tz_convert(B.TZ).tz_localize(None)
        h = M.index.hour; d = M.index.normalize()
        G = {}
        for c in M.columns:
            k = c.split("_")[-1]
            if k == "rad":
                G[f"{c}_9_17"] = M[c][(h >= 9) & (h <= 17)].groupby(d[(h >= 9) & (h <= 17)]).mean()
            elif k == "rain":
                G[f"{c}_11_19"] = M[c][(h >= 11) & (h <= 19)].groupby(d[(h >= 11) & (h <= 19)]).sum()
            elif k == "temp":
                G[f"{c}_max"] = M[c][(h >= 12) & (h <= 17)].groupby(d[(h >= 12) & (h <= 17)]).max()
            elif k == "rh":
                G[f"{c}_13"] = M[c][h == 13].groupby(d[h == 13]).mean()
        G = pd.DataFrame(G)
        for a_, b_ in (("milano", "chiavenna"), ("milano", "sondrio"), ("bergamo", "sondrio")):
            if f"{a_}_temp_max" in G and f"{b_}_temp_max" in G:
                G[f"dt_{b_}_{a_}_gemessen"] = G[f"{b_}_temp_max"] - G[f"{a_}_temp_max"]
        R.append(table(G, days, y, alle, o1.y.values, "D ARPA gemessen"))
    else:
        md.append("(ARPA-Zusatzmessungen fehlen – python training/arpa_extra.py)\n")
    R = pd.concat(R, ignore_index=True)
    R = R.sort_values("auc_band", ascending=False)
    R.round(4).to_csv(f"{B.RES}/unsichere_tage.csv", index=False)
    cols = ["groesse", "im_modell", "n", "auc_band", "richtung", "p", "auc_alle", "median_breva", "median_kein"]
    pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 40)
    for g, x in R.groupby("gruppe", sort=True):
        md += [f"\n## {g}\n", "```", x[cols].head(15).assign(p=lambda z: z.p.map(lambda v: f"{v:.3f}")).to_string(index=False), "```"]
    # E: Ziel-Rauschen
    Db = D.reindex(days)
    if "breva_lauf" in Db:
        knapp_nein = ((Db.breva == 0) & ((Db.breva_lauf == 1) | (Db.see_max_stunde.between(12, 14)))).sum()
        knapp_ja = ((Db.breva == 1) & (Db.breva_lauf == 2)).sum()
        morgen = ((Db.breva == 0) & (Db.breva_lauf >= 2)).sum()
        md += ["\n## E Ziel-Rauschen im Band\n",
               f"- Nicht-Breva-Tage, die knapp verpasst haben (nur 1 h ≥ 14 kn oder Maximum 12–14 kn): {knapp_nein} von {int((1 - y).sum())}",
               f"- Nicht-Breva-Tage mit ≥ 2 h ≥ 14 kn, die nur an Morgen- oder Nordwindregel scheiterten: {morgen}",
               f"- Breva-Tage mit genau 2 h (knapp gezählt): {knapp_ja} von {int(y.sum())}",
               f"- Mittlere Breva-Dauer im Band: {Db[Db.breva == 1].breva_h.mean():.1f} h (alle Breva-Tage: "
               f"{D[(D.breva == 1) & D.index.month.isin(range(3, 11))].breva_h.mean():.1f} h)"]
    # Bild: die 8 stärksten Größen außerhalb des Modells + Vorhersagefehler
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        src = {"A ERA5 (Wetter wie es war)": FE, "B Vorhersagefehler Vortag (Lauf − ERA5)": ERR}
        top = R[R.gruppe.isin(src) & (R.p < 0.05)].head(8)
        if len(top):
            fig, axs = plt.subplots(2, 4, figsize=(13, 6)); axs = axs.ravel()
            for ax, r in zip(axs, top.itertuples()):
                x = src[r.gruppe][r.groesse].reindex(days).values
                ax.boxplot([x[(y == 0) & np.isfinite(x)], x[(y == 1) & np.isfinite(x)]], labels=["kein Breva", "Breva"])
                ax.set_title(f"{r.groesse}\nAUC {r.auc_band:.2f}{' (im Modell)' if r.im_modell is True else ''}", fontsize=9)
            for ax in axs[len(top):]:
                ax.axis("off")
            fig.suptitle(f"Unsichere Tage (Chance {100 * LO:.0f}–{100 * HI:.0f} %, Vorlauf 1, März–Oktober)", fontsize=11)
            fig.tight_layout(); fig.savefig(f"{B.RES}/unsichere_tage.png", dpi=105); plt.close(fig)
            md += ["\n![](unsichere_tage.png)"]
    except Exception as e:
        print("Bild übersprungen:", e)
    open(f"{B.RES}/unsichere_tage.md", "w").write("\n".join(md) + "\n")
    print("\n".join(md))
    print("\ngeschrieben: results/unsichere_tage.md/.csv/.png")


if __name__ == "__main__":
    main()
