"""Wassertemperatur des Comer Sees aus dem Satelliten (Copernicus Land, Lake Surface Water Temperature, Sentinel-3 SLSTR,
1 km, 10-Tages-Werte, 2016 – heute, wenige Tage Verzug) – über die CDSE-Zugangsdaten wie beim Sentinel-1-Download.

  python training/lake_temp.py laden       # 10-Tages-Mittel oberer See -> data/lake/lswt.csv
  python training/lake_temp.py analyse     # Einfluss auf den Breva (je Monat, gegen breva_tage.csv)

Hinweis: die Sammlung wird im Sentinel-Hub-Katalog von CDSE anhand des Titels gesucht
(„Lake Surface Water Temperature … Near Real Time“). Findet das Skript sie nicht, listet es alle Sammlungen mit „lake“.
"""
import argparse, os, sys
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "lake")
RES = os.path.join(ROOT, "results")
BBOX = (9.24, 45.98, 9.42, 46.18)     # oberer See (Bellagio/Varenna bis Sorico), LSWT nur auf Seepixeln
EVAL = """//VERSION=3
function setup() {
  return { input: [{ bands: ["LSWT", "QLEVEL", "dataMask"] }],
           output: [{ id: "t", bands: 1, sampleType: "FLOAT32" }, { id: "dataMask", bands: 1 }] };
}
function evaluatePixel(s) {
  var ok = s.dataMask == 1 && s.QLEVEL >= 3;
  return { t: [ok ? s.LSWT : NaN], dataMask: [ok ? 1 : 0] };
}
"""


def config():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from sar_lake import sh_config
    return sh_config()


LSWT_NRT = "byoc-401ca642-a169-4783-b1cf-cbd33e98eccb"   # CLMS LSWT 2016–heute, 10-täglich, 1 km (CDSE-Doku)


def find_collection(cfg):
    return LSWT_NRT


def _find_collection_catalog(cfg):
    from sentinelhub import SentinelHubCatalog
    cols = list(SentinelHubCatalog(config=cfg).get_collections())
    hits = [c for c in cols if "lake surface water temperature" in (c.get("title", "") + c.get("description", "")).lower()]
    nrt = [c for c in hits if "2016" in c.get("title", "") or "near real" in c.get("title", "").lower() or "nrt" in c["id"].lower()]
    if not (nrt or hits):
        print("Keine LSWT-Sammlung gefunden. Sammlungen mit 'lake':")
        for c in cols:
            if "lake" in (c.get("title", "") + c["id"]).lower():
                print("  ", c["id"], "-", c.get("title"))
        sys.exit(1)
    c = (nrt or hits)[0]
    print("Sammlung:", c["id"], "-", c.get("title"))
    return c["id"]


def to_celsius(v):
    v = np.asarray(v, float)
    return np.where(v > 200, v - 273.15, np.where(np.abs(v) > 100, v * 0.01, v))    # Kelvin | Rohwert ×0,01 | °C


def laden(start="2016-04-01"):
    from sentinelhub import BBox, CRS, DataCollection, SentinelHubStatistical, Geometry
    cfg = config()
    cid = find_collection(cfg)
    uuid = cid.replace("byoc-", "")
    try:
        coll = DataCollection.define_byoc(uuid, service_url=cfg.sh_base_url, name="lswt_como")
    except ValueError:
        coll = DataCollection.lswt_como
    end = pd.Timestamp.today().strftime("%Y-%m-%d")
    req = SentinelHubStatistical(
        aggregation=SentinelHubStatistical.aggregation(evalscript=EVAL, time_interval=(start, end),
                                                       aggregation_interval="P10D", resolution=(0.01, 0.01)),
        input_data=[SentinelHubStatistical.input_data(coll)],
        bbox=BBox(BBOX, crs=CRS.WGS84), config=cfg)
    js = req.get_data()[0]
    rows = []
    for it in js.get("data", []):
        st = it["outputs"]["t"]["bands"]["B0"]["stats"]
        if st.get("sampleCount", 0) - st.get("noDataCount", 0) < 3:
            continue
        rows.append({"von": it["interval"]["from"][:10], "bis": it["interval"]["to"][:10],
                     "lswt_roh": st.get("mean"), "pixel": st.get("sampleCount", 0) - st.get("noDataCount", 0)})
    d = pd.DataFrame(rows)
    if d.empty:
        sys.exit("keine Werte – Bandnamen (LSWT/QLEVEL) oder Zeitraum prüfen")
    d["lswt_c"] = to_celsius(d.lswt_roh).round(2)
    os.makedirs(OUT, exist_ok=True)
    d.to_csv(f"{OUT}/lswt.csv", index=False)
    print(f"{len(d)} 10-Tages-Werte {d.von.min()} – {d.bis.max()}, Wasser {d.lswt_c.min():.1f}–{d.lswt_c.max():.1f} °C")
    print(d.tail(6).to_string(index=False))


def daily():
    d = pd.read_csv(f"{OUT}/lswt.csv", parse_dates=["von", "bis"])
    mid = d.von + (d.bis - d.von) / 2
    s = pd.Series(d.lswt_c.values, index=mid).sort_index()
    return s.resample("D").mean().interpolate(limit=25)


def analyse():
    from sklearn.metrics import roc_auc_score
    D = pd.read_csv(f"{RES}/breva_tage.csv", index_col=0, parse_dates=True)
    w = daily().reindex(D.index)
    y = (D.klasse == "Breva").astype(int)
    sch = D.klasse.isin(["Breva", "Breva schwach", "ruhig"])
    clim = w.groupby(w.index.day_of_year).transform("mean")
    X = pd.DataFrame({"wasser": w, "wasser_anomalie": w - clim})
    try:
        import breva_daten as B
        F = B.features(B.load("era5")).reindex(D.index)
        X["luft_minus_wasser"] = F.tmax_see - w
    except Exception as e:
        print("ERA5 nicht geladen:", e)
    print("Wassertemperatur oberer See und Breva (Schönwettertage, AUC je Monat; 0,5 = kein Einfluss):")
    for c in X:
        a, wts = [], []
        for m in range(1, 13):
            sel = sch & (D.index.month == m) & X[c].notna()
            if y[sel].nunique() == 2 and sel.sum() >= 30:
                a.append(roc_auc_score(y[sel], X[c][sel])); wts.append(sel.sum())
        med1, med0 = X[c][sch & (y == 1)].median(), X[c][sch & (y == 0)].median()
        print(f"  {c:18s} Breva {med1:6.1f}  kein {med0:6.1f}  AUC je Monat {np.average(a, weights=wts) if a else np.nan:.2f}"
              f"  ({len(a)} Monate)")
    print("\nJe Monat (Median Wasser °C an Breva-Tagen / sonst):")
    for m in range(1, 13):
        sel = sch & (D.index.month == m)
        if sel.sum() >= 20:
            print(f"  {m:2d}: {X.wasser[sel & (y == 1)].median():5.1f} / {X.wasser[sel & (y == 0)].median():5.1f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["laden", "analyse"])
    a = ap.parse_args()
    laden() if a.step == "laden" else analyse()
