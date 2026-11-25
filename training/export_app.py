"""Daten für die App (app/) aus den Auswertungen erzeugen.

  python training/export_app.py

Schreibt
  app/breva.json              Satellitenfaktoren Spot / Station bei Breva, Breva-Klima je Monat, Stand
  app/img/breva_mittel.png    mittlerer Seewind an Breva-Abenden (Sentinel-1, 100 m) als Kartenauflage

Braucht results/sar_spots.csv (sar_lake.py stations), results/breva_samolaco_tage.csv bzw. results/breva_tage.csv
und für das Bild data/sar100/wind/*.npz + data/sar100/water_mask.npy.
"""
import glob, json, os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
APP = os.path.join(ROOT, "app")
SAR = os.path.join(ROOT, "data", "sar100")
BBOX = (9.20, 45.96, 9.46, 46.20)
KN = 1.943844
TZ = "Europe/Rome"
SPOTS = ["colico", "gera_lario", "sorico_punta", "domaso", "dervio", "cremia"]
# Stationen für Jetzt-korr. und ihr Breva-Sektor (Richtung, aus der der Breva an der Station ankommt)
STATIONS = {"samolaco": (112, 202), "colico": (225, 315), "morbegno": (200, 290), "sansiro": (180, 270),
            "vercana": (180, 270)}

# Farbskala wie die Windanimation in wingst (kn -> RGB)
STOPS = [(0, (59, 111, 209)), (6, (47, 163, 224)), (10, (54, 195, 192)), (14, (242, 211, 59)),
         (18, (245, 130, 44)), (22, (224, 54, 42)), (28, (163, 22, 95))]


def color(kn):
    kn = np.clip(kn, STOPS[0][0], STOPS[-1][0])
    out = np.zeros(kn.shape + (3,))
    for (a, ca), (b, cb) in zip(STOPS[:-1], STOPS[1:]):
        m = (kn >= a) & (kn <= b)
        f = ((kn - a) / (b - a))[m][:, None]
        out[m] = np.array(ca) * (1 - f) + np.array(cb) * f
    return out.astype(np.uint8)


def breva_evenings():
    S = pd.read_csv(f"{RES}/sar_spots.csv", parse_dates=["t_exakt"]).sort_values("t_exakt")
    S = S[S.t_exakt.diff().fillna(pd.Timedelta(hours=1)) > pd.Timedelta(minutes=5)]
    lt = S.t_exakt.dt.tz_convert(TZ)
    S["datum"] = lt.dt.tz_localize(None).dt.normalize()
    up = [k for k in ("colico", "gera_lario", "sorico_punta", "domaso") if k in S]
    S["see"] = S[up].mean(axis=1)
    rain = None
    f = f"{RES}/breva_sat_abende.csv"
    if os.path.exists(f):
        A = pd.read_csv(f, parse_dates=["t_exakt"])
        rain = A.set_index("t_exakt").regen
    S["regen"] = S.t_exakt.map(rain).fillna(0) if rain is not None else 0
    ev = (lt.dt.hour >= 12) & lt.dt.month.isin([4, 5, 6, 7, 8, 9]) & (S.dir == 200) & (S.regen < 1)
    return S, S[ev]


def factors(B):
    """Spot / Station zur Überflugstunde an Breva-Abenden (See ≥ 10 kn, Station ≥ 3 kn)."""
    out = {}
    for sp in SPOTS:
        if sp not in B:
            continue
        out[sp] = {}
        for st in STATIONS:
            c = f"st_{st}"
            if c not in B:
                continue
            x = B[(B.see >= 10) & (B[c] >= 3) & B[sp].notna()]
            if len(x) < 15:
                continue
            r = (x[sp] / x[c])
            out[sp][st] = {"median": round(float(r.median()), 2), "q25": round(float(r.quantile(.25)), 2),
                           "q75": round(float(r.quantile(.75)), 2), "n": int(len(x)),
                           "r": round(float(B[[sp, c]].dropna().corr(method="spearman").iloc[0, 1]), 2)}
    return out


