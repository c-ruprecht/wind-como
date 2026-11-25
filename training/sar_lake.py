"""Satellitenwind auf dem oberen Comer See (100 m) und Auswahl der besten Messstation.

Sentinel-1 misst die Rauigkeit der Wasseroberfläche; daraus rechnet CMOD5.N (cmod5n.py) den Wind in 10 m. Der See ist
am oberen Ende 2–4 km breit, deshalb 100 m statt 300 m wie in wingst. Überflüge gegen 6–7 Uhr (Tivano) und 18–19 Uhr
(Ende Breva) Ortszeit; mittags gibt es keine Bilder.

Windrichtung für CMOD5.N: Auf dem See weht der Wind fast immer entlang der Seeachse (oberer See ~20° / 200°). Welche
der beiden Richtungen, sagt ICON am See (Open-Meteo, frühere Vorhersagen) zur Überflugstunde.

Schritte (Repo-Ordner, im conda-Env mit python):
  pip install sentinelhub rasterio
  export CDSE_CLIENT_ID=...  CDSE_CLIENT_SECRET=...      # wie in wingst (Copernicus Data Space, Sentinel Hub)
  python training/sar_lake.py download --start 2020-01-01   # VV + Einfallswinkel je Überflug, bis heute
  python training/sar_lake.py wind                          # Wassermaske, Richtung aus ICON, Wind je Bild
  python training/sar_lake.py stations                      # Spots gegen alle ARPA-Stationen -> beste Station

Ergebnis: data/sar100/…, results/sar_spots.csv (je Überflug Wind an den Spots und an allen Stationen),
          results/station_ranking.csv, results/sar_mean.png
"""
import argparse, glob, json, os, sys, time, urllib.error, urllib.parse, urllib.request
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sar100")
RES_DIR = os.path.join(ROOT, "results")
BBOX = (9.20, 45.96, 9.46, 46.20)            # oberer See: Sorico/Pian di Spagna bis Bellagio/Varenna
RES = 100                                    # m
AXIS = (20.0, 200.0)                         # Seeachse oberer See: Wind aus NNO (Tivano) oder SSW (Breva)
LAKE_CENTER = (46.07, 9.29)                  # für die ICON-Richtung
SPOTS = {"colico": (46.137, 9.372), "gera_lario": (46.168, 9.372), "sorico_punta": (46.162, 9.392),
         "domaso": (46.150, 9.335), "dervio": (46.077, 9.300), "cremia": (46.087, 9.276)}
EVALSCRIPT = """
//VERSION=3
function setup() {
  return { input: [{ bands: ["VV", "localIncidenceAngle", "dataMask"] }],
           output: { bands: 3, sampleType: "FLOAT32" } };
}
function evaluatePixel(s) { return [s.VV, s.localIncidenceAngle, s.dataMask]; }
"""
KN = 1.943844


# ---------------------------------------------------------------- 1. Download

def sh_config():
    from sentinelhub import SHConfig
    cfg = SHConfig()
    cfg.sh_client_id = os.environ.get("CDSE_CLIENT_ID", "")
    cfg.sh_client_secret = os.environ.get("CDSE_CLIENT_SECRET", "")
    if not cfg.sh_client_id:
        raise SystemExit("CDSE_CLIENT_ID / CDSE_CLIENT_SECRET fehlen (siehe Kopf der Datei).")
    cfg.sh_base_url = "https://sh.dataspace.copernicus.eu"
    cfg.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    return cfg


