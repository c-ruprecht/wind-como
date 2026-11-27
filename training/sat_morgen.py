"""Nordwind am Morgen (Tivano / Nordföhn) in den Satellitenbildern – und lässt er sich vorhersagen?

Sentinel-1 überfliegt den See morgens absteigend (~05:35 UTC = 6:35/7:35 Ortszeit). Wie sat_kategorien.py, nur für
die Morgenbilder: Rauigkeit σ⁰ in dB über dem ruhigen Referenzbild derselben Spur (20 %-Quantil je Pixel).

1. Je Morgenbild: Rauigkeit Süd/Mitte/Nord, Profil Nord→Süd, Anteil rauer Pixel; dazu die Stationen zur
   Überflugstunde und 5–10 Uhr (Nordkomponente Samolaco 337°, Colico 20°, Vercana, Morbegno).
   Beim Nordwind wächst der Anlauf nach Süden: rauer in Mitte/Süd als im Nordbecken (Profil fällt nach Norden).
2. Klassen: ruhig | nordwind (See rau, Stationen Nord) | nordwind_stark (ganzer See rau, Föhn) | sued | sonst.
3. Stationsziel für alle Tage: „Nordwind am Morgen“ = Samolaco-Nordkomponente 6–10 Uhr mind. 2 h ≥ T kn;
   T so gewählt, dass es am besten zum Satelliten passt (Kappa).
4. Vorhersagbar? Je ERA5-Größe Trennschärfe (AUC) und ein Modell je Jahr out-of-fold (ERA5 = Wetter wie es war,
   obere Grenze), dazu – falls vorhanden – mit den echten Läufen vom Vortag (2024–heute).

  python training/sat_morgen.py                    # oberer See (data/sar100)
  python training/sat_morgen.py --region lecco     # Lecco-Arm (data/sar100_lecco, vorher sar_lake.py download --region lecco)
  -> results/sat_morgen[_lecco]/: morgen.csv, profile.png, stationen.png, <klasse>.png (Bildtafeln), monate.png,
     vorhersage.md, merkmale.csv
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402
import sar_lake as SL  # noqa: E402
import sat_kategorien as SK  # noqa: E402
import see_achse as SA  # noqa: E402

OUT = os.path.join(B.RES, "sat_morgen")
RUHIG, RAU, STARK = 2.0, 4.0, 6.0                       # dB über ruhig, vorläufig – an den Tafeln prüfen
# Je Ausschnitt: Abschnitte (Breite), Orte fürs Profil, Stationen; die erste Station ist das Stationsziel.
# Nordwind an einer Station = Stärke, wenn die Richtung im Nordsektor liegt (sonst 0); Süd = negativ.
REG = {
    "oben": dict(seg={"sued": (45.96, 46.03), "mitte": (46.03, 46.10), "nord": (46.10, 46.18)},
                 orte=(("Bellagio", 45.985), ("Menaggio", 46.02), ("Dervio", 46.077), ("Colico", 46.137), ("Domaso", 46.15)),
                 stationen={"samolaco": ((290, 60), (112, 202)), "colico": ((330, 100), (200, 315)),
                            "vercana": ((330, 90), (180, 270)), "morbegno": ((20, 110), (200, 290))}),
    "lecco": dict(seg={"sued": (45.83, 45.89), "mitte": (45.89, 45.95), "nord": (45.95, 46.01)},
                  orte=(("Valmadrera/Parè", 45.852), ("Abbadia", 45.898), ("Mandello", 45.918), ("Lierna", 45.957), ("Varenna", 46.01)),
                  stationen={"valmadrera": ((330, 90), (135, 225)), "lecco": ((330, 90), (135, 225)),
                             "samolaco": ((290, 60), (112, 202)), "colico": ((330, 100), (200, 315))}),
    # ganzer See: Abschnitte je Arm (see_achse.py), Drittel nord/mitte/sued
    "ganz": dict(achsen=True, seg={"_": (45.80, 46.21)}, orte=(),
                 stationen={"colico": ((330, 100), (200, 315)), "samolaco": ((290, 60), (112, 202)),
                            "vercana": ((330, 90), (180, 270)), "valmadrera": ((330, 90), (135, 225)),
                            "lecco": ((330, 90), (135, 225)), "como": ((330, 90), (150, 240))}),
}
R_ = REG["oben"]


def set_region(name):
    global OUT, R_
    SL.set_region(name)
    R_ = REG[name]
    SK.SEG = R_["seg"]
    lo = min(a for a, _ in R_["seg"].values()); hi = max(b for _, b in R_["seg"].values())
    SK.LAT_BINS = np.round(np.arange(lo, hi + 0.01, 0.01), 3)
    OUT = os.path.join(B.RES, "sat_morgen" if name == "oben" else f"sat_morgen_{name}")


def station_morning():
    """Je Station Stundenwerte (Ortszeit, Stunde endet zur vollen Stunde): Nordwind > 0, Südwind < 0, sonst 0."""
    ins = lambda d, a, b: ((d >= a) & (d <= b)) if a <= b else ((d >= a) | (d <= b))  # noqa: E731
    out = {}
    for st, (nord, sued) in R_["stationen"].items():
        f = os.path.join(B.DATA, "arpa", f"{st}_wind.csv")
        if not os.path.exists(f):
            continue
        x = pd.read_csv(f, parse_dates=["time"]).set_index("time")
        x.index = pd.DatetimeIndex(x.index).tz_convert(B.TZ).tz_localize(None)
        x = x[~x.index.duplicated(keep="first")]
        out[st] = x.kn.where(ins(x.dir, *nord), 0).where(~ins(x.dir, *sued), -x.kn)
    return pd.DataFrame(out)


def main():
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    water = SL.clean_mask(np.load(f"{SL.OUT}/water_mask.npy"))
    H, W = water.shape
    lat = (SL.BBOX[3] - (np.arange(H) + 0.5) * (SL.BBOX[3] - SL.BBOX[1]) / H)[:, None] * np.ones((1, W))
    if R_.get("achsen"):
        arm, km, arms, lens = SA.zonen(H, W, SL.BBOX, water)
        ZONES = {f"{a}_{zn}": (arm == i) & (km >= lo * lens[a]) & (km < hi * lens[a])
                 for i, a in enumerate(arms) for zn, (lo, hi) in (("nord", (0, 1 / 3)), ("mitte", (1 / 3, 2 / 3)), ("sued", (2 / 3, 1.01)))}
        PBINS = [(f"{a}:{k}", (arm == i) & (km >= k) & (km < k + 1)) for i, a in enumerate(arms) for k in range(int(lens[a]) + 1)]
        print("Wasserpixel je Arm:", {a: int((arm == i).sum()) for i, a in enumerate(arms)})
    else:
        ZONES = {k: water & (lat >= a) & (lat < b) for k, (a, b) in SK.SEG.items()}
        PBINS = [(f"{a:.2f}", water & (lat >= a) & (lat < a + 0.01)) for a in SK.LAT_BINS[:-1]]
    ZK = list(ZONES)
    S = SK.scenes()
    S = S[S.te.dt.tz_convert("Europe/Rome").dt.hour < 12].reset_index(drop=True)
    print(f"{len(S)} Morgen-Überflüge mit Rohbild; lese σ⁰ …", flush=True)

    def one(s):
        try:
            db, inc = SK.read_raw(s.file)
        except Exception as e:
            print("  ", os.path.basename(s.file), e); return None, None
        if db.shape != water.shape:
            return None, None
        return np.where(water, db, np.nan).astype("float32"), f"{s.orbit}{int(round(float(np.nanmedian(inc[water]))))}"
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 2)) as ex:
        res = list(ex.map(one, [s for _, s in S.iterrows()]))
    S["spur"] = [r[1] for r in res]
    DB = [r[0] for r in res]
    ok = S.spur.notna().values
    S = S[ok].reset_index(drop=True); DB = [d for d, k in zip(DB, ok) if k]
    ref = {t: np.nanpercentile(np.stack([DB[i] for i in idx]), 20, axis=0)
           for t, idx in S.groupby("spur").groups.items() if len(idx) >= 8}
    print("Bilder je Spur:", S.spur.value_counts().to_dict())

    ST = station_morning()
    hh = ST.index.hour; dd = ST.index.normalize()
    win = (hh >= 6) & (hh <= 10)
    sm = ST[win]
    morgen = pd.DataFrame({f"{c}_nord_max": sm[c].groupby(dd[win]).max() for c in ST.columns})
    rows, profs, R = [], [], {}
    for i, s in S.iterrows():
        if s.spur not in ref:
            continue
        lt = s.te.tz_convert("Europe/Rome")
        r = DB[i] - ref[s.spur]
        rec = {k: float(np.nanmedian(r[m])) if m.sum() >= 10 else np.nan for k, m in ZONES.items()}
        v = r[water]; v = v[np.isfinite(v)]
        rec["rau_ganz"] = float((v >= RAU).mean()) if v.size else np.nan
        prof = [float(np.nanmedian(r[m])) if m.sum() >= 10 else np.nan for _, m in PBINS]
        d = lt.normalize().tz_localize(None)
        hour_end = lt.hour + 1                           # Stundenmittel endet zur vollen Stunde
        for st in ST.columns:
            rec[f"{st}_ueberflug"] = ST[st].get(d + pd.Timedelta(hours=hour_end), np.nan)
            rec[f"{st}_nord_max"] = morgen[f"{st}_nord_max"].get(d, np.nan)
        try:
            z = np.load(s.wind)
            rec["kn_richtwert"] = float(np.nanmedian((z["v"] * SL.KN)[water]))
        except Exception:
            rec["kn_richtwert"] = np.nan
        rec.update(tag=d, zeit=lt.strftime("%H:%M"), spur=s.spur)
        rows.append(rec); profs.append(prof); R[d] = r
    A = pd.DataFrame(rows).set_index("tag")
    keep = ~A.index.duplicated(keep="last")
    P = pd.DataFrame(profs, index=A.index, columns=[k for k, _ in PBINS])[keep]
    A = A[keep]
    if R_.get("achsen"):                                  # je Arm: Süddrittel − Norddrittel (> 0: nach Süden rauer)
        for a in arms:
            A[f"abfall_{a}"] = A[f"{a}_sued"] - A[f"{a}_nord"]
            A[f"arm_{a}"] = A[[f"{a}_nord", f"{a}_mitte", f"{a}_sued"]].mean(axis=1)
    else:
        A["abfall"] = A[["sued", "mitte"]].mean(axis=1) - A.nord      # > 0: nach Süden rauer (Nordwind-Fetch)
    A["gesamt"] = A[ZK].mean(axis=1)
    A["zmax"] = A[ZK].max(axis=1)
    st_cols = [f"{st}_ueberflug" for st in ST.columns]
    nord_st = (A[st_cols] > 2).any(axis=1)
    sued_st = (A[st_cols] < -3).any(axis=1) & ~nord_st

    def cat(r, n, so):
        if not np.isfinite(r.gesamt) or r.zmax < RUHIG:
            return "ruhig"
        if so:
            return "sued"
        if n and np.nanmedian([r[k] for k in ZK]) >= STARK:
            return "nordwind_stark"
        if n and r.zmax >= RAU:
            return "nordwind"
        return "sonst"
    A["klasse"] = [cat(r, n, so) for (_, r), n, so in zip(A.iterrows(), nord_st, sued_st)]
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".png"):
            os.remove(os.path.join(OUT, f))
    A.round(3).to_csv(f"{OUT}/morgen.csv"); P.round(2).to_csv(f"{OUT}/profile.csv")
    md = [f"# Nordwind am Morgen im Satelliten – {SL.REGION}\n", f"{len(A)} Morgenbilder ({A.index.min():%Y}–{A.index.max():%Y}), Klassen:\n", "```",
          A.klasse.value_counts().to_string(), "```", "\nMedian je Klasse (dB über ruhig; Stationen: Nordkomponente kn):\n", "```",
          A.groupby("klasse")[ZK + [c for c in A.columns if c.startswith("abfall")] + ["rau_ganz", "kn_richtwert"] + st_cols
                              + [f"{st}_nord_max" for st in ST.columns]].median().round(2).to_string(), "```"]
    # Je Monat
    nw = A.klasse.isin(["nordwind", "nordwind_stark"])
    mon = pd.DataFrame({"Bilder": A.groupby(A.index.month).size(), "Anteil Nordwind": nw.groupby(A.index.month).mean().round(2)})
    md += ["\nAnteil der Morgenbilder mit Nordwind je Monat:\n", "```", mon.to_string(), "```"]

    # Stationsziel: Schwelle T so, dass es am besten zum Satelliten passt
    from sklearn.metrics import cohen_kappa_score, roc_auc_score
    best = None; scan = []
    for stz in ST.columns:                               # jede Station als mögliches Stationsziel
        sw = ST[stz][win].dropna()                       # nur Tage, an denen die Station misst
        n_h = sw.groupby(sw.index.normalize()).size()
        for T in (2, 3, 4, 5, 6, 8):
            h = (sw >= T).groupby(sw.index.normalize()).sum()
            lab = (h >= 2).astype(int)[n_h >= 3]
            j = pd.concat([lab.rename("st"), nw.astype(int).rename("sat")], axis=1, join="inner").dropna()
            k = cohen_kappa_score(j.st, j.sat) if j.st.nunique() == 2 and j.sat.nunique() == 2 else np.nan
            scan.append((stz, T, round(k, 3), round(lab.mean(), 3), len(j), f"{lab.index.min():%Y}"))
            if np.isfinite(k) and len(j) >= 40 and (best is None or k > best[2]):
                best = (stz, T, k, lab)
    md += ["\nStationsziel „Nordwind am Morgen“ (Nordwind an der Station 6–10 Uhr mind. 2 h ≥ T kn) gegen den Satelliten:\n",
           "```", pd.DataFrame(scan, columns=["station", "T_kn", "kappa", "anteil_tage", "bilder", "ab"]).to_string(index=False), "```"]
    if best is None:
        open(f"{OUT}/vorhersage.md", "w").write("\n".join(md) + "\n"); print("\n".join(md)); return
    md += [f"Gewählt: {best[0]}, T = {best[1]} kn (Kappa {best[2]:.2f})."]
    best = (best[1], best[2], best[3])
    y_all = best[2]
    y_all.to_frame("nordwind_morgen").to_csv(f"{OUT}/ziel_stationen.csv")

    # Vorhersagbar?
    try:
        import train_breva as T
        FE = B.features(B.load("era5"))
        y = y_all.reindex(FE.index).dropna().astype(int)
        X = FE.reindex(y.index)
        rows_f = []
        for c in X.columns:
            x = X[c]; m = x.notna()
            if m.sum() > 200 and x[m].std() > 0:
                a = roc_auc_score(y[m], x[m]); rows_f.append((c, c in T.FEATS, round(max(a, 1 - a), 3), "höher" if a >= 0.5 else "tiefer",
                                                            round(x[m][y[m] == 1].median(), 2), round(x[m][y[m] == 0].median(), 2)))
        Fm = pd.DataFrame(rows_f, columns=["groesse", "im_breva_modell", "auc", "bei_nordwind", "median_nordwind", "median_sonst"]).sort_values("auc", ascending=False)
        Fm.to_csv(f"{OUT}/merkmale.csv", index=False)
        md += ["\n## Vorhersagbar?\n", f"Stationsziel an {len(y)} Tagen, davon {y.mean():.0%} mit Nordwind am Morgen.\n",
               "Stärkste Einzelgrößen (ERA5, Wetter wie es war):", "```", Fm.head(15).to_string(index=False), "```"]
        feats = list(X.columns)
        P_ = pd.Series(np.nan, index=y.index)
        for yr in sorted(set(y.index.year)):
            tr = y.index.year != yr
            m = T.xgb_model(feats).fit(X[tr], y[tr]); P_[~tr] = m.predict_proba(X[~tr])[:, 1]
        sa = y.index.month.isin(range(3, 11))
        md += [f"\nModell je Jahr out-of-fold mit ERA5 (obere Grenze): AUC {roc_auc_score(y, P_):.3f}, "
               f"März–Oktober {roc_auc_score(y[sa], P_[sa]):.3f}."]
        try:
            L1 = B.features(B.load("prev", 1, T.MODEL)).reindex(y.index)
            for c in feats:
                if c not in L1:
                    L1[c] = np.nan
            L1 = L1[feats]; g = L1.notna().mean(axis=1) > 0.7
            Pf = pd.Series(np.nan, index=y.index)
            for yr in sorted(set(y.index[g].year)):
                tr = y.index.year != yr; te = g & (y.index.year == yr)
                m = T.xgb_model(feats).fit(X[tr], y[tr]); Pf[te] = m.predict_proba(L1[te])[:, 1]
            ok = Pf.notna()
            md += [f"Mit dem echten ECMWF-Lauf vom Vortag ({int(ok.sum())} Tage ab {y.index[ok].min():%Y}): AUC {roc_auc_score(y[ok], Pf[ok]):.3f}."]
        except Exception as e:
            md += [f"(Vortagsläufe nicht geprüft: {e})"]
    except Exception as e:
        md += [f"\n(Vorhersage-Prüfung übersprungen: {e})"]

    # Bilder
    if R_.get("achsen"):
        fig, axs = plt.subplots(1, len(arms), figsize=(5 * len(arms), 4), sharey=True)
        for ax, a in zip(axs, arms):
            cols = [c for c in P.columns if c.startswith(a + ":")]
            x = [int(c.split(":")[1]) + 0.5 for c in cols]
            for k, g in A.groupby("klasse"):
                ax.plot(x, P.reindex(g.index)[cols].median().values, lw=2, label=f"{k} ({len(g)})")
            for name, la, lo in SA.ORTE[a]:
                kk = SA.ort_km(a, la, lo)
                ax.axvline(kk, color="grey", lw=0.5, ls=":"); ax.text(kk, 0.02, name, rotation=90, fontsize=7, va="bottom", transform=ax.get_xaxis_transform())
            ax.axhline(0, color="black", lw=0.6); ax.grid(alpha=0.3); ax.set_title(SA.NAMEN[a], fontsize=9)
            ax.set_xlabel("km from the northern end of the branch")
        axs[0].set_ylabel("Rauigkeit über ruhig (dB)"); axs[0].legend(fontsize=7)
        fig.suptitle("Morgens: Rauigkeitsprofil je Arm und Klasse (Nord → Süd)", fontsize=10)
    else:
        fig, ax = plt.subplots(figsize=(6.5, 4))
        for k, g in A.groupby("klasse"):
            ax.plot([float(c) + 0.005 for c in P.columns], P.reindex(g.index).median().values, lw=2, label=f"{k} ({len(g)})")
        for name, la in R_["orte"]:
            ax.axvline(la, color="grey", lw=0.5, ls=":"); ax.text(la, 0.02, name, rotation=90, fontsize=7, va="bottom", transform=ax.get_xaxis_transform())
        ax.axhline(0, color="black", lw=0.6); ax.legend(fontsize=8); ax.grid(alpha=0.3)
        ax.set_xlabel("Breite (Süd → Nord)"); ax.set_ylabel("Rauigkeit über ruhig (dB)")
        ax.set_title("Morgens: Rauigkeitsprofil je Klasse", fontsize=9)
    fig.tight_layout(); fig.savefig(f"{OUT}/profile.png", dpi=100); plt.close(fig)
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    for ax, st in zip(axs, st_cols[:2]):
        for k, g in A.groupby("klasse"):
            ax.scatter(g[st], g.zmax, s=10, alpha=0.6, label=k)
        ax.axvline(0, color="grey", lw=0.6); ax.grid(alpha=0.3)
        ax.set_xlabel(f"{st.split('_')[0].title()}: Nordwind zur Überflugstunde (kn, Süd negativ)")
    axs[0].set_ylabel("Rauigkeit, rauester Abschnitt (dB über ruhig)"); axs[0].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(f"{OUT}/stationen.png", dpi=100); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.bar(mon.index, mon["Anteil Nordwind"], color="#00829b"); ax.set_xticks(range(1, 13))
    ax.set_ylabel("Anteil Morgenbilder"); ax.set_title("Nordwind am Morgen je Monat (Satellit)", fontsize=9); ax.grid(alpha=0.3, axis="y")
    fig.tight_layout(); fig.savefig(f"{OUT}/monate.png", dpi=100); plt.close(fig)

    def sheet(path, X, title):
        X = X[:24]
        if not len(X):
            return
        nc = 6; nr = int(np.ceil(len(X) / nc))
        fig, axs = plt.subplots(nr, nc, figsize=(2.3 * nc, 2.9 * nr), squeeze=False)
        for ax, (d, r) in zip(axs.flat, X.iterrows()):
            im = ax.imshow(np.where(water, R[d], np.nan), extent=(SL.BBOX[0], SL.BBOX[2], SL.BBOX[1], SL.BBOX[3]), cmap="magma", vmin=-2, vmax=12)
            ax.set_aspect(1 / np.cos(np.radians(46))); ax.set_xticks([]); ax.set_yticks([])
            zt = (" ".join(f"{a[0].upper()}{r['arm_' + a]:.1f}" for a in arms) if R_.get("achsen")
                  else f"N{r.nord:.1f}/M{r.mitte:.1f}/S{r.sued:.1f}")
            ax.set_title(f"{d:%d.%m.%y} {r.zeit} {zt}\n"
                         + " · ".join(f"{c[:3].title()} {r[c + '_ueberflug']:+.0f}" for c in ST.columns[:2]) + " kn", fontsize=7)
        for ax in list(axs.flat)[len(X):]:
            ax.axis("off")
        fig.colorbar(im, ax=axs, shrink=0.5, label="dB über ruhig")
        fig.suptitle(title + "  (N/M/S = Nordbecken/Mitte/Süd bzw. O/L/C = Arm oben/Lecco/Como, dB; erste zwei Stationen: Nordwind zur Überflugstunde, Süd negativ)", fontsize=8)
        fig.savefig(path, dpi=75, bbox_inches="tight"); plt.close(fig)
    for k, g in A.groupby("klasse"):
        sheet(f"{OUT}/{k}.png", g.sort_values("gesamt", ascending=False), f"{k}: {len(g)} Morgen")
    open(f"{OUT}/vorhersage.md", "w").write("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\ngeschrieben: {os.path.relpath(OUT)}/")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", choices=list(REG), default="oben")
    set_region(ap.parse_args().region)
    main()
