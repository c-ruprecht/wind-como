"""Satellitenbilder für Fehl- und Treffer-Tage des Modells zur Sichtprüfung.

Idee: An Tagen, an denen das Modell Breva vorhersagt, die Stationen aber keinen messen (falsch positiv, FP), ist
entweder das Modell falsch – oder das Ziel (Stationen) bzw. die Satellitenauswertung. Das Abendbild (Sentinel-1,
gegen 19:15) zeigt, was auf dem See wirklich los war. Zum Vergleich: Treffer (TP) und, optional, verpasste Tage (FN).

Vorhersage: 7-Tage-Modell mit dem Wetter des Tages selbst (ERA5), je Jahr out-of-fold (Modell ohne dieses Jahr) –
also „was das Modell bei perfekter Wettervorhersage sagen würde“. So gibt es Fälle über alle Satellitenjahre.

Je Tag ein Bild: links Satellitenwind auf dem oberen See (kn) mit Spots, rechts Samolaco über den Tag
(Wind × Seefaktor in Breva-Richtung, Richtung, Überflugzeit, Schwelle). Titel: Datum, Modell-Chance, Klasse,
Seewind laut Satellit, Regen.

  python training/sat_pruefung.py [--schwelle 14] [--fp 60] [--tp 25] [--fn 25] [--ab 0.5]
-> results/sat_pruefung/{fp,tp,fn}/<datum>_p<chance>.png und results/sat_pruefung/liste.csv (alle Fälle mit Werten)
   (Bilder ~50 KB; zum Anschauen committen und pushen)
"""
import argparse, glob, os, shutil, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402
import train_breva as T  # noqa: E402
import train_heute as TH  # noqa: E402
import sar_lake as SL  # noqa: E402

OUT = os.path.join(B.RES, "sat_pruefung")


def oof_era5(D, thr):
    F = T.FEATS
    E = B.features(B.load("era5")).reindex(D.index).reindex(columns=F)
    ok = E.notna().mean(axis=1) > 0.7
    y = T.target(D, thr)
    p = pd.Series(np.nan, index=D.index)
    for yr in sorted(set(D.index[ok].year)):
        tr = ok & (D.index.year != yr); te = ok & (D.index.year == yr)
        m = T.xgb_model(F).fit(E[tr], y[tr])
        p[te] = m.predict_proba(E[te])[:, 1]
    return p, y


def evening_scenes():
    """je Ortsdatum das letzte Abendbild (benachbarte Kacheln desselben Überflugs nur einmal)"""
    rows = []
    for f in sorted(glob.glob(f"{SL.OUT}/wind/*.npz")):
        te = pd.Timestamp(os.path.basename(f)[:15], tz="UTC")
        lt = te.tz_convert("Europe/Rome")
        if lt.hour >= 12:
            rows.append(dict(tag=lt.normalize().tz_localize(None), t=lt, file=f))
    if not rows:
        sys.exit(f"keine Abend-Windbilder in {SL.OUT}/wind – erst sar_lake.py download/wind")
    S = pd.DataFrame(rows).sort_values("t")
    S = S[S.t.diff().fillna(pd.Timedelta(hours=1)) > pd.Timedelta(minutes=5)]
    return S.groupby("tag").last()


def draw(path, r, water, ys, xs, sel, O, factor, thr):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    z = np.load(r.file); v = z["v"] * SL.KN
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 4.2), gridspec_kw=dict(width_ratios=[1, 1.35]))
    im = a1.imshow(np.where(water, v, np.nan), extent=(SL.BBOX[0], SL.BBOX[2], SL.BBOX[1], SL.BBOX[3]),
                   cmap="turbo", vmin=0, vmax=24)
    for k, (la, lo) in SL.SPOTS.items():
        a1.plot(lo, la, "o", ms=4, mfc="white", mec="black", mew=0.6)
        a1.text(lo + 0.004, la, k.split("_")[0], fontsize=6.5, color="black",
                bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7))
    a1.set_xticks([]); a1.set_yticks([]); a1.set_aspect(1 / np.cos(np.radians(46)))
    fig.colorbar(im, ax=a1, shrink=0.8, label="kn")
    dq = str(z["dir_quelle"]) if "dir_quelle" in z else "?"
    a1.set_title(f"Satellit {r.t:%H:%M} · See {r.see:.1f} kn\nRichtung {float(z['dir']):.0f}° ({dq})", fontsize=9)
    # Samolaco über den Tag
    d = r.name
    s = O["samolaco"].loc[d + pd.Timedelta(hours=6): d + pd.Timedelta(hours=22)]
    if len(s):
        h = s.index.hour + s.index.minute / 60
        brev = ((s.dir >= 112) & (s.dir <= 202))
        a2.bar(h, s.kn * factor, width=0.8, color=np.where(brev, "#0b6e8a", "#b9c2c8"), label="Samolaco × Seefaktor")
        a2.axhline(thr, color="#d1495b", lw=1, ls="--")
        ax3 = a2.twinx(); ax3.plot(h, s.dir, ".", color="#e09f3e", ms=5); ax3.set_ylim(0, 360); ax3.set_yticks([0, 90, 180, 270, 360])
        ax3.set_ylabel("Richtung °", fontsize=8); ax3.tick_params(labelsize=7)
    a2.axvline(r.t.hour + r.t.minute / 60, color="black", lw=1, ls=":")
    a2.set_xlim(6, 22); a2.set_ylim(0, max(25, thr + 5)); a2.set_xlabel("Uhr (Ortszeit)", fontsize=8)
    a2.set_ylabel("kn (blau = Richtung SSO–S)", fontsize=8); a2.tick_params(labelsize=7)
    a2.set_title(f"Samolaco: Morgen {r.sam_morgen:.0f} kn, Max {r.sam_max:.0f} kn, Nordwind {r.sam_nord_std:.0f} h", fontsize=9)
    fig.suptitle(f"{d:%a %d.%m.%Y}   Modell {100 * r.p:.0f} %   Ziel ≥{thr}: {'ja' if r.y else 'nein'}   "
                 f"Klasse {r.klasse}   Regen {r.regen:.1f} mm", fontsize=10, fontweight="bold")
    fig.tight_layout(); fig.savefig(path, dpi=80); plt.close(fig)


