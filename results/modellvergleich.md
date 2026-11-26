# Wettermodelle als Eingang für die 7-Tage-Breva-Vorhersage

Je Testjahr ab 2024 ein Modell an ERA5 aller anderen Jahre (Ziel B), getestet mit den echten, archivierten Vorhersagen jedes Modells. Vergleich je Vorlauf nur auf den Tagen, die alle Modelle dieses Vorlaufs haben.


## ≥ 14 kn

merkmal_r: Übereinstimmung der Merkmale mit ERA5 (Korrelation, gewichtet mit der Wichtigkeit im Modell); auc_angeglichen: Merkmale vorher per Quantil-Angleichung auf ERA5-Verteilung gebracht; auc_eigen: Modell nur auf den eigenen Vorhersagen dieses Wettermodells trainiert (andere Jahre); auc_kombi: ERA5 + eigene Vorhersagen (3-fach gewichtet); auc_gleiche_tage: die ERA5-Variante auf genau diesen Tagen (Vergleichswert für eigen/kombi); ref_auc_gleiche_tage: ECMWF 0.25° auf denselben Tagen wie das Modell (paarweiser Vergleich). Alles je Jahr out-of-fold.

```
 schwelle  vorlauf       modell         ab  tage  breva  merkmal_r  merkmal_nmae   auc  auc_saison  auc_angeglichen  auc_gleiche_tage  auc_eigen  auc_kombi  ref_auc_gleiche_tage bereich_90
       14        1 ecmwf_ifs025 2024-02-04   956  198.0      0.897         0.320 0.886       0.834            0.886             0.886      0.847      0.886                   NaN        NaN
       14        1    ecmwf_ifs 2025-10-01   340   71.0      0.887         0.328 0.924       0.878            0.906             0.925      0.867      0.961                 0.920        NaN
       14        2 ecmwf_ifs025 2024-02-05   955  198.0      0.883         0.340 0.873       0.818            0.862             0.873      0.841      0.872                   NaN        NaN
       14        2    ecmwf_ifs 2025-10-02   339   70.0      0.872         0.342 0.899       0.836            0.880             0.947      0.747      0.947                 0.911        NaN
       14        3 ecmwf_ifs025 2024-02-06   954  197.0      0.867         0.364 0.864       0.802            0.859             0.864      0.827      0.864                   NaN        NaN
       14        3    ecmwf_ifs 2025-10-03   338   70.0      0.850         0.370 0.896       0.838            0.888             0.899      0.679      0.899                 0.903        NaN
       14        4 ecmwf_ifs025 2024-02-07   953  197.0      0.839         0.394 0.843       0.773            0.840             0.843      0.814      0.838                   NaN        NaN
       14        5 ecmwf_ifs025 2024-02-08   952  197.0      0.799         0.444 0.823       0.754            0.822             0.823      0.803      0.828                   NaN        NaN
       14        5    ecmwf_ifs 2025-10-05   347   77.0      0.781         0.452 0.875       0.804            0.859             0.921      0.988      0.945                 0.874        NaN
       14        6 ecmwf_ifs025 2024-02-09   951  197.0      0.710         0.546 0.801       0.722            0.797             0.801      0.789      0.807                   NaN        NaN
       14        7 ecmwf_ifs025 2024-02-10   950  197.0      0.681         0.607 0.800       0.716            0.793             0.800      0.744      0.804                   NaN        NaN
       14        7    ecmwf_ifs 2025-10-07   345   77.0      0.677         0.554 0.856       0.747            0.829             0.637      0.781      0.606                 0.878        NaN
```

Unterschied zu ecmwf_ifs025 (Bootstrap über Wochen, 90 %-Bereich; schließt er 0 aus, ist der Unterschied belastbar):

```
 vorlauf                       modell  tage    auc      bereich_90
       1   Δ ecmwf_ifs − ecmwf_ifs025   340  0.004 -0.013 … +0.021
       1 Δ ecmwf_ifs|q − ecmwf_ifs025   340 -0.013 -0.033 … +0.004
       2   Δ ecmwf_ifs − ecmwf_ifs025   339 -0.012 -0.028 … +0.003
       2 Δ ecmwf_ifs|q − ecmwf_ifs025   339 -0.031 -0.054 … -0.007
       3   Δ ecmwf_ifs − ecmwf_ifs025   338 -0.008 -0.021 … +0.006
       3 Δ ecmwf_ifs|q − ecmwf_ifs025   338 -0.015 -0.038 … +0.006
       5   Δ ecmwf_ifs − ecmwf_ifs025   347  0.001 -0.015 … +0.017
       5 Δ ecmwf_ifs|q − ecmwf_ifs025   347 -0.015 -0.034 … +0.005
       7   Δ ecmwf_ifs − ecmwf_ifs025   345 -0.023 -0.048 … +0.002
       7 Δ ecmwf_ifs|q − ecmwf_ifs025   345 -0.049 -0.083 … -0.018
```