def download(start, end, workers=6):
    from sentinelhub import (BBox, CRS, DataCollection, MimeType, SentinelHubCatalog, SentinelHubRequest,
                             bbox_to_dimensions)
    import rasterio
    from rasterio.transform import from_bounds
    cfg = sh_config()
    s1 = DataCollection.SENTINEL1_IW.define_from("s1iw_cdse", service_url=cfg.sh_base_url)
    bbox = BBox(BBOX, crs=CRS.WGS84)
    size = bbox_to_dimensions(bbox, resolution=RES)
    items = list(SentinelHubCatalog(config=cfg).search(s1, bbox=bbox, time=(start, end)))
    # benachbarte Kacheln desselben Überflugs (wenige Sekunden auseinander) ergeben dasselbe Mosaik: nur eine behalten
    items.sort(key=lambda it: it["properties"]["datetime"])
    keep, last = [], None
    for it in items:
        t = pd.Timestamp(it["properties"]["datetime"])
        if last is None or t - last > pd.Timedelta(minutes=5):
            keep.append(it)
        last = t
    items = keep
    print(f"{len(items)} Überflüge, Bildgröße {size} Pixel à {RES} m", flush=True)
    os.makedirs(f"{OUT}/raw", exist_ok=True)
    meta, todo = [], []
    for it in items:
        t = pd.Timestamp(it["properties"]["datetime"])
        orbit = it["properties"].get("sat:orbit_state", "")
        fn = f"{OUT}/raw/{t:%Y%m%dT%H%M%S}_{orbit[:3]}.tif"
        meta.append(dict(file=os.path.basename(fn), time=t.isoformat(), orbit=orbit, id=it["id"]))
        if not os.path.exists(fn) and fn not in {f for _, f in todo}:
            todo.append((t, fn))
    print(f"  {len(todo)} fehlen noch, {workers} parallel", flush=True)

    def fetch(t, fn):
        req = SentinelHubRequest(
            evalscript=EVALSCRIPT,
            input_data=[SentinelHubRequest.input_data(
                data_collection=s1, time_interval=(t - pd.Timedelta(minutes=2), t + pd.Timedelta(minutes=2)),
                other_args={"processing": {"backCoeff": "SIGMA0_ELLIPSOID", "orthorectify": True,
                                           "demInstance": "COPERNICUS_30", "speckleFilter": {"type": "NONE"}}})],
            responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
            bbox=bbox, size=size, config=cfg)
        for attempt in range(5):
            try:
                arr = req.get_data()[0]
                break
            except Exception as e:
                if attempt == 4:
                    return f"Fehler {os.path.basename(fn)}: {e}"
                time.sleep(10 * (attempt + 1))
        tmp = fn + ".part"
        with rasterio.open(tmp, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=3, dtype="float32",
                           crs="EPSG:4326", transform=from_bounds(*BBOX, arr.shape[1], arr.shape[0]), compress="deflate") as dst:
            for b in range(3):
                dst.write(arr[:, :, b].astype("float32"), b + 1)
        os.replace(tmp, fn)
        return None

    from concurrent.futures import ThreadPoolExecutor, as_completed
    new = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(fetch, t, fn) for t, fn in todo]
        for f in as_completed(futs):
            err = f.result()
            if err:
                print(" ", err, flush=True)
            else:
                new += 1
                if new % 50 == 0:
                    print(f"  {new}/{len(todo)} neue Bilder …", flush=True)
    pd.DataFrame(meta).drop_duplicates("file").to_csv(f"{OUT}/scenes.csv", index=False)
    print(f"fertig: {new} neue Bilder")


# ---------------------------------------------------------------- 2. Wind

def icon_direction(times):
    """ICON-Windrichtung (10 m) am See zu den Überflugstunden, jahresweise von Open-Meteo, zwischengespeichert."""
    import ssl
    try:
        import certifi; ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()
    os.makedirs(f"{OUT}/icon", exist_ok=True)
    parts = []
    today = pd.Timestamp.today().normalize()
    for y in sorted({t.year for t in times}):
        f = f"{OUT}/icon/{y}.csv"
        if not os.path.exists(f) or y == today.year:
            end = min(pd.Timestamp(f"{y}-12-31"), today - pd.Timedelta(days=1))
            h = None
            for model, base in (("icon_seamless", "https://historical-forecast-api.open-meteo.com/v1/forecast"),
                                ("era5", "https://archive-api.open-meteo.com/v1/archive")):
                q = dict(latitude=LAKE_CENTER[0], longitude=LAKE_CENTER[1], models=model,
                         hourly="wind_speed_10m,wind_direction_10m", wind_speed_unit="kn", timezone="UTC",
                         start_date=f"{y}-01-01", end_date=end.strftime("%Y-%m-%d"))
                url = base + "?" + urllib.parse.urlencode(q)
                for i in range(5):
                    try:
                        with urllib.request.urlopen(url, timeout=120, context=ctx) as r:
                            h = json.loads(r.read())["hourly"]
                        break
                    except urllib.error.HTTPError as e:
                        if e.code == 400:
                            break
                        print("  ", model, y, e); time.sleep(20 * (i + 1))
                    except Exception as e:
                        print("  ", model, y, e); time.sleep(20 * (i + 1))
                # ICON-Archiv beginnt erst ~2022: Jahr ohne Werte -> ERA5
                if h and sum(v is not None for v in h["wind_direction_10m"]) > 0.5 * len(h["time"]):
                    print(f"   Modellwind {y}: {model}", flush=True)
                    break
                h = None
            if h is None:
                print("   kein Modellwind für", y); continue
            pd.DataFrame({"time": h["time"], "ws": h["wind_speed_10m"], "wd": h["wind_direction_10m"]}).to_csv(f, index=False)
        parts.append(pd.read_csv(f))
    d = pd.concat(parts); d["time"] = pd.to_datetime(d.time, utc=True)
    return d.drop_duplicates("time").set_index("time")


