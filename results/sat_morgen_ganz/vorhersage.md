# Nordwind am Morgen im Satelliten – ganz

1095 Morgenbilder (2014–2026), Klassen:

```
klasse
sonst             464
nordwind          302
ruhig             246
nordwind_stark     50
sued               33
```

Median je Klasse (dB über ruhig; Stationen: Nordkomponente kn):

```
                oben_nord  oben_mitte  oben_sued  lecco_nord  lecco_mitte  lecco_sued  como_nord  como_mitte  como_sued  abfall_oben  abfall_lecco  abfall_como  rau_ganz  kn_richtwert  colico_ueberflug  samolaco_ueberflug  vercana_ueberflug  valmadrera_ueberflug  lecco_ueberflug  como_ueberflug  colico_nord_max  samolaco_nord_max  vercana_nord_max  valmadrera_nord_max  lecco_nord_max  como_nord_max
klasse                                                                                                                                                                                                                                                                                                                                                                                                           
nordwind             4.14        3.23       4.16        4.29         3.94        2.21       3.70        3.61       3.86         0.09         -1.99        -0.16      0.35         11.08              1.22                1.92               1.75                  0.00             0.97            2.92             2.38               2.46              2.72                 1.68            1.42           5.72
nordwind_stark       7.57        5.41       6.90        7.55         9.15        3.58       7.19        6.70       5.83        -0.10         -3.43        -1.97      0.68         17.40              4.24                2.85               2.20                  2.52             0.00            4.98             5.73               5.32              4.31                 5.34            1.91           8.70
ruhig                0.41        0.20       0.27        0.31         0.47        0.46       0.49        0.36       0.24        -0.19          0.16        -0.14      0.01         11.08              0.24                1.26               0.54                  0.48             0.87            0.00             0.91               2.11              1.68                 1.49            1.27           2.19
sonst                1.57        1.71       1.91        1.88         1.33        2.01       1.41        1.69       2.19         0.22         -0.14         0.56      0.09         12.05              0.52                1.39               0.70                  0.00             0.98            0.00             1.24               2.07              1.72                 1.50            1.35           3.36
sued                 4.39        2.10       3.10        3.88         4.51        1.73       2.56        2.61       1.85        -1.70         -1.84        -1.04      0.26         11.08             -0.62               -5.38              -3.11                  0.58             0.00            0.00             0.66               1.94              0.00                 0.96            1.25           0.00
```

Anteil der Morgenbilder mit Nordwind je Monat:

```
     Bilder  Anteil Nordwind
tag                         
1        84             0.37
2        76             0.26
3        89             0.27
4        90             0.22
5        96             0.29
6        92             0.23
7        95             0.40
8        96             0.44
9        95             0.35
10       98             0.30
11       96             0.33
12       88             0.39
```

Stationsziel „Nordwind am Morgen“ (Nordwind an der Station 6–10 Uhr mind. 2 h ≥ T kn) gegen den Satelliten:

```
   station  T_kn  kappa  anteil_tage  bilder   ab
    colico     2  0.446        0.206    1034 2014
    colico     3  0.391        0.135    1034 2014
    colico     4  0.338        0.100    1034 2014
    colico     5  0.260        0.072    1034 2014
    colico     6  0.163        0.047    1034 2014
    colico     8  0.049        0.015    1034 2014
  samolaco     2  0.283        0.339    1072 2014
  samolaco     3  0.328        0.110    1072 2014
  samolaco     4  0.299        0.084    1072 2014
  samolaco     5  0.259        0.071    1072 2014
  samolaco     6  0.256        0.068    1072 2014
  samolaco     8  0.242        0.060    1072 2014
   vercana     2  0.353        0.276    1074 2014
   vercana     3  0.344        0.147    1074 2014
   vercana     4  0.295        0.108    1074 2014
   vercana     5  0.257        0.089    1074 2014
   vercana     6  0.253        0.081    1074 2014
   vercana     8  0.238        0.072    1074 2014
valmadrera     2  0.092        0.235     238 2024
valmadrera     3  0.144        0.101     238 2024
valmadrera     4  0.141        0.052     238 2024
valmadrera     5  0.131        0.039     238 2024
valmadrera     6  0.131        0.029     238 2024
valmadrera     8  0.100        0.016     238 2024
     lecco     2  0.125        0.045    1055 2014
     lecco     3  0.024        0.007    1055 2014
     lecco     4  0.012        0.003    1055 2014
     lecco     5  0.004        0.001    1055 2014
     lecco     6  0.004        0.000    1055 2014
     lecco     8    NaN        0.000    1055 2014
      como     2  0.213        0.514    1023 2014
      como     3  0.296        0.403    1023 2014
      como     4  0.345        0.303    1023 2014
      como     5  0.346        0.222    1023 2014
      como     6  0.281        0.153    1023 2014
      como     8  0.194        0.067    1023 2014
```
Gewählt: colico, T = 2 kn (Kappa 0.45).

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
