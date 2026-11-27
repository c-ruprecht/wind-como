"""Same-Day-Modell, stündlich: Was bringt der Rest des Tages? – Prüfung, ob Messungen (Wind + ARPA-Treiber) helfen.

Für jeden Tag und jede volle Stunde H = 8 … 17 Uhr (Ortszeit) wird vorhergesagt, mit allem, was bis H bekannt ist:
  1. kommt_noch_14 / kommt_noch_18: kommen nach H noch mindestens 2 Stunden am Stück Breva ≥ 14 / ≥ 18 kn auf dem See
     (Samolaco × Satellitenfaktor, Richtung SSO–S, bis 20 Uhr)?   -> „lohnt es sich jetzt noch loszufahren?“
  2. see_+1 … see_+6: Breva-Wind auf dem See in 1 … 6 Stunden (kn)   -> Kurve „nächste Stunden“

Eingänge (drei Stufen, damit man sieht, was was bringt):
  V  Vorhersage: die 37 Größen des 7-Tage-Modells (Training: ERA5; Prüfung: ECMWF-Lauf vom Vortag bzw. --lauf),
     dazu Uhrzeit, Jahreszeit, gestern Breva
  W  + Wind gemessen: Breva-Komponente in Samolaco, Colico, Vercana, Morbegno (jetzt, 2-h-Mittel, Maximum seit 10 Uhr),
     Tivano am Morgen, See-Wind jetzt und vor 1/2 Stunden
  A  + ARPA-Treiber (data/arpa/messungen_stunde.csv aus arpa_extra.py): Temperaturgefälle Tal–Ebene jetzt und seit
     8 Uhr, See Nord–Süd, Schichtung Berg–See, Strahlung seit 8 Uhr, Feuchte Mailand, Regen bisher, Erwärmung im Tal

Prüfung: je Testjahr ab 2024 out-of-fold (Training alle anderen Jahre ab 2014), Vorhersage-Teil aus echten Läufen.
Vergleich zur Kurve: Persistenz (Wind bleibt wie jetzt). Ausgabe results/jetzt_skill.md / .csv

  python training/train_jetzt.py                 Vorhersage = ECMWF 0.25° vom Vortag (wie Heute-Modell)
  python training/train_jetzt.py --lauf ecmwf_ifs00z   Vorhersage = 00-UTC-Lauf 9 km vom selben Morgen (Vorlauf 0)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breva_daten as B  # noqa: E402
import train_breva as T  # noqa: E402
import train_heute as TH  # noqa: E402
from modell_vergleich import auc  # noqa: E402

HOURS = list(range(8, 18))
AHEAD = list(range(1, 7))
END = 20
FIRST_TEST = 2024
PLAIN, VALLEY = ["milano", "bergamo"], ["sondrio", "morbegno", "chiavenna"]


def lake_series(O, factor):
    """Breva-Wind auf dem See je Stunde (Ortszeit): Samolaco × Faktor, nur bei Richtung SSO–S, sonst 0."""
    s = O["samolaco"]
    ok = (s.dir >= 112) & (s.dir <= 202)
    return (s.kn * factor).where(ok, 0.0).where(s.kn.notna())


def arpa_hourly():
    f = os.path.join(B.DATA, "arpa", "messungen_stunde.csv")
    if not os.path.exists(f):
        print("keine ARPA-Treiber (arpa_extra.py) – Stufe A entfällt")
        return None
    M = pd.read_csv(f, parse_dates=["time"]).set_index("time")
    M.index = pd.DatetimeIndex(M.index).tz_convert(B.TZ).tz_localize(None)
    M = M[~M.index.duplicated(keep="first")]          # Herbst-Zeitumstellung: zwei UTC-Stunden -> eine Ortszeit-Stunde
    return M


def arpa_features(M, d, H):
    if M is None:
        return {}
    def g(col, h):
        if col not in M:
            return np.nan
        v = M[col].get(d + pd.Timedelta(hours=h), np.nan)
        return float(v.iloc[0]) if isinstance(v, pd.Series) else float(v)
    mean = lambda cols, h: np.nanmean([g(f"{c}_temp", h) for c in cols]) if any(np.isfinite(g(f"{c}_temp", h)) for c in cols) else np.nan
    grad = lambda h: mean(VALLEY, h) - mean(PLAIN, h)
    r = {"dT_tal_ebene": grad(H), "dT_tal_ebene_seit8": grad(H) - grad(8),
         "dT_chiavenna_milano": g("chiavenna_temp", H) - g("milano_temp", H),
         "dT_colico_como": g("colico_temp", H) - g("como_temp", H),
         "schichtung_berg_see": g("berg_see_temp", H) - g("colico_temp", H),
         "erwaermung_sondrio_seit6": g("sondrio_temp", H) - g("sondrio_temp", 6),
         "feuchte_milano": g("milano_rh", H)}
    for st in ("chiavenna", "colico", "sondrio"):
        v = [g(f"{st}_rad", h) for h in range(8, H + 1)]
        r[f"strahlung_{st}_seit8"] = np.nanmean(v) if np.isfinite(v).any() else np.nan
    rain = [g(f"{st}_rain", h) for st in ("colico", "chiavenna") for h in range(0, H + 1)]
    r["regen_bisher"] = np.nansum(rain) if np.isfinite(rain).any() else np.nan
    return r


def build(D, O, M, S, FEsrc, V):
    """eine Zeile je (Tag, Stunde)"""
    rows = []
    obs = {H: TH.obs_features(O, D.index, H) for H in HOURS}
    for d in D.index:
        fe = FEsrc.loc[d] if d in FEsrc.index else None
        if fe is None or fe.notna().mean() < 0.7:
            continue
        lake = [S.get(d + pd.Timedelta(hours=h), np.nan) for h in range(0, 24)]
        for H in HOURS:
            r = {"tag": d, "stunde": H, **fe.to_dict(), **V.loc[d].to_dict(), **obs[H].loc[d].to_dict(),
                 "see_jetzt": lake[H], "see_vor1h": lake[H - 1], "see_vor2h": lake[H - 2],
                 **arpa_features(M, d, H)}
            rest = np.array(lake[H + 1:END + 1], dtype=float)
            for thr in (14, 18):
                hit = np.nan_to_num(rest) >= thr
                run = max((len(x) for x in "".join("1" if b else "0" for b in hit).split("0")), default=0)
                r[f"kommt_noch_{thr}"] = int(run >= 2) if np.isfinite(rest).mean() > 0.6 else np.nan
            for k in AHEAD:
                r[f"see_+{k}"] = lake[H + k] if H + k < 24 else np.nan
            rows.append(r)
    return pd.DataFrame(rows)


def main(lauf):
    from xgboost import XGBRegressor
    D = pd.read_csv(f"{B.RES}/breva_tage.csv", index_col=0, parse_dates=True)
    factor = float((D.see_max_est / D.sam_max).median())
    O = TH.hourly_obs(); M = arpa_hourly(); S = lake_series(O, factor)
    BD = TH.breva_day(O, factor)
    V = pd.DataFrame({"gestern_breva": BD.breva.shift(1, freq="D"), "gestern_max": BD["max"].shift(1, freq="D")}).reindex(D.index)
    FE = B.features(B.load("era5")).reindex(D.index).reindex(columns=T.FEATS)
    lead = 0 if lauf.endswith("00z") else 1
    FL = B.features(B.load("prev", lead, lauf)).reindex(D.index).reindex(columns=T.FEATS)
    FL = FL[FL.index.year >= FIRST_TEST]
    print(f"Vorhersage für die Prüfung: {lauf}, Vorlauf {lead}; {int((FL.notna().mean(axis=1) > 0.7).sum())} Tage ab {FIRST_TEST}")
    Xtr = build(D[D.index.year < 2100], O, M, S, FE, V)            # Training: ERA5 als „Vorhersage“
    Xte = build(D[D.index.year >= FIRST_TEST], O, M, S, FL, V)       # Prüfung: echte Läufe
    obsW = TH.OBS + ["see_jetzt", "see_vor1h", "see_vor2h"]
    arpaA = [c for c in Xtr.columns if c.startswith(("dT_", "schichtung", "erwaermung", "feuchte", "strahlung", "regen_bisher"))]
    base = T.FEATS + ["stunde"] + TH.VORTAG
    stages = {"V Vorhersage": base, "W + Wind": base + obsW}
    if arpaA and Xtr[arpaA].notna().mean().max() > 0.3:
        stages["A + ARPA-Treiber"] = base + obsW + arpaA
    years = sorted(set(Xte.tag.dt.year))
    rows, OOF = [], []
    for name, feats in stages.items():
        for thr in (14, 18):
            tgt = f"kommt_noch_{thr}"
            p = pd.Series(np.nan, index=Xte.index)
            for yr in years:
                tr = Xtr[(Xtr.tag.dt.year != yr) & Xtr[tgt].notna()]
                te = Xte[(Xte.tag.dt.year == yr) & Xte[tgt].notna()]
                m = T.xgb_model().fit(tr[feats], tr[tgt])
                p[te.index] = m.predict_proba(te[feats])[:, 1]
            ok_ = p.notna()
            OOF.append(pd.DataFrame({"tag": Xte.tag[ok_].dt.strftime("%Y-%m-%d"), "stunde": Xte.stunde[ok_], "schwelle": thr,
                                     "stufe": name, "p": p[ok_].round(4), "y": Xte.loc[ok_, tgt]}))
            for H in HOURS:
                i = (Xte.stunde == H) & p.notna(); s = i & Xte.tag.dt.month.between(3, 10)
                rows.append(dict(art="kommt_noch", stufe=name, schwelle=thr, stunde=H, faelle=int(i.sum()),
                                 ja=int(Xte.loc[i, tgt].sum()), auc=round(auc(Xte.loc[i, tgt], p[i]), 3),
                                 auc_saison=round(auc(Xte.loc[s, tgt], p[s]), 3)))
        for k in AHEAD:
            tgt = f"see_+{k}"
            p = pd.Series(np.nan, index=Xte.index)
            for yr in years:
                tr = Xtr[(Xtr.tag.dt.year != yr) & Xtr[tgt].notna()]
                te = Xte[(Xte.tag.dt.year == yr) & Xte[tgt].notna()]
                m = XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.8,
                                 colsample_bytree=0.8, min_child_weight=10, verbosity=0).fit(tr[feats], tr[tgt])
                p[te.index] = m.predict(te[feats])
            i = p.notna() & Xte.tag.dt.month.between(3, 10) & Xte.stunde.between(9, 16)
            err = (p[i] - Xte.loc[i, tgt]).abs(); pers = (Xte.loc[i, "see_jetzt"] - Xte.loc[i, tgt]).abs()
            big = i & (Xte[tgt] >= 10)
            rows.append(dict(art="kurve", stufe=name, stunden_voraus=k, faelle=int(i.sum()),
                             mae=round(err.mean(), 2), mae_persistenz=round(pers.mean(), 2),
                             mae_bei_wind=round((p[big] - Xte.loc[big, tgt]).abs().mean(), 2)))
        print(f"  {name} fertig", flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(f"{B.RES}/jetzt_skill.csv", index=False)
    pd.concat(OOF).to_csv(f"{B.RES}/oof_jetzt_{lauf}.csv", index=False)
    print(f"geschrieben: results/oof_jetzt_{lauf}.csv (out-of-fold je Tag, Stunde, Stufe)")
    lines = ["# Same-Day-Modell, stündlich\n",
             f"Prüfung {years[0]}–{years[-1]} je Jahr out-of-fold; Vorhersage-Teil aus {lauf} (Vorlauf {lead}). "
             "Stufen: V nur Vorhersage, W + gemessener Wind, A + ARPA-Treiber.\n"]
    K = R[R.art == "kommt_noch"]
    for thr in (14, 18):
        W = K[K.schwelle == thr].pivot_table(index="stunde", columns="stufe", values="auc_saison")
        lines += [f"\n## Kommt nach dieser Stunde noch ≥ {thr} kn (≥ 2 h)? – AUC März–Oktober\n", "```", W.round(3).to_string(), "```"]
    C = R[R.art == "kurve"].pivot_table(index="stunden_voraus", columns="stufe", values="mae")
    C["Persistenz"] = R[R.art == "kurve"].groupby("stunden_voraus").mae_persistenz.first()
    lines += ["\n## Wind auf dem See in k Stunden – mittlerer Fehler (kn), März–Oktober, 9–16 Uhr\n", "```", C.round(2).to_string(), "```",
              "\nPersistenz = „bleibt wie jetzt“. Je kleiner, desto besser.\n"]
    open(f"{B.RES}/jetzt_skill.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("geschrieben: results/jetzt_skill.md, results/jetzt_skill.csv")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lauf", default=T.MODEL, help="ecmwf_ifs025 (Vortag) oder ecmwf_ifs00z (selber Morgen, Vorlauf 0)")
    main(ap.parse_args().lauf)