def snap_axis(wd):
    """Modellrichtung auf die Seeachse legen: Wind aus NNO oder SSW."""
    diff = lambda a, b: abs((a - b + 180) % 360 - 180)
    return AXIS[0] if diff(wd, AXIS[0]) <= diff(wd, AXIS[1]) else AXIS[1]


def clean_mask(water, min_px=150):
    """Kleine Einzelflecken entfernen (Land, das wie Wasser aussieht: glatte Flächen, Hangschatten).
    Der See, die Bucht von Piona und der Lago di Mezzola sind groß genug und bleiben."""
    from scipy.ndimage import label
    lab, n = label(water)
    sizes = np.bincount(lab.ravel())
    keep = np.zeros_like(sizes, bool); keep[1:] = sizes[1:] >= min_px
    return keep[lab]


def wind(force=False):
    import rasterio
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from cmod5n import cmod5n_inverse
    from scipy.ndimage import binary_erosion
    sc = pd.read_csv(f"{OUT}/scenes.csv")
    sc["t"] = pd.to_datetime(sc.time, utc=True).dt.round("h")
    os.makedirs(f"{OUT}/wind", exist_ok=True)
    # Wassermaske aus dem Median aller Bilder (Wasser dunkel, Land und Berge hell), Otsu-Schwelle
    stack = []
    for f in sc.file:
        p = f"{OUT}/raw/{f}"
        if os.path.exists(p):
            with rasterio.open(p) as r:
                vv, m = r.read(1), r.read(3)
            stack.append(np.where(m > 0, vv, np.nan))
    med = 10 * np.log10(np.clip(np.nanmedian(np.stack(stack), axis=0), 1e-6, None))
    vals = med[np.isfinite(med)]
    hist, edges = np.histogram(vals, bins=200); mids = (edges[:-1] + edges[1:]) / 2
    w0 = np.cumsum(hist); w1 = w0[-1] - w0
    m0 = np.cumsum(hist * mids) / np.maximum(w0, 1); m1 = (np.sum(hist * mids) - np.cumsum(hist * mids)) / np.maximum(w1, 1)
    thr = mids[np.argmax(w0 * w1 * (m0 - m1) ** 2)]
    water = clean_mask(binary_erosion(med < thr, iterations=2))   # 200 m Abstand zum Ufer, ohne Einzelflecken
    np.save(f"{OUT}/water_mask.npy", water)
    print(f"Wasser/Land-Schwelle {thr:.1f} dB, Wassermaske {water.sum()} Pixel à {RES} m")
    icon = icon_direction(sorted(sc.t.unique()))
    done = new = 0
    skip = {"kein Rohbild": [], "keine Modellrichtung": [], "Fehler": []}
    for _, row in sc.iterrows():
        p = f"{OUT}/raw/{row.file}"; out = f"{OUT}/wind/{row.file[:-4]}.npz"
        if not os.path.exists(p):
            skip["kein Rohbild"].append(row.t.year); continue
        if not force and os.path.exists(out):
            done += 1; continue
        if row.t not in icon.index or pd.isna(icon.wd.get(row.t)):
            skip["keine Modellrichtung"].append(row.t.year); continue
        wd = snap_axis(float(icon.wd[row.t]))
        try:
            with rasterio.open(p) as r:
                vv, inc, m = r.read(1), r.read(2), r.read(3)
        except Exception as e:
            skip["Fehler"].append(row.t.year); print("  Fehler", row.file, e); continue
        if vv.shape != water.shape:
            skip["Fehler"].append(row.t.year); print("  andere Bildgröße", row.file, vv.shape); continue
        heading = 348.0 if str(row.orbit).lower().startswith("asc") else 192.0
        phi = (wd - (heading + 90.0) % 360) % 360
        ok = water & (m > 0) & np.isfinite(vv) & (vv > 0)
        v = np.full(vv.shape, np.nan)
        v[ok] = cmod5n_inverse(vv[ok], phi, inc[ok])
        np.savez_compressed(out, v=v.astype("float32"), dir=wd, icon_kn=float(icon.ws[row.t]), time=str(row.t))
        new += 1
        if new % 100 == 0:
            print(f"  {new} Windbilder neu gerechnet (zuletzt {row.file[:8]}) …", flush=True)
    print(f"Wind gerechnet: {new} neu, {done} vorhanden")
    for why, ys in skip.items():
        if ys:
            print(f"  übersprungen ({why}): {len(ys)} –", dict(sorted(pd.Series(ys).value_counts().items())))
    have = pd.Series([os.path.basename(f)[:4] for f in glob.glob(f"{OUT}/wind/*.npz")]).value_counts().sort_index()
    print("  Windbilder je Jahr:", dict(have))


