"""Tivano und Breva: Folgt auf einen sauberen Tivano am Morgen ein sauberer Breva?

Physik: Beide sind Teil derselben Tal-Zirkulation. Nachts kühlen die Täler aus, die Luft fließt als Tivano zum See
(Nord); tagsüber heizen sie auf, die Luft strömt als Breva zurück (Süd). Ein klarer Tivano zeigt eine ruhige,
strahlungsreiche Lage – ein Nordwind aus einer Föhnlage dagegen eine Störung.

Morgen-Klassen (Stationen, alle Tage 2014–heute):
  tivano     Colico Nordwind 6–10 Uhr mind. 2 h ≥ T kn (T aus sat_morgen: bestes Kappa mit dem Satelliten),
             KEINE Föhnlage: Zürich − Mailand < FOEHN hPa (ERA5, 12 Uhr)
  nordfoehn  Nordwind am Morgen UND Föhnlage
  kein       sonst
Achtung Zirkel: Das Breva-Ziel schließt Tage mit Morgenwind aus anderer Richtung (Samolaco 6–10 Uhr ≥ 6 kn) und mit
Nordwind am Nachmittag aus. Ein kräftiger Tivano kann den Breva-Tag also per Definition verhindern. Deshalb zusätzlich
„breva_roh“: ≥ 2 h ≥ 14 kn am Nachmittag, ohne Morgen- und Nordwindregel.
1. Breva-Häufigkeit, langer Breva, Breva-Stunden je Klasse und Monat (März–Oktober).
2. Nur Schönwetter (Sonne im Tal über dem Monatsmedian, kein Regen): bleibt der Unterschied?
3. Bringt der Tivano etwas über das Wetter hinaus? Breva-Chance aus ERA5 (je Jahr out-of-fold) in Zehnteln,
   je Zehntel Breva-Anteil mit und ohne Tivano; und ein Modell mit dem gemessenen Tivano als zusätzlicher Größe
   (das ginge im Heute-Modell ab 9/11 Uhr). Bootstrap über Wochen für den AUC-Unterschied.
4. Satellit: Morgenbilder (sat_morgen) – Breva am Abend nach nordwind- gegen ruhige Morgen.

  python training/tivano_breva.py   -> results/tivano_breva.md, results/tivano_breva.png
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402

FOEHN = 4.0                       # hPa Zürich − Mailand (12 Uhr): ab hier Nordföhn-Lage
T_DEFAULT = 3                     # kn Colico, falls sat_morgen noch nicht gelaufen
SAISON = range(3, 11)


def north_hours(st, nord, T):
    f = os.path.join(B.DATA, "arpa", f"{st}_wind.csv")
    x = pd.read_csv(f, parse_dates=["time"]).set_index("time")
    x.index = pd.DatetimeIndex(x.index).tz_convert(B.TZ).tz_localize(None)
    x = x[~x.index.duplicated(keep="first")]
    a, b = nord
    ins = ((x.dir >= a) | (x.dir <= b)) if a > b else ((x.dir >= a) & (x.dir <= b))
    h = x.index.hour; m = (h >= 6) & (h <= 10)
    v = x[m]; n = v.groupby(v.index.normalize()).size()
    hrs = ((v.kn >= T) & ins[m]).groupby(v.index.normalize()).sum()
    return hrs[n >= 3]


def main():
    from sklearn.metrics import roc_auc_score
    D = pd.read_csv(f"{B.RES}/breva_tage.csv", index_col=0, parse_dates=True)
    T = T_DEFAULT
    fz = f"{B.RES}/sat_morgen/vorhersage.md"
    if os.path.exists(fz):
        import re
        m = re.search(r"Gewählt: (\w+), T = (\d+) kn", open(fz).read())
        if m and m.group(1) == "colico":
            T = int(m.group(2))
    hrs = north_hours("colico", (330, 100), T)
    FE = B.features(B.load("era5"))
    dz = FE["dp_zurich_milano_12"].reindex(D.index)
    D["nachm_nord"] = (D.sam_nord_std.fillna(0) >= 2).astype(int)       # Nordwind auch am Nachmittag
    D["breva_roh"] = (D.breva_lauf >= 2).astype(int)                    # ohne Morgen- und Nordwindregel
    D["von_regel_gestrichen"] = ((D.breva_roh == 1) & (D.breva == 0)).astype(int)
    nw = (hrs.reindex(D.index) >= 2)
    known = hrs.reindex(D.index).notna()
    kl = pd.Series("kein", index=D.index)
    kl[nw & (dz >= FOEHN)] = "nordfoehn"
    kl[nw & (dz < FOEHN)] = "tivano"
    D["morgen"] = kl.where(known)
    S = D[D.index.month.isin(SAISON) & D.morgen.notna()].copy()
    md = ["# Tivano und Breva\n",
          f"Tivano = Colico Nordwind 6–10 Uhr mind. 2 h ≥ {T} kn, ohne Föhnlage (Zürich − Mailand < {FOEHN} hPa) und ohne "
          f"Nordwind am Nachmittag. März–Oktober {S.index.year.min()}–{S.index.year.max()}, {len(S)} Tage.\n",
          "## 1. Breva nach der Art des Morgens\n", "```",
          S.groupby("morgen").agg(tage=("breva", "size"), breva=("breva", "mean"), breva_roh=("breva_roh", "mean"),
                                  von_regel_gestrichen=("von_regel_gestrichen", "mean"), lang=("breva_lang", "mean"),
                                  stunden=("breva_h", "mean"), see_max=("see_max_stunde", "median"),
                                  nachm_nord=("nachm_nord", "mean")).round(2).to_string(), "```",
          "breva_roh: Breva am Nachmittag ohne Morgen-/Nordwindregel; von_regel_gestrichen: Anteil Tage, die nur wegen "
          "dieser Regeln nicht als Breva-Tag zählen; nachm_nord: Nordwind auch am Nachmittag."]
    M = S.groupby([S.index.month, "morgen"]).breva.mean().unstack().round(2)
    M["tage_tivano"] = S[S.morgen == "tivano"].groupby(S[S.morgen == "tivano"].index.month).size()
    md += ["\nBreva-Anteil je Monat:\n", "```", M.to_string(), "```"]

    # 2. nur Schönwetter
    rad = FE["rad_chiavenna"].reindex(S.index); regen = FE["regen_see"].reindex(S.index)
    med = rad.groupby(S.index.month).transform("median")
    sw = (rad >= med) & (regen < 0.5)
    G = S[sw]
    md += ["\n## 2. Nur Schönwetter (Sonne im Tal über dem Monatsmedian, kein Regen)\n", "```",
           G.groupby("morgen").agg(tage=("breva", "size"), breva=("breva", "mean"), breva_roh=("breva_roh", "mean"), lang=("breva_lang", "mean"),
                                   stunden=("breva_h", "mean")).round(2).to_string(), "```"]

    # 3. über das Wetter hinaus?
    import train_breva as TB
    from modell_vergleich import block_boot
    F = TB.FEATS
    X = FE.reindex(D.index)[F]
    y = D.breva.astype(int)
    ok = X.notna().mean(axis=1) > 0.7
    tiv = (D.morgen == "tivano").astype(float).where(D.morgen.notna())
    tivh = hrs.reindex(D.index)
    X2 = X.assign(tivano_morgen=tiv, tivano_stunden=tivh)
    P1 = pd.Series(np.nan, index=D.index); P2 = P1.copy()
    for yr in sorted(set(D.index.year)):
        tr = ok & (D.index.year != yr); te = ok & (D.index.year == yr)
        if te.sum() < 30:
            continue
        P1[te] = TB.xgb_model(F).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
        f2 = F + ["tivano_morgen", "tivano_stunden"]
        P2[te] = TB.xgb_model(f2).fit(X2.loc[tr, f2], y[tr]).predict_proba(X2.loc[te, f2])[:, 1]
    g = P1.notna() & P2.notna() & D.index.month.isin(SAISON) & D.morgen.notna()
    a1, a2 = roc_auc_score(y[g], P1[g]), roc_auc_score(y[g], P2[g])
    lo, hi = block_boot(y[g].values, P2[g].values, P1[g].values, D.index[g])
    Z = pd.DataFrame({"p": P1[g], "y": y[g], "morgen": D.morgen[g]})
    Z["zehntel"] = pd.qcut(Z.p, 10, labels=False, duplicates="drop")
    Q = Z.groupby(["zehntel", "morgen"]).y.agg(["mean", "size"]).unstack().round(2)
    Q.insert(0, "p_mittel", Z.groupby("zehntel").p.mean().round(2))
    md += ["\n## 3. Bringt der Tivano etwas über das Wetter hinaus?\n",
           "Breva-Chance aus dem Wetter (ERA5, je Jahr out-of-fold) in Zehnteln; je Zehntel der tatsächliche Breva-Anteil "
           "nach der Art des Morgens (mean) und die Zahl der Tage (size):\n", "```", Q.to_string(), "```",
           f"\nModell nur Wetter: AUC {a1:.3f}; mit gemessenem Tivano am Morgen: {a2:.3f} "
           f"(Unterschied {a2 - a1:+.3f}, 90 % Bereich {lo:+.3f} … {hi:+.3f}; März–Oktober, {int(g.sum())} Tage).",
           "Ist der Unterschied belastbar, gehört der Tivano ins Heute-Modell (ab 9/11 Uhr gemessen); das 7-Tage-Modell "
           "kann ihn nur über eine Tivano-Vorhersage nutzen."]

    # 4. Satellit
    fm = f"{B.RES}/sat_morgen/morgen.csv"
    if os.path.exists(fm):
        Mo = pd.read_csv(fm, index_col=0, parse_dates=True)
        Mo = Mo[Mo.index.month.isin(SAISON)].join(D[["breva", "breva_lang", "breva_h"]], how="inner")
        md += ["\n## 4. Satellit am Morgen → Breva am Nachmittag (oberer See)\n", "```",
               Mo.groupby("klasse").agg(bilder=("breva", "size"), breva=("breva", "mean"), lang=("breva_lang", "mean"),
                                        stunden=("breva_h", "mean")).round(2).to_string(), "```"]
    # Bild
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, axs = plt.subplots(1, 2, figsize=(11, 4))
        cols = {"tivano": "#00829b", "kein": "#9aa7ad", "nordfoehn": "#d9711c"}
        for ax, (title, X_) in zip(axs, (("all days", S), ("fair weather only", G))):
            T_ = X_.groupby([X_.index.month, "morgen"]).breva.mean().unstack()
            w = 0.27
            for i, k in enumerate(["kein", "tivano", "nordfoehn"]):
                if k in T_:
                    ax.bar(T_.index + (i - 1) * w, T_[k], width=w, color=cols[k], label=k)
            ax.set_xticks(list(SAISON)); ax.set_ylim(0, 1); ax.grid(alpha=0.3, axis="y")
            ax.set_title(f"Share of Breva days by morning type – {title}", fontsize=9); ax.set_xlabel("month")
        axs[0].set_ylabel("share of Breva days"); axs[0].legend(fontsize=8)
        fig.tight_layout(); fig.savefig(f"{B.RES}/tivano_breva.png", dpi=100); plt.close(fig)
        md += ["\n![](tivano_breva.png)"]
    except Exception as e:
        print("Bild übersprungen:", e)
    open(f"{B.RES}/tivano_breva.md", "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
