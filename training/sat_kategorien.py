"""Kategorien aus den Satellitenbildern – aus der Wasserrauigkeit (σ⁰), nicht aus Meeres-Windgeschwindigkeiten.

CMOD5.N ist für den offenen Ozean geeicht; auf dem See (kurzer Fetch, Abschattung, Filme) sind die Knoten unsicher.
Für Klassen reicht die Rauigkeit selbst: Bei gleicher Geometrie bedeutet mehr σ⁰ mehr Wind.

Rauigkeit-Anomalie r (dB) je Pixel:
  σ⁰ in dB minus Referenz der „Spur“ (Orbitrichtung + Einfallswinkel am See, auf 1° gerundet).
  Referenz = 20 %-Quantil je Pixel über alle Bilder dieser Spur ≈ ruhiger See bei genau dieser Geometrie.
  Damit fallen Einfallswinkel, Uferabschattung und ortsfeste Störungen heraus; r = 0 heißt „wie an ruhigen Tagen“.
Je Abendbild (Ortszeit ≥ 12 Uhr):
  sued / mitte / nord   Median-r in 45,96–46,03 / 46,03–46,10 / 46,10–46,18 (Bellagio–Menaggio / Cremia–Dervio / Domaso–Sorico)
  rau_nord              Anteil Nordbecken-Pixel mit r ≥ RAU dB
  anstieg               nord − sued (dB)        flecken  Streuung der 1-km-Kachelmittel im ganzen See (dB)
  profil                Median-r in 0,01°-Streifen von Süd nach Nord
  kn_richtwert          CMOD5.N-Wind im Nordbecken (nur zur Orientierung)
Fetch-Prüfung: Beim Breva wächst der Anlauf nach Norden, das allein macht den Nordteil rauer. Verglichen wird der
  Anstieg bei Breva-Tagen (thermischer Ablauf an den Stationen) mit Südwind-Tagen ohne Ablauf (synoptisch/Regen/ruhig)
  bei ähnlicher Gesamtrauigkeit – nur ein Anstieg darüber hinaus ist ein Breva-Zeichen.
Kategorien (Regeln, an den Bildtafeln zu prüfen):
  ruhig              nord < RUHIG dB
  nordwind           Richtung 20° (Station/Modell – nicht vom Satelliten gemessen)
  gewitter_sturm     ganzer See rau (sued und mitte ≥ STURM dB) oder fleckig (flecken ≥ FLECK) bei Regen
  breva_typisch      Süd, nord ≥ RUHIG, anstieg ≥ ANSTIEG
  sued_gleichmaessig Süd, nord ≥ RUHIG, anstieg < ANSTIEG
Ausgabe results/sat_kategorien/: abende.csv, profile.png, fetch.png, <kategorie>.png (Bildtafeln der Rauigkeit),
  breva_stufen.png (nach Rauigkeit im Nordbecken), stationen.png (Rauigkeit Nordbecken gegen Samolaco/Colico)

  python training/sat_kategorien.py
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402
import sar_lake as SL  # noqa: E402

OUT = os.path.join(B.RES, "sat_kategorien")
SEG = {"sued": (45.96, 46.03), "mitte": (46.03, 46.10), "nord": (46.10, 46.18)}
LAT_BINS = np.round(np.arange(45.96, 46.19, 0.01), 3)
RUHIG, RAU, ANSTIEG, STURM, FLECK = 2.0, 4.0, 2.0, 6.0, 2.5      # dB, vorläufig – an den Tafeln anpassen


def read_raw(f):
    import rasterio
    with rasterio.open(f) as r:
        vv, inc, m = r.read(1), r.read(2), r.read(3)
    db = np.where((m > 0) & (vv > 0), 10 * np.log10(np.clip(vv, 1e-6, None)), np.nan)
    return db, inc


def scenes():
    sc = pd.read_csv(f"{SL.OUT}/scenes.csv")
    rows = []
    for _, s in sc.iterrows():
        p = f"{SL.OUT}/raw/{s.file}"
        if os.path.exists(p):
            rows.append(dict(file=p, wind=f"{SL.OUT}/wind/{s.file[:-4]}.npz", te=pd.Timestamp(s.file[:15], tz="UTC"),
                             orbit=str(s.orbit)[:3]))
    if not rows:
        sys.exit(f"keine Rohbilder in {SL.OUT}/raw – erst sar_lake.py download")
    S = pd.DataFrame(rows).sort_values("te")
    return S[S.te.diff().fillna(pd.Timedelta(hours=1)) > pd.Timedelta(minutes=5)].reset_index(drop=True)   # Kacheln nur einmal


def main():
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    water = SL.clean_mask(np.load(f"{SL.OUT}/water_mask.npy"))
    H, W = water.shape
    lat = (SL.BBOX[3] - (np.arange(H) + 0.5) * (SL.BBOX[3] - SL.BBOX[1]) / H)[:, None] * np.ones((1, W))
    S = scenes()
    print(f"{len(S)} Überflüge mit Rohbild; lese σ⁰ …", flush=True)
    def one(s):
        try:
            db, inc = read_raw(s.file)
        except Exception as e:
            print("  ", os.path.basename(s.file), e); return None, None
        if db.shape != water.shape:
            return None, None
        return (np.where(water, db, np.nan).astype("float32"),
                f"{s.orbit}{int(round(float(np.nanmedian(inc[water]))))}")
    from concurrent.futures import ThreadPoolExecutor        # GDAL gibt beim Lesen den GIL frei
    with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 2)) as ex:
        res = list(ex.map(one, [s for _, s in S.iterrows()]))
    DB = [r[0] for r in res]; track = [r[1] for r in res]
    S["spur"] = track
    ok = S.spur.notna().values
    S = S[ok].reset_index(drop=True); DB = [d for d, k in zip(DB, ok) if k]
    ref = {}
    for t, idx in S.groupby("spur").groups.items():                 # Referenz je Spur: 20 %-Quantil je Pixel
        if len(idx) >= 8:
            ref[t] = np.nanpercentile(np.stack([DB[i] for i in idx]), 20, axis=0)
    print("Bilder je Spur (Referenz ab 8):", S.spur.value_counts().to_dict())
    D = pd.read_csv(f"{B.RES}/breva_tage.csv", index_col=0, parse_dates=True)
    north_px = water & (lat >= SEG["nord"][0]) & (lat < SEG["nord"][1])
    rows, profs, R = [], [], {}
    for i, s in S.iterrows():
        lt = s.te.tz_convert("Europe/Rome")
        if lt.hour < 12 or s.spur not in ref:
            continue
        r = DB[i] - ref[s.spur]
        rec = {k: float(np.nanmedian(r[water & (lat >= a) & (lat < b)])) for k, (a, b) in SEG.items()}
        nr = r[north_px]; nr = nr[np.isfinite(nr)]
        rec["rau_nord"] = float((nr >= RAU).mean()) if nr.size else np.nan
        tiles = [np.nanmean(r[y:y + 10, x:x + 10][water[y:y + 10, x:x + 10]]) for y in range(0, H, 10) for x in range(0, W, 10)
                 if water[y:y + 10, x:x + 10].sum() >= 30]
        rec["flecken"] = float(np.nanstd(tiles)) if tiles else np.nan
        prof = []
        for a in LAT_BINS[:-1]:
            m = water & (lat >= a) & (lat < a + 0.01)
            prof.append(float(np.nanmedian(r[m])) if m.sum() >= 10 else np.nan)
        d = lt.normalize().tz_localize(None)
        rec.update(tag=d, zeit=lt.strftime("%H:%M"), spur=s.spur)
        try:
            z = np.load(s.wind)
            rec["richtung"] = float(z["dir"]); rec["richtung_quelle"] = str(z["dir_quelle"]) if "dir_quelle" in z else "modell"
            rec["kn_richtwert"] = float(np.nanmedian((z["v"] * SL.KN)[north_px]))
        except Exception:
            rec.update(richtung=np.nan, richtung_quelle="", kn_richtwert=np.nan)
        for c in ("sam_max", "col_max", "regen", "klasse", "breva14", "breva18", "sam_morgen", "sam_nord_std"):
            rec[c] = D[c].get(d, np.nan) if c in D else np.nan
        rows.append(rec); profs.append(prof); R[d] = r
    if not rows:
        sys.exit("keine Abendbilder mit Referenz")
    A = pd.DataFrame(rows).set_index("tag")
    keep = ~A.index.duplicated(keep="last")
    P = pd.DataFrame(profs, index=A.index, columns=[f"{a:.2f}" for a in LAT_BINS[:-1]])[keep]
    A = A[keep]
    A["regen"] = A.regen.fillna(0)
    A["anstieg"] = A.nord - A.sued
    A["gesamt"] = A[["sued", "mitte", "nord"]].mean(axis=1)

    def cat(r):
        if not np.isfinite(r.nord) or r.nord < RUHIG:
            return "ruhig"
        if r.richtung == 20:
            return "nordwind"
        if (r.sued >= STURM and r.mitte >= STURM) or (r.flecken >= FLECK and r.regen >= 2):
            return "gewitter_sturm"
        return "breva_typisch" if r.anstieg >= ANSTIEG else "sued_gleichmaessig"
    A["kategorie"] = [cat(r) for _, r in A.iterrows()]
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".png"):
            os.remove(os.path.join(OUT, f))
    A.round(3).to_csv(f"{OUT}/abende.csv")
    P.round(2).to_csv(f"{OUT}/profile.csv")
    M = A[A.index.month.isin(range(3, 11))]
    print(f"\n{len(A)} Abendbilder mit Referenz, März–Oktober {len(M)}")
    print(M.kategorie.value_counts().to_string())
    print("\nMedian je Kategorie (März–Oktober; dB über ruhig, kn nur Richtwert):")
    print(M.groupby("kategorie")[["sued", "mitte", "nord", "anstieg", "rau_nord", "flecken", "kn_richtwert", "sam_max", "col_max", "regen"]]
          .median().round(2).to_string())
    print("\nStationsziel breva14 je Kategorie (Anteil):")
    print(M.groupby("kategorie").breva14.mean().round(2).to_string())
    # Fetch-Prüfung
    sued = M[M.richtung == 200]
    therm = sued.klasse.isin(["Breva", "Breva schwach"]); syn = sued.klasse.isin(["synoptisch", "Regen/Gewitter", "ruhig"])
    bins = [-5, 2, 4, 6, 8, 30]
    grp = lambda X: X.groupby(pd.cut(X.gesamt, bins), observed=False)  # noqa: E731
    F = pd.DataFrame({"Anstieg thermisch": grp(sued[therm]).anstieg.median(), "n": grp(sued[therm]).size(),
                      "Anstieg ohne Ablauf": grp(sued[syn]).anstieg.median(), "n ohne": grp(sued[syn]).size()})
    print("\nFetch-Prüfung – Anstieg Nord−Süd (dB) bei ähnlicher Gesamtrauigkeit:")
    print(F.round(2).to_string())
    F.round(3).to_csv(f"{OUT}/fetch.csv")
    # Bilder
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for k, g in M.groupby("kategorie"):
        ax.plot(LAT_BINS[:-1] + 0.005, P.reindex(g.index).median().values, lw=2, label=f"{k} ({len(g)})")
    for name, la in (("Bellagio", 45.985), ("Menaggio", 46.02), ("Dervio", 46.077), ("Colico", 46.137), ("Domaso", 46.15), ("Sorico", 46.162)):
        ax.axvline(la, color="grey", lw=0.5, ls=":")
        ax.text(la, 0.02, name, rotation=90, fontsize=7, va="bottom", transform=ax.get_xaxis_transform())
    ax.axhline(0, color="black", lw=0.6)
    ax.set_xlabel("Breite (Süd → Nord)"); ax.set_ylabel("Rauigkeit über ruhig (dB)"); ax.legend(fontsize=8); ax.grid(alpha=0.3)
    ax.set_title("Mittleres Rauigkeitsprofil entlang des oberen Sees je Kategorie (März–Oktober)", fontsize=9)
    fig.tight_layout(); fig.savefig(f"{OUT}/profile.png", dpi=100); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(sued[syn].gesamt, sued[syn].anstieg, s=12, alpha=0.6, label="Südwind ohne thermischen Ablauf")
    ax.scatter(sued[therm].gesamt, sued[therm].anstieg, s=12, alpha=0.6, label="Breva (thermischer Ablauf)")
    ax.axhline(ANSTIEG, color="#d1495b", ls="--", lw=0.8)
    ax.set_xlabel("Gesamtrauigkeit (dB über ruhig)"); ax.set_ylabel("Anstieg Nord − Süd (dB)"); ax.legend(fontsize=8); ax.grid(alpha=0.3)
    ax.set_title("Fetch-Prüfung", fontsize=9)
    fig.tight_layout(); fig.savefig(f"{OUT}/fetch.png", dpi=100); plt.close(fig)

    def sheet(path, X, title):
        X = X[:24]
        if not len(X):
            return
        nc = 6; nr = int(np.ceil(len(X) / nc))
        fig, axs = plt.subplots(nr, nc, figsize=(2.3 * nc, 2.9 * nr), squeeze=False)
        for ax, (d, r) in zip(axs.flat, X.iterrows()):
            im = ax.imshow(np.where(water, R[d], np.nan), extent=(SL.BBOX[0], SL.BBOX[2], SL.BBOX[1], SL.BBOX[3]),
                           cmap="magma", vmin=-2, vmax=12)
            ax.set_aspect(1 / np.cos(np.radians(46))); ax.set_xticks([]); ax.set_yticks([])
            ax.set_title(f"{d:%d.%m.%y} N{r.nord:.1f}/M{r.mitte:.1f}/S{r.sued:.1f} dB\n"
                         f"Sam {r.sam_max:.0f} · Col {r.col_max:.0f} kn · ~{r.kn_richtwert:.0f} kn", fontsize=7)
        for ax in list(axs.flat)[len(X):]:
            ax.axis("off")
        fig.colorbar(im, ax=axs, shrink=0.5, label="dB über ruhig")
        fig.suptitle(title + "  (N/M/S = Nordbecken/Mitte/Süd; Sam/Col = Stationsmaximum 11–20 Uhr; ~kn = CMOD-Richtwert)", fontsize=8)
        fig.savefig(path, dpi=75, bbox_inches="tight"); plt.close(fig)
    for k, g in M.groupby("kategorie"):
        sheet(f"{OUT}/{k}.png", g.sort_values("nord", ascending=False), f"{k}: {len(g)} Abende")
    bt = M[M.kategorie == "breva_typisch"]
    if len(bt) >= 10:
        qs = np.nanpercentile(bt.nord, [0, 20, 40, 60, 80, 100]); parts = []
        for a, b in zip(qs[:-1], qs[1:]):
            g = bt[(bt.nord >= a) & (bt.nord <= b)]
            parts.append(g.sample(min(6, len(g)), random_state=0).sort_values("nord"))
        sheet(f"{OUT}/breva_stufen.png", pd.concat(parts), "Typischer Breva nach Rauigkeit im Nordbecken, je Zeile ein Fünftel (schwach → stark)")
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    for ax, st in zip(axs, ("sam_max", "col_max")):
        for k, g in M.groupby("kategorie"):
            ax.scatter(g[st], g.nord, s=12, alpha=0.7, label=k)
        ax.set_xlabel(f"{'Samolaco' if st == 'sam_max' else 'Colico'}: Maximum 11–20 Uhr (kn)"); ax.grid(alpha=0.3)
    axs[0].set_ylabel("Rauigkeit Nordbecken um 19:15 (dB über ruhig)"); axs[0].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(f"{OUT}/stationen.png", dpi=100); plt.close(fig)
    print(f"\ngeschrieben: {os.path.relpath(OUT)}/ (abende.csv, profile.csv/png, fetch.csv/png, Bildtafeln, breva_stufen.png, stationen.png)")


if __name__ == "__main__":
    main()
