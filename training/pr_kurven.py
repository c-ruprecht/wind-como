"""Precision-Recall-Kurven: 7-Tage-Modell (Vorlauf 1–7) und Jetzt-Modell (9, 11, 13, 15 Uhr).

Grundlage sind die out-of-fold-Vorhersagen der Prüfung 2024–heute (echte Läufe, Modell ohne das jeweilige Jahr):
  results/oof_7tage.csv                 aus train_breva.py
  results/oof_jetzt_<lauf>.csv          aus train_jetzt.py (Stufe „A + ARPA-Treiber“, wenn vorhanden)

Präzision: Anteil der Tage mit „Breva vorhergesagt“, an denen wirklich Breva kam.
Recall (Trefferquote): Anteil aller Breva-Tage, die vorhergesagt wurden.
Waagerechte Linie: Anteil der Breva-Tage (so gut ist Raten). Punkte: Breva-Call (≥ 80 % Präzision).

  python training/pr_kurven.py [--lauf ecmwf_ifs00z] [--saison]
-> results/pr_7tage.png, results/pr_jetzt.png, results/pr_kurven.md
"""
import argparse, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402

TARGET = 0.8


def pr(y, p):
    from sklearn.metrics import average_precision_score, precision_recall_curve
    y = np.asarray(y, int); p = np.asarray(p, float)
    prec, rec, thr = precision_recall_curve(y, p)
    return prec, rec, thr, average_precision_score(y, p)


def at_precision(prec, rec, thr, target=TARGET, min_calls=8, n=None, y=None, p=None):
    """größter Recall bei Präzision ≥ target (mit mindestens min_calls Calls)"""
    best = None
    for P, R, t in zip(prec[:-1], rec[:-1], thr):
        if P >= target and (p is None or (p >= t).sum() >= min_calls):
            if best is None or R > best[1]:
                best = (P, R, t)
    return best


def plot(groups, title, path, label):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from matplotlib import cm
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    rows = []
    for ax, thr in zip(axs, (14, 18)):
        G = groups[thr]
        cols = cm.viridis(np.linspace(0.05, 0.9, len(G)))
        for c, (k, (y, p)) in zip(cols, G.items()):
            if len(set(y)) < 2:
                continue
            prec, rec, t, ap = pr(y, p)
            ax.plot(rec, prec, color=c, lw=1.8, label=f"{label(k)}  (AP {ap:.2f})")
            b = at_precision(prec, rec, t, p=np.asarray(p))
            if b:
                ax.plot(b[1], b[0], "o", color=c, ms=6, mec="black", mew=0.6)
            for P0 in (0.6, 0.7, 0.8):
                bb = at_precision(prec, rec, t, P0, p=np.asarray(p))
                rows.append(dict(schwelle=thr, wann=label(k), tage=len(y), breva=int(np.sum(y)),
                                 anteil=round(float(np.mean(y)), 3), ap=round(ap, 3), praezision_ziel=P0,
                                 recall=round(bb[1], 3) if bb else np.nan, ab_chance=round(float(bb[2]), 3) if bb else np.nan))
        base = np.mean(np.concatenate([np.asarray(v[0]) for v in G.values()]))
        ax.axhline(base, color="grey", ls=":", lw=1)
        ax.axhline(TARGET, color="#d1495b", ls="--", lw=0.8)
        ax.set_title(f"≥ {thr} kn", fontsize=11); ax.set_xlabel("Recall (Anteil erwischter Breva-Tage)")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1.02); ax.grid(alpha=0.25); ax.legend(fontsize=8, loc="lower left", framealpha=0.9)
    axs[0].set_ylabel("Präzision (Anteil richtiger Calls)")
    fig.suptitle(title, fontsize=11)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    return pd.DataFrame(rows)


def main(lauf, saison):
    md = ["# Precision-Recall\n", "Out-of-fold-Vorhersagen 2024–heute mit echten Läufen. AP = Average Precision "
          "(Fläche unter der Kurve). Tabelle: größter Recall, bei dem die Präzision mindestens 60/70/80 % ist, "
          "und ab welcher (geeichten) Chance.", "Nur März–Oktober.\n" if saison else "Ganzes Jahr.\n"]
    if os.path.exists(f"{B.RES}/pr_kurven.csv"):
        os.remove(f"{B.RES}/pr_kurven.csv")
    f7 = f"{B.RES}/oof_7tage.csv"
    if os.path.exists(f7):
        O = pd.read_csv(f7, parse_dates=["tag"])
        if saison:
            O = O[O.tag.dt.month.between(3, 10)]
        g = {thr: {L: (x.y.values, x.p.values) for L, x in O[O.schwelle == thr].groupby("vorlauf")} for thr in (14, 18)}
        R = plot(g, "7-Tage-Modell: Precision-Recall je Vorlauf", f"{B.RES}/pr_7tage.png", lambda L: f"Tag {L}")
        R.assign(modell="7tage").to_csv(f"{B.RES}/pr_kurven.csv", index=False)
        md += ["## 7-Tage-Modell\n", "![](pr_7tage.png)\n", "```", R.pivot_table(index=["schwelle", "wann", "ap", "anteil"],
               columns="praezision_ziel", values="recall").to_string(), "```\n"]
    else:
        print("fehlt:", f7, "– erst train_breva.py")
    fj = f"{B.RES}/oof_jetzt_{lauf}.csv"
    if os.path.exists(fj):
        J = pd.read_csv(fj, parse_dates=["tag"])
        stufe = "A + ARPA-Treiber" if (J.stufe == "A + ARPA-Treiber").any() else "W + Wind"
        J = J[(J.stufe == stufe) & J.stunde.isin([9, 11, 13, 15])]
        if saison:
            J = J[J.tag.dt.month.between(3, 10)]
        g = {thr: {h: (x.y.values, x.p.values) for h, x in J[J.schwelle == thr].groupby("stunde")} for thr in (14, 18)}
        R = plot(g, f"Jetzt-Modell ({stufe}, {lauf}): kommt nach dieser Stunde noch ≥ 2 h Breva?",
                 f"{B.RES}/pr_jetzt.png", lambda h: f"{int(h):02d} Uhr")
        R.assign(modell=f"jetzt {lauf}").to_csv(f"{B.RES}/pr_kurven.csv", index=False, mode="a",
                                                 header=not os.path.exists(f"{B.RES}/pr_kurven.csv"))
        md += [f"## Jetzt-Modell ({stufe}, Lauf {lauf})\n", "![](pr_jetzt.png)\n", "Ungeeichte Modellausgabe; "
               "„ab_chance“ in pr_kurven.csv ist daher die Rohschwelle.\n", "```",
               R.pivot_table(index=["schwelle", "wann", "ap", "anteil"], columns="praezision_ziel", values="recall").to_string(), "```\n"]
    else:
        print("fehlt:", fj, "– erst train_jetzt.py" + (f" --lauf {lauf}" if lauf != "ecmwf_ifs025" else ""))
    open(f"{B.RES}/pr_kurven.md", "w").write("\n".join(md) + "\n")
    print("\n".join(md))
    print("geschrieben: results/pr_7tage.png, results/pr_jetzt.png, results/pr_kurven.md")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lauf", default="ecmwf_ifs00z")
    ap.add_argument("--saison", action="store_true", help="nur März–Oktober")
    a = ap.parse_args()
    main(a.lauf, a.saison)
