# Nordwind am Morgen im Satelliten – lecco

1100 Morgenbilder (2014–2026), Klassen:

```
klasse
sonst             535
ruhig             364
nordwind          155
sued               28
nordwind_stark     18
```

Median je Klasse (dB über ruhig; Stationen: Nordkomponente kn):

```
                sued  mitte  nord  abfall  rau_ganz  kn_richtwert  valmadrera_ueberflug  lecco_ueberflug  samolaco_ueberflug  colico_ueberflug  valmadrera_nord_max  lecco_nord_max  samolaco_nord_max  colico_nord_max
klasse                                                                                                                                                                                                                 
nordwind        3.15   5.92  5.46   -0.78      0.70         11.27                  0.00             0.00                2.59              2.68                 2.50            1.69               3.69             4.42
nordwind_stark  7.49  10.14  6.69    2.69      0.96         22.06                  3.37             0.00               15.26              4.99                10.40            1.66              18.87             7.20
ruhig           0.56   0.52  0.43   -0.10      0.01          7.19                  0.41             0.88                1.26              0.32                 1.51            1.35               2.14             1.02
sonst           2.33   2.09  2.84   -0.52      0.21          7.39                  0.00             0.99                1.43              0.57                 1.46            1.33               2.11             1.33
sued            2.30   4.83  3.97    0.05      0.50         10.01                  0.00             0.00               -5.80             -0.68                 1.54            1.27               2.05             0.53
```

Anteil der Morgenbilder mit Nordwind je Monat:

```
     Bilder  Anteil Nordwind
tag                         
1        85             0.24
2        79             0.15
3        89             0.15
4        91             0.10
5        96             0.12
6        92             0.08
7        95             0.21
8        96             0.16
9        95             0.18
10       98             0.13
11       96             0.16
12       88             0.23
```

Stationsziel „Nordwind am Morgen“ (Nordwind an der Station 6–10 Uhr mind. 2 h ≥ T kn) gegen den Satelliten:

```
   station  T_kn  kappa  anteil_tage  bilder   ab
valmadrera     2  0.207        0.235     239 2024
valmadrera     3  0.352        0.101     239 2024
valmadrera     4  0.364        0.052     239 2024
valmadrera     5  0.335        0.039     239 2024
valmadrera     6  0.335        0.029     239 2024
valmadrera     8  0.231        0.016     239 2024
     lecco     2  0.205        0.045    1060 2014
     lecco     3  0.042        0.007    1060 2014
     lecco     4  0.018        0.003    1060 2014
     lecco     5  0.010        0.001    1060 2014
     lecco     6  0.010        0.000    1060 2014
     lecco     8    NaN        0.000    1060 2014
  samolaco     2  0.305        0.339    1077 2014
  samolaco     3  0.516        0.110    1077 2014
  samolaco     4  0.506        0.084    1077 2014
  samolaco     5  0.469        0.071    1077 2014
  samolaco     6  0.472        0.068    1077 2014
  samolaco     8  0.445        0.060    1077 2014
    colico     2  0.533        0.206    1039 2014
    colico     3  0.535        0.135    1039 2014
    colico     4  0.488        0.100    1039 2014
    colico     5  0.443        0.072    1039 2014
    colico     6  0.305        0.047    1039 2014
    colico     8  0.082        0.015    1039 2014
```
Gewählt: colico, T = 3 kn (Kappa 0.53).

## Vorhersagbar?

Stationsziel an 4374 Tagen, davon 13% mit Nordwind am Morgen.

Stärkste Einzelgrößen (ERA5, Wetter wie es war):
```
              groesse  im_breva_modell   auc bei_nordwind  median_nordwind  median_sonst
         dp_po_tal_06             True 0.838       tiefer            -3.70         -1.50
  dp_zurich_milano_12             True 0.836        höher             6.20          0.80
         geo_aus_west             True 0.835       tiefer            -1.86         -0.17
   dp_lyon_venezia_12             True 0.811        höher             5.90          0.40
dp_muenchen_genova_12             True 0.808        höher             5.25          0.30
         geo_aus_sued             True 0.799       tiefer            -0.98         -0.05
        dt_engadin_po             True 0.795       tiefer           -15.20        -11.70
      wolken_tief_see            False 0.757       tiefer             0.94         17.44
          geo_staerke             True 0.749        höher             2.21          1.09
   dp_tag_minus_nacht             True 0.738        höher             1.60          0.40
            dt_tal_po             True 0.706       tiefer            -2.70         -1.10
dp_bergamo_sondrio_15             True 0.692       tiefer            -1.70         -0.70
  taupunktdiff_milano             True 0.678        höher            11.85          8.20
    wolken_morgen_see             True 0.673       tiefer            22.50         62.67
           wolken_see             True 0.662       tiefer            33.00         62.44
```

Modell je Jahr out-of-fold mit ERA5 (obere Grenze): AUC 0.929, März–Oktober 0.920.
Mit dem echten ECMWF-Lauf vom Vortag (952 Tage ab 2024): AUC 0.855.