# ---------------------------------------------------------------- 3. Stationen bewerten

def spot_pixels(water):
    H, W = water.shape
    ys, xs = np.where(water)
    lat = BBOX[3] - (ys + 0.5) / H * (BBOX[3] - BBOX[1]); lon = BBOX[0] + (xs + 0.5) / W * (BBOX[2] - BBOX[0])
    sel = {}
    for k, (la, lo) in SPOTS.items():
        d = np.hypot((lat - la) * 111.2, (lon - lo) * 111.2 * np.cos(np.radians(la)))
        idx = np.argsort(d)[:25]
        sel[k] = idx[d[idx] <= 2.0]                             # 25 nächste Wasserpixel bis 2 km (Spots am Ufer)
    return ys, xs, sel


def auc(score, label):
    s = pd.Series(score).rank(); pos = label.sum(); neg = len(label) - pos
    return np.nan if pos == 0 or neg == 0 else float((s[label].sum() - pos * (pos + 1) / 2) / (pos * neg))


def stations():
    water = clean_mask(np.load(f"{OUT}/water_mask.npy"))
    ys, xs, sel = spot_pixels(water)
    obs = {}
    for f in glob.glob(os.path.join(ROOT, "data", "arpa", "*_wind.csv")):
        d = pd.read_csv(f, parse_dates=["time"]).set_index("time")
        d.index = pd.DatetimeIndex(d.index).tz_convert("UTC")
        obs[os.path.basename(f)[:-9]] = d.sort_index()
    rows = []
    for f in sorted(glob.glob(f"{OUT}/wind/*.npz")):
        z = np.load(f); v = z["v"] * KN; t = pd.Timestamp(str(z["time"]))
        t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
        te = pd.Timestamp(os.path.basename(f)[:15], tz="UTC")           # genaue Überflugzeit aus dem Dateinamen
        rec = {"time": t, "t_exakt": te, "file": f, "dir": float(z["dir"]), "icon_kn": float(z["icon_kn"])}
        for k, idx in sel.items():
            vals = v[ys[idx], xs[idx]]; vals = vals[np.isfinite(vals)]
            rec[k] = float(np.median(vals)) if vals.size >= 5 else np.nan
        lab = te.ceil("h")                                              # Stationsstunde, die den Überflug enthält
        day = te.tz_convert("Europe/Rome").normalize()
        for st, d in obs.items():
            rec[f"st_{st}"] = float(d.kn.get(lab, np.nan))
            nm = d.kn.loc[day + pd.Timedelta(hours=12):day + pd.Timedelta(hours=20)]   # Nachmittag 11–20 Uhr Ortszeit
            rec[f"max_{st}"] = float(nm.max()) if len(nm) >= 6 else np.nan
        rows.append(rec)
    S = pd.DataFrame(rows)
    # benachbarte Kacheln desselben Überflugs sind identisch: einmal zählen
    S = S.sort_values("t_exakt")
    S = S[S.t_exakt.diff().fillna(pd.Timedelta(hours=1)) > pd.Timedelta(minutes=5)].reset_index(drop=True)
    os.makedirs(RES_DIR, exist_ok=True)
    S.drop(columns="file").to_csv(f"{RES_DIR}/sar_spots.csv", index=False)
    spots_up = [k for k in ("colico", "gera_lario", "sorico_punta", "domaso") if k in S]
    S["see"] = S[spots_up].mean(axis=1)                         # Wind auf dem oberen See
    loc = S.time.dt.tz_convert("Europe/Rome")
    S["abends"] = loc.dt.hour >= 12
    S["sommer"] = loc.dt.month.isin([4, 5, 6, 7, 8, 9])
    S["breva"] = S.abends & S.sommer & (S.dir == AXIS[1])          # Abendüberflug, Modellwind aus Süd
    out = []
    for st in obs:
        c = f"st_{st}"
        for name, m in (("alle", S.index == S.index), ("Sommerabend Süd (Breva)", S.breva),
                        ("morgens (Tivano)", ~S.abends)):
            x = S[m & S[c].notna() & S.see.notna()]
            if len(x) < 20:
                continue
            strong = x.see >= 12
            out.append(dict(station=st, fall=name, n=len(x), r=round(x[c].corr(x.see), 2),
                            verhaeltnis_see_zu_station=round(float((x.see / x[c]).where(x[c] >= 3).median()), 2),
                            auc_see_ab_12kn=round(auc(x[c].values, strong.values), 2),
                            see_ab_12kn=int(strong.sum())))
    for name, m in (("alle", S.index == S.index), ("Sommerabend Süd (Breva)", S.breva)):
        x = S[m & S.see.notna()]
        if len(x) >= 20:
            out.append(dict(station="Modell (ICON ab 2022, sonst ERA5)", fall=name, n=len(x), r=round(x.icon_kn.corr(x.see), 2),
                            verhaeltnis_see_zu_station=round(float((x.see / x.icon_kn).where(x.icon_kn >= 3).median()), 2),
                            auc_see_ab_12kn=round(auc(x.icon_kn.values, (x.see >= 12).values), 2), see_ab_12kn=int((x.see >= 12).sum())))
    R = pd.DataFrame(out).sort_values(["fall", "auc_see_ab_12kn"], ascending=[True, False])
    R.to_csv(f"{RES_DIR}/station_ranking.csv", index=False)
    pd.set_option("display.width", 200)
    print(f"{len(S)} Überflüge. Wind auf dem oberen See (Mittel Colico, Gera Lario, Sorico, Domaso) gegen jede Station:")
    print(R.to_string(index=False))
    print("\nr: Zusammenhang; auc: wie gut die Station Überflüge mit ≥ 12 kn auf dem See erkennt (1 = perfekt, 0,5 = Zufall);"
          "\nVerhältnis: See / Station (Median) – der Faktor, mit dem man die Station auf den See umrechnet.")
    # Welche Station passt zu welchem Spot? r bei Breva-Abenden und bei allen Überflügen
    for name, m in (("Breva-Abende (Apr–Sep, Süd)", S.breva), ("alle Überflüge", S.index == S.index)):
        M = {}
        for st in obs:
            c = f"st_{st}"
            M[st] = {k: round(S.loc[m, [c, k]].dropna()[c].corr(S.loc[m, [c, k]].dropna()[k]), 2)
                     for k in SPOTS if k in S and S.loc[m, [c, k]].dropna().shape[0] >= 20}
        M = pd.DataFrame(M).T
        if not M.empty:
            M = M.loc[M.mean(axis=1).sort_values(ascending=False).index]
            print(f"\nZusammenhang r Station (Zeile) – Satellitenwind am Spot (Spalte), {name}:")
            print(M.to_string())
            M.to_csv(f"{RES_DIR}/station_spot_r_{'breva' if 'Breva' in name else 'alle'}.csv")
    breva_scenes(S, water, list(obs))
    # Karte: mittlerer Wind bei Sommerabenden mit Breva auf dem See
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        ev = S[S.breva & (S.see >= 8)]
        files = {}
        for f in glob.glob(f"{OUT}/wind/*.npz"):
            tt = pd.Timestamp(str(np.load(f)["time"]))
            files[tt.tz_localize("UTC") if tt.tzinfo is None else tt.tz_convert("UTC")] = f
        imgs = [np.load(files[t])["v"] for t in ev.time if t in files]
        if imgs:
            arr = np.nanmedian(np.stack(imgs), axis=0) * KN
            plt.figure(figsize=(6, 6))
            plt.imshow(np.where(water, arr, np.nan), extent=(BBOX[0], BBOX[2], BBOX[1], BBOX[3]), cmap="turbo", vmin=0, vmax=20)
            plt.colorbar(label="Wind auf dem Wasser (kn), Median Sommerabende mit Breva")
            for k, (la, lo) in SPOTS.items():
                plt.plot(lo, la, "k^"); plt.text(lo + 0.004, la, k, fontsize=8)
            plt.title(f"Sentinel-1, {RES} m, {len(ev)} Sommerabende")
            plt.savefig(f"{RES_DIR}/sar_mean.png", dpi=150, bbox_inches="tight")
    except Exception as e:
        print("Karte nicht gezeichnet:", e)