def spot_ratio(B):
    """Spot / Mittel oberer See an Breva-Abenden: wie stark jeder Spot im Vergleich weht."""
    x = B[B.see >= 10]
    return {sp: round(float((x[sp] / x.see).median()), 2) for sp in SPOTS if sp in x and x[sp].notna().sum() > 20}


def climate():
    f = f"{RES}/breva_tage.csv"
    if os.path.exists(f):
        D = pd.read_csv(f, index_col=0, parse_dates=True)
        src = "breva_tage.csv (bereinigte Klassen)"
    else:
        D = pd.read_csv(f"{RES}/breva_samolaco_tage.csv", index_col=0, parse_dates=True)
        src = "breva_samolaco_tage.csv"
    out = {}
    for thr in (14, 18):
        c = f"breva{thr}"
        if c not in D:
            continue
        g = D.groupby(D.index.month)[c]
        out[str(thr)] = {str(m): {"p": round(float(v.mean()), 3), "tage": round(float(v.mean() * pd.Timestamp(2001, m, 1).days_in_month), 1)}
                         for m, v in g}
    return out, src, f"{D.index.year.min()}–{D.index.year.max()}"


def overlay(B):
    w = np.load(f"{SAR}/water_mask.npy")
    try:
        from scipy.ndimage import label
        lab, _ = label(w); sz = np.bincount(lab.ravel()); keep = sz >= 150; keep[0] = False; w = keep[lab]
    except ImportError:
        pass
    files = {}
    for f in glob.glob(f"{SAR}/wind/*.npz"):
        files[os.path.basename(f)[:15]] = f
    stems = [t.tz_convert("UTC").strftime("%Y%m%dT%H%M%S") for t in B[B.see >= 12].t_exakt]
    imgs = [np.load(files[s])["v"] * KN for s in stems if s in files]
    if len(imgs) < 3:
        print("  zu wenige Windbilder für das Mittelbild:", len(imgs)); return None
    med = np.nanmedian(np.stack(imgs), axis=0)
    rgba = np.zeros(med.shape + (4,), np.uint8)
    ok = w & np.isfinite(med)
    rgba[ok, :3] = color(med[ok]); rgba[ok, 3] = 215
    os.makedirs(f"{APP}/img", exist_ok=True)
    import matplotlib.image as mpimg
    mpimg.imsave(f"{APP}/img/breva_mittel.png", rgba)
    print(f"  Mittelbild aus {len(imgs)} Breva-Abenden (See ≥ 12 kn) -> app/img/breva_mittel.png")
    return len(imgs)


def main():
    S, B = breva_evenings()
    print(f"Breva-Abende (Apr–Sep, Süd, ohne Regen): {len(B)}, davon See ≥ 10 kn: {(B.see >= 10).sum()}")
    cl, src, yrs = climate()
    n_img = overlay(B)
    out = {
        "stand": pd.Timestamp.today().strftime("%Y-%m-%d"),
        "faktoren": factors(B),
        "spot_zu_see": spot_ratio(B),
        "stationen_sektor": {k: list(v) for k, v in STATIONS.items()},
        "klima": cl, "klima_quelle": src, "klima_jahre": yrs,
        "overlay": {"bild": "img/breva_mittel.png", "bbox": BBOX, "abende": n_img,
                    "jahre": f"{B.t_exakt.dt.year.min()}–{B.t_exakt.dt.year.max()}"},
        "sat_abende": int(len(B)),
    }
    json.dump(out, open(f"{APP}/breva.json", "w"), indent=1, ensure_ascii=False)
    print("Faktoren Spot / Station (Median):")
    for sp, d in out["faktoren"].items():
        print(f"  {sp:13s} " + "  ".join(f"{st} {v['median']:.2f} (r {v['r']:.2f})" for st, v in d.items()))
    print("Spot / Mittel oberer See:", out["spot_zu_see"])
    print("geschrieben: app/breva.json")


if __name__ == "__main__":
    main()
