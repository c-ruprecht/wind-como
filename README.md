# wind-como – lokale Kite-Windvorhersage Comer See

Ableger von [wingst](https://github.com/c-ruprecht/wingst) (Darß/Zingst/Bodden): freie Wettermodelle (ICON, GFS, ECMWF
über Open-Meteo) mit lokalen Messungen und Satellitenwind korrigieren, damit die Vorhersage für
„Stunden am Stück ab 14 kn / ab 18 kn“ an den Spots am oberen Comer See genauer wird – Breva (thermischer
Südwind am Nachmittag) und Tivano (Nordwind morgens).

Spots (geplant): Colico, Gera Lario, Sorico/La Punta, Domaso, Dervio, Cremia.

## Ziele

1. **Wo ist heute/jetzt Wind?** Live-Messungen (ARPA alle 10 min, private Stationen am Wasser) mit Satellitenfaktor
   auf die Spots umgerechnet (Jetzt-korr.), dazu lokales Modell und korrigiertes ICON-Feld für den restlichen Tag.
2. **Kommt in den nächsten 7 Tagen ein Breva ≥ 14 / ≥ 18 kn?** Tageschance „mind. 2 h am Stück“, geeicht.
   Der Breva ist thermisch: Merkmale aus den Modellen sind vor allem Einstrahlung/Bewölkung, Temperaturgefälle
   Po-Ebene (Mailand) – Alpentäler (Chiavenna, Sondrio), Druckgefälle Mailand – Täler, Höhenwind 850 hPa
   (Nordföhn/Westlagen unterdrücken den Breva), Jahreszeit.

Voraussetzung: eine Messstation, die den Wind auf dem See wirklich abbildet – Auswahl mit dem Satelliten (unten).

## Messstationen

ARPA Lombardia, offen über Open Data Lombardia (Socrata, ohne Zugangsdaten), 10-Minuten-Werte, Historie ab Datum:

| Station | Höhe | seit | Rolle |
|---|---|---|---|
| Colico v.La Madoneta | 229 m | 2013-12 | Hauptstation Nordende (Colico, Gera Lario, Domaso) |
| Como Villa Gallia | 201 m | 2013-10 | Südende |
| Lecco v.Sora, Valmadrera v.Pozzi | 272 / 247 m | 2013/14 | Lecco-Arm |
| Samolaco v.Vignola | 206 m | 1994 | Pian di Spagna / Mera-Tal nördlich des Sees |
| Morbegno eliporto | 230 m | 2016 | Veltlin, Talwind |
| Vercana, San Siro Alpe Rescascìa, Canzo | 980–1285 m | 2008–14 | Hangstationen: Höhenwind, Föhn (Merkmale) |

Seespiegel ~198 m. Private Stationen an den Spots (nur live, Historie/Lizenz anfragen): Domaso (nauticadomaso.it),
Gravedona (casarina.com), Gravedona ed Uniti (Centro Meteo Lombardo), Colico Piano (MADIS F2315).

## Ablauf

```
conda env create -f environment.yml && conda activate windcomo
python training/download_arpa.py            # Sensoren nachschlagen, 10-min-Werte laden, Stundenwerte -> data/arpa/
python training/station_screen.py           # jede Station aus eigenen Messungen bewerten (Breva-Tagesgang, Böen, Richtung)

# Satellit (Sentinel-1, 100 m) – Wind auf dem See gegen alle Stationen -> beste Station
pip install sentinelhub rasterio
export CDSE_CLIENT_ID=...  CDSE_CLIENT_SECRET=...
python training/sar_lake.py download --start 2015-01-01 --workers 6
python training/sar_lake.py wind
python training/sar_lake.py stations
```

Erste Prüfung (Mai–Sep, 2014–2026): Colico und Como messen den Breva kaum – nachmittags im Mittel 3–4 kn,
ab 14 kn in 0,1 % bzw. 1 % der Stunden, Böe/Mittel ~2,5 (geschützte Standorte), kaum Südwind.
Deshalb erst die beste Station mit dem Satelliten auswählen.

Stationsvergleich (`station_screen.py`, 9 Stationen, Sommer, Nachmittag 13–18 Uhr):

| Station | Mittag kn | Tagesgang kn | ab 14 kn % | Süd % | Breva-Tage/Sommer | Max. Stunde |
|---|---|---|---|---|---|---|
| **Samolaco** (206 m, Pian di Spagna) | 7.5 | 4.6 | 8.4 | 63 | 66.7 | 15 |
| Vercana (980 m, über Domaso) | 5.6 | 2.7 | 3.2 | 56 | 12.2 | 16 |
| Morbegno (230 m) | 5.9 | 3.4 | 0.2 | 29 | 11.4 | 16 |
| Colico (229 m) | 3.8 | 2.5 | 0.0 | 8 | 2.3 | 17 |
| Como / Lecco / Valmadrera | 2–3.4 | ≤1.4 | ≤1.2 | – | ≤9 | – |
| Canzo (1233 m) | 5.2 | −2.2 | 4.5 | 25 | – | 1 (Höhenwind) |

- **Samolaco** zeigt die klare Breva-Signatur (starker Tagesgang, Süd, Maximum 15 Uhr): Kandidat für die Trainingsstation.
- Nordgruppe Samolaco–Vercana–Colico–Morbegno hängt zusammen (r 0.47–0.69, Vercana–Samolaco 0.69);
  Südgruppe Como–Lecco–Canzo läuft getrennt (r ~0 zum Norden) – für die Spots am oberen See ungeeignet.
- Offen: Faktor See/Samolaco und Trefferquote aus dem Satelliten (`sar_lake.py stations`).