## ≥ 18 kn

merkmal_r: Übereinstimmung der Merkmale mit ERA5 (Korrelation, gewichtet mit der Wichtigkeit im Modell); auc_angeglichen: Merkmale vorher per Quantil-Angleichung auf ERA5-Verteilung gebracht; auc_eigen: Modell nur auf den eigenen Vorhersagen dieses Wettermodells trainiert (andere Jahre); auc_kombi: ERA5 + eigene Vorhersagen (3-fach gewichtet); auc_gleiche_tage: die ERA5-Variante auf genau diesen Tagen (Vergleichswert für eigen/kombi); ref_auc_gleiche_tage: ECMWF 0.25° auf denselben Tagen wie das Modell (paarweiser Vergleich). Alles je Jahr out-of-fold.

```
 schwelle  vorlauf       modell         ab  tage  breva  merkmal_r  merkmal_nmae   auc  auc_saison  auc_angeglichen  auc_gleiche_tage  auc_eigen  auc_kombi  ref_auc_gleiche_tage bereich_90
       18        1 ecmwf_ifs025 2024-02-04   956   57.0      0.892         0.328 0.744       0.682            0.752             0.744      0.736      0.766                   NaN        NaN
       18        1    ecmwf_ifs 2025-10-01   340   22.0      0.881         0.336 0.753       0.673            0.771               NaN        NaN        NaN                 0.715        NaN
       18        2 ecmwf_ifs025 2024-02-05   955   57.0      0.876         0.348 0.745       0.683            0.750             0.745      0.803      0.780                   NaN        NaN
       18        2    ecmwf_ifs 2025-10-02   339   22.0      0.862         0.354 0.735       0.658            0.752               NaN        NaN        NaN                 0.729        NaN
       18        3 ecmwf_ifs025 2024-02-06   954   57.0      0.858         0.372 0.767       0.709            0.767             0.767      0.818      0.794                   NaN        NaN
       18        3    ecmwf_ifs 2025-10-03   338   22.0      0.838         0.381 0.736       0.656            0.781               NaN        NaN        NaN                 0.733        NaN
       18        4 ecmwf_ifs025 2024-02-07   953   57.0      0.829         0.403 0.740       0.674            0.751             0.740      0.815      0.804                   NaN        NaN
       18        5 ecmwf_ifs025 2024-02-08   952   57.0      0.785         0.455 0.721       0.656            0.739             0.721      0.779      0.746                   NaN        NaN
       18        5    ecmwf_ifs 2025-10-05   347   28.0      0.773         0.461 0.763       0.684            0.761               NaN        NaN        NaN                 0.782        NaN
       18        6 ecmwf_ifs025 2024-02-09   951   57.0      0.705         0.530 0.716       0.653            0.739             0.716      0.758      0.736                   NaN        NaN
       18        7 ecmwf_ifs025 2024-02-10   950   57.0      0.667         0.588 0.743       0.678            0.738             0.743      0.725      0.754                   NaN        NaN
       18        7    ecmwf_ifs 2025-10-07   345   28.0      0.662         0.565 0.795       0.713            0.789               NaN        NaN        NaN                 0.814        NaN
```

Unterschied zu ecmwf_ifs025 (Bootstrap über Wochen, 90 %-Bereich; schließt er 0 aus, ist der Unterschied belastbar):

```
 vorlauf                       modell  tage    auc      bereich_90
       1   Δ ecmwf_ifs − ecmwf_ifs025   340  0.038 +0.002 … +0.081
       1 Δ ecmwf_ifs|q − ecmwf_ifs025   340  0.056 +0.018 … +0.104
       2   Δ ecmwf_ifs − ecmwf_ifs025   339  0.006 -0.034 … +0.050
       2 Δ ecmwf_ifs|q − ecmwf_ifs025   339  0.023 -0.054 … +0.094
       3   Δ ecmwf_ifs − ecmwf_ifs025   338  0.003 -0.043 … +0.059
       3 Δ ecmwf_ifs|q − ecmwf_ifs025   338  0.048 -0.011 … +0.133
       5   Δ ecmwf_ifs − ecmwf_ifs025   347 -0.019 -0.063 … +0.023
       5 Δ ecmwf_ifs|q − ecmwf_ifs025   347 -0.021 -0.068 … +0.026
       7   Δ ecmwf_ifs − ecmwf_ifs025   345 -0.019 -0.065 … +0.030
       7 Δ ecmwf_ifs|q − ecmwf_ifs025   345 -0.025 -0.064 … +0.011
```