def breva_scenes(S, water, stations, top=12):
    """Abendüberflüge (Apr–Sep, Süd) mit Breva auf dem See: Liste und Bildtafel, Vergleich mit den Stationen."""
    B = S[S.breva & S.see.notna()].sort_values("see", ascending=False)
    if B.empty:
        print("\nKeine Breva-Abendüberflüge gefunden."); return
    cols = ["see"] + [k for k in SPOTS if k in B] + [c for st in ("samolaco", "vercana", "colico", "morbegno")
                                                     for c in (f"st_{st}", f"max_{st}") if c in B]
    L = B.assign(ortszeit=B.t_exakt.dt.tz_convert("Europe/Rome").dt.strftime("%Y-%m-%d %H:%M"))[["ortszeit"] + cols]
    L.round(1).to_csv(f"{RES_DIR}/breva_szenen.csv", index=False)
    print(f"\nBreva-Abendüberflüge (Apr–Sep, Modellwind Süd): {len(B)}, davon See ≥ 10 kn: {(B.see >= 10).sum()}, "
          f"≥ 12 kn: {(B.see >= 12).sum()}, ≥ 14 kn: {(B.see >= 14).sum()}")
    print("Stärkste Fälle (st_ = Station zur Überflugstunde, max_ = Nachmittagsmaximum 11–20 Uhr):")
    print(L.head(25).round(1).to_string(index=False))
    for st in stations:
        c, mx = f"st_{st}", f"max_{st}"
        x = B[(B.see >= 10) & B[c].notna()]
        if len(x) >= 5:
            print(f"  See ≥ 10 kn (n={len(x)}): {st:10s} zur Überflugstunde Median {x[c].median():4.1f} kn, "
                  f"See/Station {(x.see / x[c].clip(lower=1)).median():.2f}; "
                  f"Nachmittagsmax {x[mx].median():4.1f} kn, See/Max {(x.see / x[mx].clip(lower=1)).median():.2f}")
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        T = B.head(top); n = len(T); nc = 4; nr = int(np.ceil(n / nc))
        fig, axs = plt.subplots(nr, nc, figsize=(4 * nc, 4.3 * nr), squeeze=False)
        for ax, (_, r) in zip(axs.flat, T.iterrows()):
            v = np.load(r.file)["v"] * KN
            im = ax.imshow(np.where(water, v, np.nan), extent=(BBOX[0], BBOX[2], BBOX[1], BBOX[3]), cmap="turbo", vmin=0, vmax=22)
            lt = r.t_exakt.tz_convert("Europe/Rome")
            sam = f"Samolaco {r.get('st_samolaco', np.nan):.0f} (max {r.get('max_samolaco', np.nan):.0f})"
            ax.set_title(f"{lt:%d.%m.%Y %H:%M}\nSee {r.see:.0f} kn · {sam}", fontsize=9)
            ax.set_xticks([]); ax.set_yticks([])
        for ax in list(axs.flat)[n:]:
            ax.axis("off")
        fig.colorbar(im, ax=axs, shrink=0.6, label="kn")
        fig.savefig(f"{RES_DIR}/breva_top.png", dpi=110, bbox_inches="tight")
    except Exception as e:
        print("Bildtafel nicht gezeichnet:", e)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["download", "wind", "stations"])
    ap.add_argument("--start", default="2020-01-01")
    ap.add_argument("--end", default=pd.Timestamp.today().strftime("%Y-%m-%d"))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    if a.step == "download":
        download(a.start, a.end, a.workers)
    elif a.step == "wind":
        wind(a.force)
    else:
        stations()
