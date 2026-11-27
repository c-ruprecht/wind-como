"""Kategorien aus den Satellitenbildern: das räumliche Muster entlang des Sees statt nur ein Wert.

Breva hat eine Signatur: schwächer im Süden (Bellagio/Menaggio), mittel bei Dervio/Cremia, am stärksten im
Nordbecken (Domaso/Colico/Gera/Sorico). Ein Gewitter- oder Sturmbild ist auf dem ganzen See stark, Südströmung vor
einer Front eher gleichmäßig, ruhige Abende überall schwach.

Je Abendbild (Ortszeit ≥ 12 Uhr):
  Profil   Median-Wind in 0,01°-Breitenstreifen (≈ 1,1 km) von Süd nach Nord
  sued     45,96–46,03 (Bellagio–Menaggio)   mitte 46,03–46,10 (Cremia/Dervio)   nord 46,10–46,18 (Domaso–Sorico)
  anstieg  nord − sued (kn)          gleichm  Streuung der Pixel / Mittel        p_stark Anteil Pixel ≥ 20 kn
  richtung aus der Windbild-Datei (Station/Modell, nicht vom Satelliten gemessen)
Kategorien (Regeln, an den Bildtafeln zu prüfen und anzupassen):
  ruhig              nord < 8 kn
  nordwind           Richtung 20° (Tivano/Föhn/Nordlage)
  gewitter_sturm     sued ≥ 16 und mitte ≥ 16 kn (ganzer See stark) oder p_stark ≥ 0,5 mit Regen ≥ 2 mm
  breva_typisch      Süd, nord ≥ 8 kn, anstieg ≥ 2 kn (nach Norden zunehmend)
  sued_gleichmaessig Süd, nord ≥ 8 kn, anstieg < 2 kn
Ausgabe results/sat_kategorien/:
  abende.csv                 je Abend alle Werte + Kategorie + Stationswerte (Samolaco, Colico Nachmittagsmax)
  profile.png                mittleres Profil je Kategorie
  <kategorie>.png            Bildtafel (bis 24 Abende, nach Nordbecken-Wind sortiert)
  breva_stufen.png           typische Breva-Abende nach Stärke im Nordbecken (10–12, 12–14, 14–16, 16–18, ≥ 18 kn)
  stationen.png              Nordbecken-Wind (Satellit) gegen Samolaco-/Colico-Maximum, je Kategorie

  python training/sat_kategorien.py
"""
import glob, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402
import sar_lake as SL  # noqa: E402

OUT = os.path.join(B.RES, "sat_kategorien")
SEG = {"sued": (45.96, 46.03), "mitte": (46.03, 46.10), "nord": (46.10, 46.18)}
LAT_BINS = np.round(np.arange(45.96, 46.19, 0.01), 3)


def scene_stats(v, water, lat):
    ok = water & np.isfinite(v)
    r = {}
    for k, (a, b) in SEG.items():
        m = ok & (lat >= a) & (lat < b)
        r[k] = float(np.nanmedian(v[m])) if m.sum() >= 30 else np.nan
    allv = v[ok]
    r["gleichm"] = float(np.nanstd(allv) / max(np.nanmean(allv), 1)) if allv.size else np.nan
    r["p_stark"] = float((allv >= 20).mean()) if allv.size else np.nan
    prof = []
    for a in LAT_BINS[:-1]:
        m = ok & (lat >= a) & (lat < a + 0.01)
        prof.append(float(np.nanmedian(v[m])) if m.sum() >= 10 else np.nan)
    return r, prof


def category(r):
    if not np.isfinite(r["nord"]) or r["nord"] < 8:
        return "ruhig"
    if r["richtung"] != 200:
        return "nordwind"
    if (r["sued"] >= 16 and r["mitte"] >= 16) or (r["p_stark"] >= 0.5 and r.get("regen", 0) >= 2):
        return "gewitter_sturm"
    return "breva_typisch" if r["nord"] - r["sued"] >= 2 else "sued_gleichmaessig"


def sheet(path, rows, water, title):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    rows = rows[:24]
    if not len(rows):
        return
    nc = 6; nr = int(np.ceil(len(rows) / nc))
    fig, axs = plt.subplots(nr, nc, figsize=(2.3 * nc, 2.9 * nr), squeeze=False)
    for ax, (_, r) in zip(axs.flat, rows.iterrows()):
        v = np.load(r.file)["v"] * SL.KN
        ax.imshow(np.where(water, v, np.nan), extent=(SL.BBOX[0], SL.BBOX[2], SL.BBOX[1], SL.BBOX[3]),
                  cmap="turbo", vmin=0, vmax=24)
        ax.set_aspect(1 / np.cos(np.radians(46))); ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"{r.name:%d.%m.%y}  N{r.nord:.0f}/M{r.mitte:.0f}/S{r.sued:.0f}\n"
                     f"Sam {r.sam_max:.0f} · Col {r.col_max:.0f} kn", fontsize=7)
    for ax in list(axs.flat)[len(rows):]:
        ax.axis("off")
    fig.suptitle(title + "   (N/M/S = Nordbecken/Mitte/Süd, Satellit; Sam/Col = Stationsmaximum 11–20 Uhr)", fontsize=9)
    fig.tight_layout(); fig.savefig(path, dpi=75); plt.close(fig)


