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
import argparse, glob, json, os, sys, time, urllib.parse, urllib.request
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


def download(start, end):
    from sentinelhub import (BBox, CRS, DataCollection, MimeType, SentinelHubCatalog, SentinelHubRequest,
                             bbox_to_dimensions)
    import rasterio
    from rasterio.transform import from_bounds
    cfg = sh_config()
    s1 = DataCollection.SENTINEL1_IW.define_from("s1iw_cdse", service_url=cfg.sh_base_url)
    bbox = BBox(BBOX, crs=CRS.WGS84)
    size = bbox_to_dimensions(bbox, resolution=RES)
    items = list(SentinelHubCatalog(config=cfg).search(s1, bbox=bbox, time=(start, end)))
    print(f"{len(items)} Überflüge, Bildgröße {size} Pixel à {RES} m", flush=True)
    os.makedirs(f"{OUT}/raw", exist_ok=True)
    meta, new = [], 0
    for it in items:
        t = pd.Timestamp(it["properties"]["datetime"])
        orbit = it["properties"].get("sat:orbit_state", "")
        fn = f"{OUT}/raw/{t:%Y%m%dT%H%M%S}_{orbit[:3]}.tif"
        meta.append(dict(file=os.path.basename(fn), time=t.isoformat(), orbit=orbit, id=it["id"]))
        if os.path.exists(fn):
            continue
        req = SentinelHubRequest(
            evalscript=EVALSCRIPT,
            input_data=[SentinelHubRequest.input_data(
                data_collection=s1, time_interval=(t - pd.Timedelta(minutes=2), t + pd.Timedelta(minutes=2)),
                other_args={"processing": {"backCoeff": "SIGMA0_ELLIPSOID", "orthorectify": True,
                                           "demInstance": "COPERNICUS_30", "speckleFilter": {"type": "NONE"}}})],
            responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
            bbox=bbox, size=size, config=cfg)
        try:
            arr = req.get_data()[0]
        except Exception as e:
            print("  Fehler", fn, e); continue
        with rasterio.open(fn, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=3, dtype="float32",
                           crs="EPSG:4326", transform=from_bounds(*BBOX, arr.shape[1], arr.shape[0]), compress="deflate") as dst:
            for b in range(3):
                dst.write(arr[:, :, b].astype("float32"), b + 1)
        new += 1
        if new % 25 == 0:
            print(f"  {new} neue Bilder …", flush=True)
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
            q = dict(latitude=LAKE_CENTER[0], longitude=LAKE_CENTER[1], models="icon_seamless",
                     hourly="wind_speed_10m,wind_direction_10m", wind_speed_unit="kn", timezone="UTC",
                     start_date=f"{y}-01-01", end_date=end.strftime("%Y-%m-%d"))
            url = "https://historical-forecast-api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(q)
            for i in range(5):
                try:
                    with urllib.request.urlopen(url, timeout=120, context=ctx) as r:
                        h = json.loads(r.read())["hourly"]; break
                except Exception as e:
                    print("   ICON", y, e); time.sleep(20 * (i + 1))
            else:
                continue
            pd.DataFrame({"time": h["time"], "ws": h["wind_speed_10m"], "wd": h["wind_direction_10m"]}).to_csv(f, index=False)
        parts.append(pd.read_csv(f))
    d = pd.concat(parts); d["time"] = pd.to_datetime(d.time, utc=True)
    return d.drop_duplicates("time").set_index("time")


def snap_axis(wd):
    """Modellrichtung auf die Seeachse legen: Wind aus NNO oder SSW."""
    diff = lambda a, b: abs((a - b + 180) % 360 - 180)
    return AXIS[0] if diff(wd, AXIS[0]) <= diff(wd, AXIS[1]) else AXIS[1]


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
    water = binary_erosion(med < thr, iterations=2)          # 200 m Abstand zum Ufer: Mischpixel und Hangschatten
    np.save(f"{OUT}/water_mask.npy", water)
    print(f"Wasser/Land-Schwelle {thr:.1f} dB, Wassermaske {water.sum()} Pixel à {RES} m")
    icon = icon_direction(sorted(sc.t.unique()))
    done = new = 0
    for _, row in sc.iterrows():
        p = f"{OUT}/raw/{row.file}"; out = f"{OUT}/wind/{row.file[:-4]}.npz"
        if not os.path.exists(p):
            continue
        if not force and os.path.exists(out):
            done += 1; continue
        if row.t not in icon.index or pd.isna(icon.wd.get(row.t)):
            continue
        wd = snap_axis(float(icon.wd[row.t]))
        with rasterio.open(p) as r:
            vv, inc, m = r.read(1), r.read(2), r.read(3)
        heading = 348.0 if str(row.orbit).lower().startswith("asc") else 192.0
        phi = (wd - (heading + 90.0) % 360) % 360
        ok = water & (m > 0) & np.isfinite(vv) & (vv > 0)
        v = np.full(vv.shape, np.nan)
        v[ok] = cmod5n_inverse(vv[ok], phi, inc[ok])
        np.savez_compressed(out, v=v.astype("float32"), dir=wd, icon_kn=float(icon.ws[row.t]), time=str(row.t))
        new += 1
    print(f"Wind gerechnet: {new} neu, {done} vorhanden")


