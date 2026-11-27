"""Auswertung der Satellitenprüfung (nach sat_pruefung.py): Ursachen der Fehlalarme (FP) und verpassten Tage (FN),
und ob ein anderes Ziel besser zum Satelliten passt.

1. Ursache je Fall (Regeln, nachvollziehbar in der Liste):
   FP – Modell sagt Breva, Ziel nein
     ziel_verpasst_morgen   Satellit Süd ≥ 14 kn, Samolaco morgens ≥ 6 kn, aber aus Breva-Richtung (früher Breva)
     ziel_verpasst_knapp    Satellit Süd ≥ 14 kn, Samolaco × Faktor knapp darunter (11–14 kn)
     ziel_verpasst_kurz     Satellit Süd ≥ 14 kn, Samolaco × Faktor ≥ 14 kn, aber keine 2 h am Stück
     grenzfall_10_14        Satellit Süd 10–14 kn: schwacher Breva, Ziel ≥ 14 kn knapp verfehlt
     ziel_verpasst_sonst    Satellit Süd ≥ 14 kn, anderer Grund
     breva_frueh_vorbei     Satellit < 10 kn, Samolaco nachmittags ≥ 10 kn (× Faktor), um 19 Uhr abgeflaut
     nordwind               Satellit aus Nord / Samolaco mit Nordwind-Stunden – Modell falsch (Föhnlage)
     gewitter               Satellit ≥ 25 kn auf dem ganzen See und Regen – Bild unbrauchbar
     echt_falsch            schwacher oder kein Breva laut Stationen und Satellit
   FN – Modell nein, Ziel ja
     satellit_bestaetigt    Satellit Süd ≥ 10 kn: Breva war da, das Modell hat ihn übersehen
     abends_vorbei          Satellit < 10 kn, Breva vor dem Überflug abgeflaut
     (zusätzlich: Föhnindex Zürich–Mailand, Regen – was das Modell vermutlich abgeschreckt hat)
2. Ziel-Varianten gegen den Satelliten (alle Abende März–Oktober, Satellit Süd ≥ 14 kn = „Breva laut Satellit“):
     B           wie bisher (Samolaco × Faktor ≥ 14 kn 2 h, morgens < 6 kn, < 2 h Nordwind)
     B_morgen    Morgenregel zählt nur Wind, der nicht aus Breva-Richtung kommt
     B_zwei      Seewind = Mittel aus Samolaco und Colico (je × eigenem Faktor), mit B_morgen-Regel
     B_eine      Samolaco ODER Colico erreicht die Schwelle 2 h, mit B_morgen-Regel
   Kennzahlen: Übereinstimmung, Präzision/Recall gegen den Satelliten, Kappa.

  python training/sat_analyse.py   -> results/sat_analyse.md, results/sat_pruefung/ursachen.csv
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402
import train_heute as TH  # noqa: E402

SECTOR = {"samolaco": (112, 202), "colico": (200, 315)}
NORTH = lambda d: (d >= 315) | (d <= 45)  # noqa: E731


def run2(mask):
    best = cur = 0
    for m in mask:
        cur = cur + 1 if m else 0; best = max(best, cur)
    return best


def daily(O, days, f_s, f_c, thr=14):
    rows = []
    s, c = O["samolaco"], O["colico"]
    for d in days:
        a = s.loc[d + pd.Timedelta(hours=6): d + pd.Timedelta(hours=10)]
        aft_s = s.loc[d + pd.Timedelta(hours=11): d + pd.Timedelta(hours=20)]
        aft_c = c.loc[d + pd.Timedelta(hours=11): d + pd.Timedelta(hours=20)]
        if len(aft_s) < 8:
            continue
        ins = lambda x, st: (x.dir >= SECTOR[st][0]) & (x.dir <= SECTOR[st][1])  # noqa: E731
        ls = (aft_s.kn * f_s).where(ins(aft_s, "samolaco"), 0)
        lc = (aft_c.kn * f_c).where(ins(aft_c, "colico"), 0).reindex(ls.index)
        both = pd.concat([ls, lc], axis=1).mean(axis=1)
        either = pd.concat([ls, lc], axis=1).max(axis=1)
        mor_non = a.kn.where(~ins(a, "samolaco"), 0).mean() if len(a) else np.nan
        rows.append(dict(tag=d, morgen_alle=a.kn.mean() if len(a) else np.nan, morgen_nicht_breva=mor_non,
                         morgen_breva_anteil=float(ins(a, "samolaco").mean()) if len(a) else np.nan,
                         nord_std=int((NORTH(aft_s.dir) & (aft_s.kn >= 8)).sum()),
                         run_s=run2(ls >= thr), run_both=run2(both >= thr), run_either=run2(either >= thr),
                         max_s=float(ls.max()), max_c=float(lc.max()) if lc.notna().any() else np.nan))
    return pd.DataFrame(rows).set_index("tag")


def kappa(a, b):
    a = np.asarray(a, bool); b = np.asarray(b, bool)
    po = (a == b).mean(); pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return (po - pe) / (1 - pe) if pe < 1 else np.nan


def main():
    L = pd.read_csv(f"{B.RES}/sat_pruefung/liste.csv", index_col=0, parse_dates=True)
    if "sat_richtung" not in L:
        print("Hinweis: liste.csv ohne sat_richtung (ältere sat_pruefung) – alle Bilder als Süd angenommen")
        L["sat_richtung"] = 200.0
    D = pd.read_csv(f"{B.RES}/breva_tage.csv", index_col=0, parse_dates=True)
    O = TH.hourly_obs()
    # Faktoren aus sauberen Breva-Abenden: Satellit / Nachmittagsmaximum der Station
    sud = L.sat_richtung == 200
    Dd = daily(O, L.index, 1.0, 1.0)
    J = L.join(Dd, how="inner")
    clean = sud & (J.see >= 10) & (J.regen.fillna(0) < 1) & (J.morgen_alle < 6)
    f_s = float((J.see / J.max_s.clip(lower=1))[clean].median())
    f_c = float((J.see / J.max_c.clip(lower=1))[clean].median())
    print(f"Faktoren See/Station (n={int(clean.sum())} saubere Abende): Samolaco {f_s:.2f}, Colico {f_c:.2f}")
    Dd = daily(O, L.index, f_s, f_c)
    J = L.join(Dd, how="inner")
    sat_sued = J.sat_richtung == 200
    sat_breva = sat_sued & (J.see >= 14)

    # 1. Ursachen
    cause = pd.Series("", index=J.index)
    fp = J.fall == "fp"; fn = J.fall == "fn"
    gew = (J.see >= 25) & (J.regen.fillna(0) >= 2)
    nordw = (~sat_sued) | (J.nord_std >= 2)
    cause[fp & gew] = "gewitter"
    cause[fp & (cause == "") & nordw & ~sat_breva] = "nordwind"
    cause[fp & (cause == "") & sat_breva & (J.morgen_alle >= 6) & (J.morgen_nicht_breva < 6)] = "ziel_verpasst_morgen"
    cause[fp & (cause == "") & sat_breva & J.max_s.between(11, 14)] = "ziel_verpasst_knapp"
    cause[fp & (cause == "") & sat_breva & (J.max_s >= 14) & (J.run_s < 2)] = "ziel_verpasst_kurz"
    cause[fp & (cause == "") & sat_breva] = "ziel_verpasst_sonst"
    cause[fp & (cause == "") & sat_sued & (J.see >= 10)] = "grenzfall_10_14"
    cause[fp & (cause == "") & (J.see < 10) & (J.max_s >= 10)] = "breva_frueh_vorbei"
    cause[fp & (cause == "")] = "echt_falsch"
    cause[fn & sat_sued & (J.see >= 10)] = "satellit_bestaetigt"
    cause[fn & (cause == "")] = "abends_vorbei"
    J["ursache"] = cause
    E = B.features(B.load("era5")).reindex(J.index) if B.load("era5") else pd.DataFrame(index=J.index)
    for c in ("dp_zurich_milano_12", "regen_see", "rad_chiavenna", "dp_po_tal_15"):
        J[c] = E[c] if c in E else np.nan
    os.makedirs(f"{B.RES}/sat_pruefung", exist_ok=True)
    cols = ["zeit", "fall", "ursache", "p", "y", "klasse", "see", "sat_richtung", "morgen_alle", "morgen_nicht_breva",
            "nord_std", "max_s", "max_c", "run_s", "run_both", "run_either", "regen", "dp_zurich_milano_12", "dp_po_tal_15"]
    J[J.fall.isin(["fp", "fn"])][[c for c in cols if c in J]].round(2).sort_values(["fall", "ursache"]).to_csv(
        f"{B.RES}/sat_pruefung/ursachen.csv")
    md = ["# Satellitenprüfung: Fehlalarme und verpasste Tage\n",
          f"Satellitenfaktoren aus {int(clean.sum())} sauberen Breva-Abenden: Samolaco × {f_s:.2f}, Colico × {f_c:.2f}.\n"]
    for k, name in (("fp", "Fehlalarme (Modell ja, Ziel nein)"), ("fn", "Verpasste Tage (Modell nein, Ziel ja)")):
        X = J[J.fall == k]
        t = X.groupby("ursache").agg(faelle=("p", "size"), modell_p=("p", "median"), satellit_kn=("see", "median"),
                                     foehnindex=("dp_zurich_milano_12", "median"), regen=("regen", "median")).round(2)
        md += [f"## {name}: {len(X)}\n", "```", t.sort_values("faelle", ascending=False).to_string(), "```\n"]
    # 2. Ziel-Varianten gegen den Satelliten (März–Oktober, alle Abende)
    S = J[J.index.month.isin(range(3, 11))]
    sb = (S.sat_richtung == 200) & (S.see >= 14)
    mor_ok = S.morgen_nicht_breva < 6; nord_ok = S.nord_std < 2
    V = {"B (bisher)": (S.run_s >= 2) & (S.morgen_alle < 6) & nord_ok,
         "B_morgen": (S.run_s >= 2) & mor_ok & nord_ok,
         "B_zwei (Mittel Samolaco+Colico)": (S.run_both >= 2) & mor_ok & nord_ok,
         "B_eine (Samolaco oder Colico)": (S.run_either >= 2) & mor_ok & nord_ok}
    rows = []
    for name, v in V.items():
        tp = (v & sb).sum(); fp_ = (v & ~sb).sum(); fn_ = (~v & sb).sum()
        rows.append(dict(ziel=name, breva_tage=int(v.sum()), satellit_breva=int(sb.sum()),
                         uebereinstimmung=round(float((v == sb).mean()), 3),
                         praezision=round(tp / max(tp + fp_, 1), 3), recall=round(tp / max(tp + fn_, 1), 3),
                         kappa=round(kappa(v, sb), 3)))
    R = pd.DataFrame(rows)
    check = float(((S.run_s >= 2) == (S.y == 1)).mean()) if "y" in S else np.nan
    md += [f"## Ziel-Varianten gegen den Satelliten ({len(S)} Abende März–Oktober)\n",
           "Satellit-Breva = Abendbild aus Süd mit ≥ 14 kn auf dem oberen See. Das Bild entsteht gegen 19:15 – "
           "ein Breva, der früher abflaut, fehlt dort; ein perfektes Ziel erreicht deshalb keine 100 %.\n",
           "```", R.to_string(index=False), "```",
           f"\nKontrolle: Nachbau von B stimmt an {check:.0%} der Abende mit dem gespeicherten Ziel überein.\n"]
    open(f"{B.RES}/sat_analyse.md", "w").write("\n".join(md) + "\n")
    print("\n".join(md))
    print("geschrieben: results/sat_analyse.md, results/sat_pruefung/ursachen.csv")


if __name__ == "__main__":
    main()
