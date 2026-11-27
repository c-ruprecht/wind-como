# Nordwind am Morgen im Satelliten

1093 Morgenbilder (2015–2026), Klassen:

```
klasse
ruhig             407
sonst             406
nordwind          209
sued               46
nordwind_stark     25
```

Median je Klasse (dB über ruhig; Stationen: Nordkomponente kn):

```
                sued  mitte  nord  abfall  rau_ganz  kn_richtwert  samolaco_ueberflug  colico_ueberflug  samolaco_nord_max  vercana_nord_max
klasse                                                                                                                                      
nordwind        4.97   4.14  4.46    0.22      0.60         11.08                1.86              1.02               2.46              2.34
nordwind_stark  7.74   6.86  7.23    0.32      0.97         18.66                8.20              2.45              15.90              8.32
ruhig           0.45   0.46  0.49   -0.05      0.01         10.30                1.24              0.14               2.02              1.52
sonst           2.66   2.47  2.36    0.16      0.18         10.40                1.36              0.35               2.11              1.63
sued            3.45   2.50  2.96    0.07      0.32         10.21               -4.48              0.07               1.90              2.57
```

Anteil der Morgenbilder mit Nordwind je Monat:

```
     Bilder  Anteil Nordwind
tag                         
1        85             0.27
2        79             0.23
3        89             0.13
4        91             0.16
5        96             0.11
6        92             0.13
7        95             0.28
8        96             0.19
9        95             0.27
10       97             0.20
11       92             0.29
12       86             0.30
```

Stationsziel „Nordwind am Morgen“ (Samolaco-Nordkomponente 6–10 Uhr mind. 2 h ≥ T kn) gegen den Satelliten:

```
 T_kn  kappa  anteil_tage  bilder
    2  0.230        0.282    1075
    3  0.307        0.099    1075
    4  0.264        0.079    1075
    5  0.236        0.070    1075
    6  0.234        0.066    1075
    8  0.233        0.059    1075
```
Gewählt: T = 3 kn (Kappa 0.31).

## Vorhersagbar?

Stationsziel an 4655 Tagen, davon 10% mit Nordwind am Morgen.

Stärkste Einzelgrößen (ERA5, Wetter wie es war):
```
              groesse  im_breva_modell   auc bei_nordwind  median_nordwind  median_sonst
  dp_zurich_milano_12             True 0.873        höher             8.00          1.00
         geo_aus_west             True 0.869       tiefer            -2.41         -0.22
   dp_lyon_venezia_12             True 0.853        höher             7.85          0.50
        dt_engadin_po             True 0.846       tiefer           -16.50        -11.80
         geo_aus_sued             True 0.844       tiefer            -1.29         -0.08
          geo_staerke             True 0.841        höher             2.83          1.11
dp_muenchen_genova_12             True 0.836        höher             6.60          0.40
         dp_po_tal_06             True 0.832       tiefer            -3.85         -1.60
     wind_see_15_sued             True 0.792       tiefer            -2.11          1.60
            dt_tal_po             True 0.773       tiefer            -3.60         -1.20
dp_bergamo_sondrio_15             True 0.767       tiefer            -2.40         -0.70
      wolken_tief_see            False 0.737       tiefer             0.78         15.89
          wind_see_15             True 0.711        höher             3.40          2.30
  taupunktdiff_milano             True 0.710        höher            13.05          8.30
         dp_po_tal_15             True 0.707       tiefer            -2.55         -1.00
```

Modell je Jahr out-of-fold mit ERA5 (obere Grenze): AUC 0.927, März–Oktober 0.909.
Mit dem echten ECMWF-Lauf vom Vortag (969 Tage ab 2024): AUC 0.872.