Breva-Ereignisse und Vorhersagbarkeit (`training/breva_events.py`):
```
python training/breva_events.py wetter
python training/breva_events.py laeufe
python training/breva_events.py ereignisse
python training/breva_events.py analyse
python training/breva_events.py vorlauf
```
1. Breva-Abende aus Sentinel-1 (Apr–Sep, Abendüberflug, See ≥ 12 kn aus Süd), dazu Breva-Tage aus Samolaco × Satellitenfaktor.
2. ERA5 (Wetter, wie es war): welche Größen trennen Breva-Tage von ruhigen – Einstrahlung, Wolken, Temperatur- und
   Druckgefälle Po-Ebene – Täler, Nord-Süd-Druck (Föhn), Regen. Modell-AUC = Obergrenze bei perfekter Vorhersage.
3. ECMWF-Läufe 1–7 Tage vorher (ab 2024): AUC nach Vorlauf – ab wann der Breva vorhersagbar ist.

Sauberer Breva-Datensatz und Faktoren (`training/breva_daten.py`):
```
python training/breva_daten.py wetter
python training/breva_daten.py archiv
python training/breva_daten.py laeufe
python training/breva_daten.py tage
python training/breva_daten.py pruefen
python training/breva_daten.py pruefen --quelle archiv
python training/breva_daten.py faktoren
python training/breva_daten.py vorlauf
```
- `tage`: jeder Tag Apr–Sep bekommt eine Klasse – Breva (≥ 14 kn auf dem See, ≥ 2 h), Breva schwach, ruhig,
  Regen/Gewitter, Nordföhn, synoptisch (Wind schon morgens / sehr böig). Gegenprobe mit dem Satellitenbild am Abend.
- Nur Größen, die es auch als 7-Tage-Vorhersage gibt (Modellausgaben) oder langsam ändernde Zustände (Jahreszeit,
  Wassertemperatur-Ersatz, Bodenfeuchte). Messungen und Satellit dienen nur als Wahrheit und Prüfung.
- `archiv`: Vorhersagearchiv ICON ab 2022 mit Höhenwerten 850/700/500 hPa (Temperatur, Feuchte, Wind, Geopotential),
  Labilität (Lifted Index), Diffusstrahlung (Dunst), Böen, Verdunstung, Schnee.
- `pruefen`: jede Größe einzeln – AUC je Monat (Jahreszeit herausgerechnet), Stabilität über die Jahre, gegen alle
  Tage, gegen Störungen, Rangkorrelation mit dem Seewind im Satellitenbild; doppelte Größen zusammengefasst.
- `faktoren`: Wettergrößen an Schönwettertagen (Breva gegen ruhig) und Modell auf allen Tagen; wichtigste Größen (SHAP).
- Wettergrößen: ERA5 an See, Mailand, Bergamo, Chiavenna, Sondrio, Engadin + Großwetterlage (Zürich, München, Genua,
  Venedig, Lyon): Einstrahlung, Wolken, Grenzschicht, Bodenfeuchte, CAPE, Temperatur-/Druckgefälle, Föhn-Index,
  geostrophischer Wind, Drucktendenz, Schnee Engadin, Ersatz Wassertemperatur (30-Tage-Lufttemperatur am See).

Offene Punkte / Plan
1. ARPA-Download prüfen (Zeitzone der Zeitstempel: Annahme UTC+1 ohne Sommerzeit, gegen bekannte Ereignisse prüfen)
2. ICON/GFS/ECMWF an den Stationen (Open-Meteo, frühere Läufe) – wie gut trifft ICON den Breva?
3. Sentinel-1 in 100 m für den See (Morgen- und Abendüberflug: Tivano bzw. Ende Breva), Faktoren je Spot
4. 7-Tage-Modell (XGBoost, 14/18 kn), Tageschancen, Eichung
5. App (Karte, Windanimation, Jetzt-korr.) aus wingst übernehmen

## Datenquellen

ARPA Lombardia / Regione Lombardia – Open Data Lombardia · Open-Meteo (CC BY 4.0) · Copernicus Sentinel-1

## App (erste Version)

`app/` wird über GitHub Pages veröffentlicht (`.github/workflows/pages.yml`, in den Repo-Einstellungen unter
Pages „GitHub Actions“ als Quelle wählen). Lokal: `cd app && python -m http.server`, dann `http://localhost:8000`
(mit `?demo` und Dateien in `app/demo/` ohne Netz testbar).

- **Jetzt:** ARPA-Messungen (10 min, live) × Satellitenfaktor Spot/Station, nur wenn die Station Breva-Richtung misst.
- **7 Tage:** Breva-Zeichen aus ICON/ECMWF (Südwind am See, Druckgefälle Mailand–Chiavenna, Sonne im Tal, kein
  Nordföhn, trockene Luft, Regen dämpft) – vorläufig, bis das Modell trainiert ist; dazu das Breva-Klima je Monat.
- **Breva-Bild:** Median des Seewinds an Breva-Abenden (Sentinel-1) als Kartenauflage.
- Daten aktualisieren: `python training/export_app.py` (schreibt `app/breva.json`, `app/img/breva_mittel.png`).

### Modelle für die App

```
python training/train_breva.py      # 7 Tage: app/model/breva_14.json, breva_18.json, manifest.json (Eichung je Vorlauf)
python training/train_heute.py      # Heute 9/11/13 Uhr: app/model/heute*.json (Vorhersage + Messungen + Vortag)
python training/export_analyse.py   # Seite „Windanalyse & Breva“: app/analyse.json, Bilder
```
Die App rechnet die Merkmale selbst aus der ECMWF-Vorhersage an 11 Punkten (`app/breva_model.js`, identisch zu
`breva_daten.features`, geprüft auf 1e-13) und die Stationsmerkmale aus den ARPA-Stundenmitteln.
