# wind-como – lokale Kite-Windvorhersage Comer See

Ableger von [wingst](https://github.com/c-ruprecht/wingst) (Darß/Zingst/Bodden): freie Wettermodelle (ICON, GFS, ECMWF
über Open-Meteo) mit lokalen Messungen und Satellitenwind korrigieren, damit die Vorhersage für
„Stunden am Stück ab 14 kn / ab 18 kn“ an den Spots am oberen Comer See genauer wird – Breva (thermischer
Südwind am Nachmittag) und Tivano (Nordwind morgens).

Spots (geplant): Colico, Gera Lario, Sorico/La Punta, Domaso, Dervio, Cremia.

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
```

Offene Punkte / Plan
1. ARPA-Download prüfen (Zeitzone der Zeitstempel: Annahme UTC+1 ohne Sommerzeit, gegen bekannte Ereignisse prüfen)
2. ICON/GFS/ECMWF an den Stationen (Open-Meteo, frühere Läufe) – wie gut trifft ICON den Breva?
3. Sentinel-1 in 100 m für den See (Morgen- und Abendüberflug: Tivano bzw. Ende Breva), Faktoren je Spot
4. 7-Tage-Modell (XGBoost, 14/18 kn), Tageschancen, Eichung
5. App (Karte, Windanimation, Jetzt-korr.) aus wingst übernehmen

## Datenquellen

ARPA Lombardia / Regione Lombardia – Open Data Lombardia · Open-Meteo (CC BY 4.0) · Copernicus Sentinel-1