def main():
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    water = SL.clean_mask(np.load(f"{SL.OUT}/water_mask.npy"))
    H, W = water.shape
    lat = (SL.BBOX[3] - (np.arange(H) + 0.5) * (SL.BBOX[3] - SL.BBOX[1]) / H)[:, None] * np.ones((1, W))
    D = pd.read_csv(f"{B.RES}/breva_tage.csv", index_col=0, parse_dates=True)
    rows, profs = [], []
    files = sorted(glob.glob(f"{SL.OUT}/wind/*.npz"))
    last = None
    for f in files:
        te = pd.Timestamp(os.path.basename(f)[:15], tz="UTC"); lt = te.tz_convert("Europe/Rome")
        if lt.hour < 12 or (last is not None and te - last < pd.Timedelta(minutes=5)):
            continue
        last = te
        z = np.load(f); v = z["v"] * SL.KN
        r, prof = scene_stats(v, water, lat)
        d = lt.normalize().tz_localize(None)
        r.update(tag=d, zeit=lt.strftime("%H:%M"), file=f, richtung=float(z["dir"]),
                 richtung_quelle=str(z["dir_quelle"]) if "dir_quelle" in z else "modell")
        for c in ("sam_max", "col_max", "regen", "klasse", "breva14", "breva18", "sam_morgen"):
            r[c] = D[c].get(d, np.nan) if c in D else np.nan
        rows.append(r); profs.append(prof)
    if not rows:
        sys.exit("keine Abend-Windbilder – erst sar_lake.py download/wind")
    A = pd.DataFrame(rows).set_index("tag")
    A = A[~A.index.duplicated(keep="last")]
    P = pd.DataFrame(profs, columns=[f"{a:.2f}" for a in LAT_BINS[:-1]])
    P.index = pd.DataFrame(rows).tag
    P = P[~P.index.duplicated(keep="last")]
    A["regen"] = A.regen.fillna(0)
    A["anstieg"] = A.nord - A.sued
    A["kategorie"] = [category(r) for _, r in A.iterrows()]
    os.makedirs(OUT, exist_ok=True)
    A.drop(columns="file").round(3).to_csv(f"{OUT}/abende.csv")
    S = A[A.index.month.isin(range(3, 11))]
    print(f"{len(A)} Abendbilder, davon März–Oktober {len(S)}")
    print(S.kategorie.value_counts().to_string())
    print("\nMedian je Kategorie (März–Oktober):")
    print(S.groupby("kategorie")[["sued", "mitte", "nord", "anstieg", "gleichm", "p_stark", "sam_max", "col_max", "regen"]]
          .median().round(2).to_string())
    print("\nStationsziel (breva14) je Kategorie, Anteil:")
    print(S.groupby("kategorie").breva14.mean().round(2).to_string())
    # Profile
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for k, g in S.groupby("kategorie"):
        pm = P.reindex(g.index).median()
        ax.plot(LAT_BINS[:-1] + 0.005, pm.values, lw=2, label=f"{k} ({len(g)})")
    for k, (a, b) in SEG.items():
        ax.axvspan(a, b, alpha=0.06 if k == "mitte" else 0.0, color="grey")
    for name, la in (("Bellagio", 45.985), ("Menaggio", 46.02), ("Dervio", 46.077), ("Domaso", 46.15), ("Colico", 46.137), ("Sorico", 46.162)):
        ax.axvline(la, color="grey", lw=0.5, ls=":")
        ax.text(la, 0.02, name, rotation=90, fontsize=7, va="bottom", transform=ax.get_xaxis_transform())
    ax.set_xlabel("Breite (Süd → Nord)"); ax.set_ylabel("Median-Wind (kn)"); ax.legend(fontsize=8); ax.grid(alpha=0.3)
    ax.set_title("Mittleres Windprofil entlang des oberen Sees je Kategorie (März–Oktober)", fontsize=9)
    fig.tight_layout(); fig.savefig(f"{OUT}/profile.png", dpi=100); plt.close(fig)
    # Bildtafeln je Kategorie
    for k, g in S.groupby("kategorie"):
        sheet(f"{OUT}/{k}.png", g.sort_values("nord", ascending=False), water, f"{k}: {len(g)} Abende")
    # Breva-Stufen
    bt = S[S.kategorie == "breva_typisch"]
    bins = [(10, 12), (12, 14), (14, 16), (16, 18), (18, 99)]
    sel = pd.concat([bt[(bt.nord >= a) & (bt.nord < b)].sample(min(6, int(((bt.nord >= a) & (bt.nord < b)).sum())), random_state=0)
                     .sort_values("nord") for a, b in bins])
    sheet(f"{OUT}/breva_stufen.png", sel, water, "Typischer Breva nach Stärke im Nordbecken: je Zeile eine Stufe 10–12 / 12–14 / 14–16 / 16–18 / ≥ 18 kn")
    # Satellit gegen Stationen
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    for ax, st in zip(axs, ("sam_max", "col_max")):
        for k, g in S.groupby("kategorie"):
            ax.scatter(g[st], g.nord, s=12, alpha=0.7, label=k)
        ax.set_xlabel(f"{'Samolaco' if st == 'sam_max' else 'Colico'}: Maximum 11–20 Uhr (kn)"); ax.grid(alpha=0.3)
    axs[0].set_ylabel("Satellit Nordbecken um 19:15 (kn)"); axs[0].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(f"{OUT}/stationen.png", dpi=100); plt.close(fig)
    print(f"\ngeschrieben: {os.path.relpath(OUT)}/ (abende.csv, profile.png, Bildtafeln je Kategorie, breva_stufen.png, stationen.png)")


if __name__ == "__main__":
    main()
