# Nordwind am Morgen im Satelliten – oben

1093 Morgenbilder (2015–2026), Klassen:

```
klasse
sonst             413
ruhig             407
nordwind          219
sued               28
nordwind_stark     26
```

Median je Klasse (dB über ruhig; Stationen: Nordkomponente kn):

```
                sued  mitte  nord  abfall  rau_ganz  kn_richtwert  samolaco_ueberflug  colico_ueberflug  vercana_ueberflug  morbegno_ueberflug  samolaco_nord_max  colico_nord_max  vercana_nord_max  morbegno_nord_max
klasse                                                                                                                                                                                                                 
nordwind        4.95   4.18  4.49    0.15      0.61         10.89                1.88              1.28               1.65                5.38               2.49             2.78              2.72               6.48
nordwind_stark  7.77   6.92  7.37    0.35      0.97         18.76                6.53              5.58               2.85                2.30              15.66             7.20              8.50               4.69
ruhig           0.45   0.46  0.49   -0.05      0.01         10.30                1.30              0.26               0.60                1.94               2.11             0.98              1.68               4.70
sonst           2.65   2.45  2.34    0.21      0.18         10.11                1.46              0.62               0.87                3.54               2.14             1.39              1.86               5.90
sued            3.41   2.73  4.00   -0.67      0.34         10.50               -5.56             -0.26               0.00                0.00               1.88             0.61              1.78               0.41
```

Anteil der Morgenbilder mit Nordwind je Monat:

```
     Bilder  Anteil Nordwind
tag                         
1        85             0.26
2        79             0.23
3        89             0.15
4        91             0.18
5        96             0.15
6        92             0.14
7        95             0.27
8        96             0.21
9        95             0.28
10       97             0.25
11       92             0.26
12       86             0.33
```

Stationsziel „Nordwind am Morgen“ (Nordwind an der Station 6–10 Uhr mind. 2 h ≥ T kn) gegen den Satelliten:

```
 station  T_kn  kappa  anteil_tage  bilder   ab
samolaco     2  0.239        0.339    1071 2014
samolaco     3  0.320        0.110    1071 2014
samolaco     4  0.287        0.084    1071 2014
samolaco     5  0.242        0.071    1071 2014
samolaco     6  0.236        0.068    1071 2014
samolaco     8  0.227        0.060    1071 2014
  colico     2  0.396        0.206    1034 2014
  colico     3  0.376        0.135    1034 2014
  colico     4  0.355        0.100    1034 2014
  colico     5  0.291        0.072    1034 2014
  colico     6  0.200        0.047    1034 2014
  colico     8  0.060        0.015    1034 2014
 vercana     2  0.260        0.276    1073 2014
 vercana     3  0.262        0.147    1073 2014
 vercana     4  0.246        0.108    1073 2014
 vercana     5  0.213        0.089    1073 2014
 vercana     6  0.217        0.081    1073 2014
 vercana     8  0.198        0.072    1073 2014
morbegno     2  0.085        0.692     966 2016
morbegno     3  0.087        0.614     966 2016
morbegno     4  0.106        0.530     966 2016
morbegno     5  0.158        0.424     966 2016
morbegno     6  0.173        0.276     966 2016
morbegno     8  0.102        0.055     966 2016
```
Gewählt: colico, T = 2 kn (Kappa 0.40).

## Vorhersagbar?

Stationsziel an 4374 Tagen, davon 21% mit Nordwind am Morgen.

Stärkste Einzelgrößen (ERA5, Wetter wie es war):
```
              groesse  im_breva_modell   auc bei_nordwind  median_nordwind  median_sonst
         dp_po_tal_06             True 0.805       tiefer            -3.30         -1.40
  dp_zurich_milano_12             True 0.780        höher             5.20          0.70
         geo_aus_west             True 0.773       tiefer            -1.55         -0.13
        dt_engadin_po             True 0.763       tiefer           -14.40        -11.50
   dp_lyon_venezia_12             True 0.755        höher             5.00          0.20
dp_muenchen_genova_12             True 0.745        höher             4.20          0.10
         geo_aus_sued             True 0.743       tiefer            -0.79         -0.02
      wolken_tief_see            False 0.713       tiefer             2.00         18.67
            dt_tal_po             True 0.698       tiefer            -2.50         -1.00
dp_bergamo_sondrio_15             True 0.697       tiefer            -1.70         -0.60
          geo_staerke             True 0.676        höher             1.90          1.08
   dp_tag_minus_nacht             True 0.668        höher             1.10          0.40
         dp_po_tal_15             True 0.666       tiefer            -2.10         -0.90
  taupunktdiff_milano             True 0.664        höher            11.05          8.00
         dp_po_tal_18             True 0.656       tiefer            -2.60         -1.30
```

Modell je Jahr out-of-fold mit ERA5 (obere Grenze): AUC 0.884, März–Oktober 0.868.
Mit dem echten ECMWF-Lauf vom Vortag (952 Tage ab 2024): AUC 0.788.