def main(thr, n_fp, n_tp, n_fn, cut):
    D = pd.read_csv(f"{B.RES}/breva_tage.csv", index_col=0, parse_dates=True)
    print("Modell je Jahr out-of-fold (ERA5) …", flush=True)
    p, y = oof_era5(D, thr)
    S = evening_scenes()
    water = SL.clean_mask(np.load(f"{SL.OUT}/water_mask.npy"))
    ys, xs, sel = SL.spot_pixels(water)
    up = [k for k in ("colico", "gera_lario", "sorico_punta", "domaso") if k in sel]

    def see(f):
        v = np.load(f)["v"] * SL.KN
        vals = [np.nanmedian(v[ys[sel[k]], xs[sel[k]]]) for k in up]
        return float(np.nanmean(vals))
    L = D.join(S, how="inner")
    L["p"] = p.reindex(L.index); L["y"] = y.reindex(L.index)
    L = L[L.p.notna()].copy()
    L["see"] = [see(f) for f in L.file]
    L["sat_richtung"] = [float(np.load(f)["dir"]) for f in L.file]          # 200 = Süd (Breva), 20 = Nord
    L["fall"] = np.select([(L.p >= cut) & (L.y == 0), (L.p >= cut) & (L.y == 1), (L.p < 0.2) & (L.y == 1)],
                          ["fp", "tp", "fn"], "")
    print(f"Abende mit Satellitenbild und Modell: {len(L)}; FP {int((L.fall == 'fp').sum())}, "
          f"TP {int((L.fall == 'tp').sum())}, FN {int((L.fall == 'fn').sum())} (Schwelle {cut:.2f})")
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)
    keep = ["p", "y", "fall", "klasse", "see", "sat_richtung", "sat_see", "sam_morgen", "sam_max", "sam_nord_std", "sam_boe",
            "see_max_est", "regen", "sat_widerspruch"]
    L.assign(zeit=L.t.dt.strftime("%H:%M"))[["zeit"] + [c for c in keep if c in L]].round(3).to_csv(f"{OUT}/liste.csv")
    O = TH.hourly_obs()
    factor = float((D.see_max_est / D.sam_max).median())
    for kind, n, asc in (("fp", n_fp, False), ("tp", n_tp, False), ("fn", n_fn, True)):
        X = L[L.fall == kind].sort_values("p", ascending=asc).head(n)
        if X.empty:
            continue
        os.makedirs(f"{OUT}/{kind}", exist_ok=True)
        for d, r in X.iterrows():
            draw(f"{OUT}/{kind}/{d:%Y-%m-%d}_p{100 * r.p:02.0f}.png", r, water, ys, xs, sel, O, factor, thr)
        print(f"  {kind}: {len(X)} Bilder; Seewind laut Satellit Median {X.see.median():.1f} kn, "
              f"≥ 10 kn: {(X.see >= 10).sum()}, ≥ {thr} kn: {(X.see >= thr).sum()}")
    # Kurzbilanz: Wie oft zeigt der Satellit bei FP doch Breva?
    for kind in ("fp", "tp", "fn"):
        X = L[L.fall == kind]
        if len(X):
            print(f"  alle {kind.upper()} ({len(X)}): Satellit Median {X.see.median():.1f} kn, "
                  f"Anteil ≥ 10 kn {(X.see >= 10).mean():.0%}")
    print(f"geschrieben: {os.path.relpath(OUT)}/ (liste.csv + Bilder) – zum Anschauen committen und pushen")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--schwelle", type=int, default=14)
    ap.add_argument("--fp", type=int, default=60)
    ap.add_argument("--tp", type=int, default=25)
    ap.add_argument("--fn", type=int, default=25)
    ap.add_argument("--ab", type=float, default=0.5, help="Modell-Chance, ab der ein Tag als „Breva vorhergesagt“ zählt")
    a = ap.parse_args()
    main(a.schwelle, a.fp, a.tp, a.fn, a.ab)