# ---------------------------------------------------------------- 3. Stationen bewerten

def spot_pixels(water):
    H, W = water.shape
    ys, xs = np.where(water)
    lat = BBOX[3] - (ys + 0.5) / H * (BBOX[3] - BBOX[1]); lon = BBOX[0] + (xs + 0.5) / W * (BBOX[2] - BBOX[0])
    sel = {}
    for k, (la, lo) in SPOTS.items():
        d = np.hypot((lat - la) * 111.2, (lon - lo) * 111.2 * np.cos(np.radians(la)))
        idx = np.argsort(d)[:15]
        sel[k] = idx[d[idx] <= 1.2]                             # bis 1,2 km vom Spot aufs Wasser
    return ys, xs, sel


def auc(score, label):
    s = pd.Series(score).rank(); pos = label.sum(); neg = len(label) - pos
    return np.nan if pos == 0 or neg == 0 else float((s[label].sum() - pos * (pos + 1) / 2) / (pos * neg))


def stations():
    water = np.load(f"{OUT}/water_mask.npy")
    ys, xs, sel = spot_pixels(water)
    obs = {os.path.basename(f)[:-9]: pd.read_csv(f, parse_dates=["time"]).set_index("time")
           for f in glob.glob(os.path.join(ROOT, "data", "arpa", "*_wind.csv"))}
    rows = []
    for f in sorted(glob.glob(f"{OUT}/wind/*.npz")):
        z = np.load(f); v = z["v"] * KN; t = pd.Timestamp(str(z["time"]))
        t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
        rec = {"time": t, "dir": float(z["dir"]), "icon_kn": float(z["icon_kn"])}
        for k, idx in sel.items():
            vals = v[ys[idx], xs[idx]]; vals = vals[np.isfinite(vals)]
            rec[k] = float(np.median(vals)) if vals.size >= 5 else np.nan
        for st, d in obs.items():
            rec[f"st_{st}"] = float(d.kn.get(t, np.nan))
        rows.append(rec)
    S = pd.DataFrame(rows)
    os.makedirs(RES_DIR, exist_ok=True)
    S.to_csv(f"{RES_DIR}/sar_spots.csv", index=False)
    spots_up = [k for k in ("colico", "gera_lario", "sorico_punta", "domaso") if k in S]
    S["see"] = S[spots_up].mean(axis=1)                         # Wind auf dem oberen See
    loc = S.time.dt.tz_convert("Europe/Rome")
    S["abends"] = loc.dt.hour >= 12
    S["sommer"] = loc.dt.month.isin([5, 6, 7, 8, 9])
    out = []
    for st in obs:
        c = f"st_{st}"
        for name, m in (("alle", S.index == S.index), ("Sommerabend (Breva)", S.abends & S.sommer),
                        ("morgens (Tivano)", ~S.abends)):
            x = S[m & S[c].notna() & S.see.notna()]
            if len(x) < 20:
                continue
            strong = x.see >= 12
            out.append(dict(station=st, fall=name, n=len(x), r=round(x[c].corr(x.see), 2),
                            verhaeltnis_see_zu_station=round(float((x.see / x[c]).where(x[c] >= 3).median()), 2),
                            auc_see_ab_12kn=round(auc(x[c].values, strong.values), 2),
                            see_ab_12kn=int(strong.sum())))
    for name, m in (("alle", S.index == S.index), ("Sommerabend (Breva)", S.abends & S.sommer)):
        x = S[m & S.see.notna()]
        if len(x) >= 20:
            out.append(dict(station="ICON (Modell)", fall=name, n=len(x), r=round(x.icon_kn.corr(x.see), 2),
                            verhaeltnis_see_zu_station=round(float((x.see / x.icon_kn).where(x.icon_kn >= 3).median()), 2),
                            auc_see_ab_12kn=round(auc(x.icon_kn.values, (x.see >= 12).values), 2), see_ab_12kn=int((x.see >= 12).sum())))
    R = pd.DataFrame(out).sort_values(["fall", "auc_see_ab_12kn"], ascending=[True, False])
    R.to_csv(f"{RES_DIR}/station_ranking.csv", index=False)
    pd.set_option("display.width", 200)
    print(f"{len(S)} Überflüge. Wind auf dem oberen See (Mittel Colico, Gera Lario, Sorico, Domaso) gegen jede Station:")
    print(R.to_string(index=False))
    print("\nr: Zusammenhang; auc: wie gut die Station Überflüge mit ≥ 12 kn auf dem See erkennt (1 = perfekt, 0,5 = Zufall);"
          "\nVerhältnis: See / Station (Median) – der Faktor, mit dem man die Station auf den See umrechnet.")
    # Karte: mittlerer Wind bei Sommerabenden mit Breva auf dem See
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        ev = S[S.abends & S.sommer & (S.see >= 8)]
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


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["download", "wind", "stations"])
    ap.add_argument("--start", default="2020-01-01")
    ap.add_argument("--end", default=pd.Timestamp.today().strftime("%Y-%m-%d"))
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.step == "download":
        download(a.start, a.end)
    elif a.step == "wind":
        wind(a.force)
    else:
        stations()
