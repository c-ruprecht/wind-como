# Wettermodelle als Eingang für die 7-Tage-Breva-Vorhersage

Je Testjahr ab 2024 ein Modell an ERA5 aller anderen Jahre (Ziel B), getestet mit den echten, archivierten Vorhersagen jedes Modells. Vergleich je Vorlauf nur auf den Tagen, die alle Modelle dieses Vorlaufs haben.


**Bestes Modell je Merkmal, Vorlauf 1 (gewählt 2024):** rad_chiavenna → ecmwf_ifs025, wind_see_15_sued → ecmwf_ifs025, rad_spaet_chiavenna → ecmwf_ifs025, doy_sin → ecmwf_ifs00z, doy_cos → ecmwf_ifs00z, geo_aus_sued → ecmwf_ifs025, dp_lyon_venezia_12 → ecmwf_ifs025, dp_zurich_milano_12 → ecmwf_ifs025, wind_see_15 → ecmwf_ifs025, dp_bergamo_sondrio_15 → ecmwf_ifs025, wind_milano_12 → ecmwf_ifs00z, regen_see → ecmwf_ifs025

**Bestes Modell je Merkmal, Vorlauf 3 (gewählt 2024):** rad_chiavenna → ecmwf_ifs025, wind_see_15_sued → ecmwf_ifs00z, rad_spaet_chiavenna → ecmwf_ifs025, doy_sin → ecmwf_ifs00z, doy_cos → ecmwf_ifs00z, geo_aus_sued → ecmwf_ifs025, dp_lyon_venezia_12 → ecmwf_ifs025, dp_zurich_milano_12 → ecmwf_ifs025, wind_see_15 → ecmwf_ifs025, dp_bergamo_sondrio_15 → ecmwf_ifs025, wind_milano_12 → ecmwf_ifs025, regen_see → ecmwf_ifs00z

## ≥ 14 kn

merkmal_r: Übereinstimmung der Merkmale mit ERA5 (Korrelation, gewichtet mit der Wichtigkeit im Modell); auc_angeglichen: Merkmale vorher per Quantil-Angleichung auf ERA5-Verteilung gebracht; auc_eigen: Modell nur auf den eigenen Vorhersagen dieses Wettermodells trainiert (andere Jahre); auc_kombi: ERA5 + eigene Vorhersagen (3-fach gewichtet); auc_gleiche_tage: die ERA5-Variante auf genau diesen Tagen (Vergleichswert für eigen/kombi); ref_auc_gleiche_tage: ECMWF 0.25° auf denselben Tagen wie das Modell (paarweiser Vergleich). Alles je Jahr out-of-fold.

```
 schwelle  vorlauf                                            modell         ab  tage  breva  merkmal_r  merkmal_nmae   auc  auc_saison  auc_angeglichen  auc_gleiche_tage  auc_eigen  auc_kombi  ref_auc_gleiche_tage bereich_90
       14        1                                      ecmwf_ifs025 2024-02-04   956  198.0      0.897         0.320 0.886       0.834            0.886             0.886      0.847      0.886                   NaN        NaN
       14        1                                         ecmwf_ifs 2025-10-01   340   71.0      0.887         0.328 0.924       0.878            0.906             0.925      0.867      0.961                 0.920        NaN
       14        1                                      ecmwf_ifs00z 2024-03-15   915  195.0      0.884         0.351 0.881       0.831            0.877             0.881      0.845      0.883                 0.884        NaN
       14        1                            Mittel (langes Archiv) 2024-03-15   915  195.0        NaN           NaN 0.891       0.842              NaN               NaN        NaN        NaN                 0.884        NaN
       14        1               Mittel (langes Archiv), angeglichen 2024-03-15   915  195.0        NaN           NaN 0.889       0.838              NaN               NaN        NaN        NaN                 0.884        NaN
       14        1 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   623  142.0        NaN           NaN 0.900       0.847              NaN               NaN        NaN        NaN                 0.899        NaN
       14        2                                      ecmwf_ifs025 2024-02-05   955  198.0      0.883         0.340 0.873       0.818            0.862             0.873      0.841      0.872                   NaN        NaN
       14        2                                         ecmwf_ifs 2025-10-02   339   70.0      0.872         0.342 0.899       0.836            0.880             0.947      0.747      0.947                 0.911        NaN
       14        2                                      ecmwf_ifs00z 2024-03-16   914  195.0      0.868         0.370 0.867       0.811            0.865             0.867      0.836      0.867                 0.874        NaN
       14        2                            Mittel (langes Archiv) 2024-03-16   914  195.0        NaN           NaN 0.879       0.824              NaN               NaN        NaN        NaN                 0.874        NaN
       14        2               Mittel (langes Archiv), angeglichen 2024-03-16   914  195.0        NaN           NaN 0.872       0.814              NaN               NaN        NaN        NaN                 0.874        NaN
       14        2 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   623  142.0        NaN           NaN 0.889       0.830              NaN               NaN        NaN        NaN                 0.887        NaN
       14        3                                      ecmwf_ifs025 2024-02-06   954  197.0      0.867         0.364 0.864       0.802            0.859             0.864      0.827      0.864                   NaN        NaN
       14        3                                         ecmwf_ifs 2025-10-03   338   70.0      0.850         0.370 0.896       0.838            0.888             0.899      0.679      0.899                 0.903        NaN
       14        3                                      ecmwf_ifs00z 2024-03-17   911  195.0      0.848         0.398 0.851       0.791            0.850             0.851      0.821      0.855                 0.862        NaN
       14        3                            Mittel (langes Archiv) 2024-03-17   911  195.0        NaN           NaN 0.864       0.806              NaN               NaN        NaN        NaN                 0.862        NaN
       14        3               Mittel (langes Archiv), angeglichen 2024-03-17   911  195.0        NaN           NaN 0.862       0.803              NaN               NaN        NaN        NaN                 0.862        NaN
       14        3 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621  142.0        NaN           NaN 0.870       0.814              NaN               NaN        NaN        NaN                 0.873        NaN
       14        4                                      ecmwf_ifs025 2024-02-07   953  197.0      0.839         0.394 0.843       0.773            0.840             0.843      0.814      0.838                   NaN        NaN
       14        4                                      ecmwf_ifs00z 2024-03-18   910  194.0      0.813         0.429 0.834       0.770            0.839             0.834      0.827      0.850                 0.843        NaN
       14        4                            Mittel (langes Archiv) 2024-03-18   910  194.0        NaN           NaN 0.849       0.786              NaN               NaN        NaN        NaN                 0.843        NaN
       14        4               Mittel (langes Archiv), angeglichen 2024-03-18   910  194.0        NaN           NaN 0.851       0.788              NaN               NaN        NaN        NaN                 0.843        NaN
       14        4 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621  141.0        NaN           NaN 0.858       0.790              NaN               NaN        NaN        NaN                 0.852        NaN
       14        5                                      ecmwf_ifs025 2024-02-08   952  197.0      0.799         0.444 0.823       0.754            0.822             0.823      0.803      0.828                   NaN        NaN
       14        5                                         ecmwf_ifs 2025-10-05   347   77.0      0.781         0.452 0.875       0.804            0.859             0.921      0.988      0.945                 0.874        NaN
       14        5                                      ecmwf_ifs00z 2024-03-19   909  196.0      0.762         0.487 0.812       0.741            0.821             0.812      0.788      0.821                 0.822        NaN
       14        5                            Mittel (langes Archiv) 2024-03-19   909  196.0        NaN           NaN 0.831       0.763              NaN               NaN        NaN        NaN                 0.822        NaN
       14        5               Mittel (langes Archiv), angeglichen 2024-03-19   909  196.0        NaN           NaN 0.836       0.770              NaN               NaN        NaN        NaN                 0.822        NaN
       14        5 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621  143.0        NaN           NaN 0.833       0.765              NaN               NaN        NaN        NaN                 0.834        NaN
       14        6                                      ecmwf_ifs025 2024-02-09   951  197.0      0.710         0.546 0.801       0.722            0.797             0.801      0.789      0.807                   NaN        NaN
       14        6                                      ecmwf_ifs00z 2024-03-20   908  194.0      0.714         0.530 0.813       0.735            0.810             0.813      0.796      0.834                 0.800        NaN
       14        6                            Mittel (langes Archiv) 2024-03-20   908  194.0        NaN           NaN 0.823       0.747              NaN               NaN        NaN        NaN                 0.800        NaN
       14        6               Mittel (langes Archiv), angeglichen 2024-03-20   908  194.0        NaN           NaN 0.819       0.743              NaN               NaN        NaN        NaN                 0.800        NaN
       14        6 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621  142.0        NaN           NaN 0.822       0.744              NaN               NaN        NaN        NaN                 0.820        NaN
       14        7                                      ecmwf_ifs025 2024-02-10   950  197.0      0.681         0.607 0.800       0.716            0.793             0.800      0.744      0.804                   NaN        NaN
       14        7                                         ecmwf_ifs 2025-10-07   345   77.0      0.677         0.554 0.856       0.747            0.829             0.637      0.781      0.606                 0.878        NaN
       14        7                                      ecmwf_ifs00z 2024-03-21   907  192.0      0.660         0.580 0.764       0.678            0.770             0.764      0.737      0.775                 0.804        NaN
       14        7                            Mittel (langes Archiv) 2024-03-21   907  192.0        NaN           NaN 0.811       0.728              NaN               NaN        NaN        NaN                 0.804        NaN
       14        7               Mittel (langes Archiv), angeglichen 2024-03-21   907  192.0        NaN           NaN 0.810       0.728              NaN               NaN        NaN        NaN                 0.804        NaN
       14        7 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621  141.0        NaN           NaN 0.841       0.766              NaN               NaN        NaN        NaN                 0.832        NaN
```

Unterschied zu ecmwf_ifs025 (Bootstrap über Wochen, 90 %-Bereich; schließt er 0 aus, ist der Unterschied belastbar):

```
 vorlauf                                               modell  tage    auc      bereich_90
       1                           Δ ecmwf_ifs − ecmwf_ifs025   340  0.004 -0.013 … +0.021
       1                         Δ ecmwf_ifs|q − ecmwf_ifs025   340 -0.013 -0.033 … +0.004
       1                        Δ ecmwf_ifs00z − ecmwf_ifs025   915 -0.003 -0.016 … +0.011
       1                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   915 -0.007 -0.022 … +0.007
       1                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   915 -0.001 -0.014 … +0.012
       1              Δ Mittel (langes Archiv) − ecmwf_ifs025   915  0.007 +0.000 … +0.015
       1 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   915  0.005 -0.005 … +0.014
       2                           Δ ecmwf_ifs − ecmwf_ifs025   339 -0.012 -0.028 … +0.003
       2                         Δ ecmwf_ifs|q − ecmwf_ifs025   339 -0.031 -0.054 … -0.007
       2                        Δ ecmwf_ifs00z − ecmwf_ifs025   914 -0.007 -0.019 … +0.006
       2                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   914 -0.009 -0.021 … +0.004
       2                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   914 -0.007 -0.019 … +0.004
       2              Δ Mittel (langes Archiv) − ecmwf_ifs025   914  0.005 -0.001 … +0.011
       2 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   914 -0.002 -0.009 … +0.005
       3                           Δ ecmwf_ifs − ecmwf_ifs025   338 -0.008 -0.021 … +0.006
       3                         Δ ecmwf_ifs|q − ecmwf_ifs025   338 -0.015 -0.038 … +0.006
       3                        Δ ecmwf_ifs00z − ecmwf_ifs025   911 -0.011 -0.026 … +0.003
       3                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   911 -0.012 -0.026 … +0.003
       3                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   911 -0.007 -0.022 … +0.007
       3              Δ Mittel (langes Archiv) − ecmwf_ifs025   911  0.002 -0.005 … +0.011
       3 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   911 -0.000 -0.010 … +0.010
       4                        Δ ecmwf_ifs00z − ecmwf_ifs025   910 -0.008 -0.028 … +0.010
       4                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   910 -0.004 -0.023 … +0.014
       4                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   910  0.007 -0.009 … +0.024
       4              Δ Mittel (langes Archiv) − ecmwf_ifs025   910  0.007 -0.003 … +0.016
       4 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   910  0.008 -0.003 … +0.019
       5                           Δ ecmwf_ifs − ecmwf_ifs025   347  0.001 -0.015 … +0.017
       5                         Δ ecmwf_ifs|q − ecmwf_ifs025   347 -0.015 -0.034 … +0.005
       5                        Δ ecmwf_ifs00z − ecmwf_ifs025   909 -0.010 -0.031 … +0.011
       5                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   909 -0.001 -0.025 … +0.021
       5                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   909 -0.001 -0.021 … +0.018
       5              Δ Mittel (langes Archiv) − ecmwf_ifs025   909  0.009 -0.002 … +0.021
       5 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   909  0.014 -0.000 … +0.028
       6                        Δ ecmwf_ifs00z − ecmwf_ifs025   908  0.013 -0.008 … +0.033
       6                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   908  0.010 -0.012 … +0.032
       6                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   908  0.033 +0.011 … +0.055
       6              Δ Mittel (langes Archiv) − ecmwf_ifs025   908  0.023 +0.011 … +0.035
       6 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   908  0.019 +0.004 … +0.035
       7                           Δ ecmwf_ifs − ecmwf_ifs025   345 -0.023 -0.048 … +0.002
       7                         Δ ecmwf_ifs|q − ecmwf_ifs025   345 -0.049 -0.083 … -0.018
       7                        Δ ecmwf_ifs00z − ecmwf_ifs025   907 -0.039 -0.070 … -0.010
       7                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   907 -0.033 -0.064 … -0.003
       7                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   907 -0.029 -0.057 … -0.001
       7              Δ Mittel (langes Archiv) − ecmwf_ifs025   907  0.007 -0.007 … +0.021
       7 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   907  0.006 -0.013 … +0.024
```

## ≥ 18 kn

merkmal_r: Übereinstimmung der Merkmale mit ERA5 (Korrelation, gewichtet mit der Wichtigkeit im Modell); auc_angeglichen: Merkmale vorher per Quantil-Angleichung auf ERA5-Verteilung gebracht; auc_eigen: Modell nur auf den eigenen Vorhersagen dieses Wettermodells trainiert (andere Jahre); auc_kombi: ERA5 + eigene Vorhersagen (3-fach gewichtet); auc_gleiche_tage: die ERA5-Variante auf genau diesen Tagen (Vergleichswert für eigen/kombi); ref_auc_gleiche_tage: ECMWF 0.25° auf denselben Tagen wie das Modell (paarweiser Vergleich). Alles je Jahr out-of-fold.

```
 schwelle  vorlauf                                            modell         ab  tage  breva  merkmal_r  merkmal_nmae   auc  auc_saison  auc_angeglichen  auc_gleiche_tage  auc_eigen  auc_kombi  ref_auc_gleiche_tage bereich_90
       18        1                                      ecmwf_ifs025 2024-02-04   956   57.0      0.892         0.328 0.744       0.682            0.752             0.744      0.736      0.766                   NaN        NaN
       18        1                                         ecmwf_ifs 2025-10-01   340   22.0      0.881         0.336 0.753       0.673            0.771               NaN        NaN        NaN                 0.715        NaN
       18        1                                      ecmwf_ifs00z 2024-03-15   915   56.0      0.876         0.358 0.768       0.704            0.745             0.768      0.759      0.765                 0.744        NaN
       18        1                            Mittel (langes Archiv) 2024-03-15   915   56.0        NaN           NaN 0.762       0.696              NaN               NaN        NaN        NaN                 0.744        NaN
       18        1               Mittel (langes Archiv), angeglichen 2024-03-15   915   56.0        NaN           NaN 0.754       0.690              NaN               NaN        NaN        NaN                 0.744        NaN
       18        1 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   623   41.0        NaN           NaN 0.742       0.668              NaN               NaN        NaN        NaN                 0.734        NaN
       18        2                                      ecmwf_ifs025 2024-02-05   955   57.0      0.876         0.348 0.745       0.683            0.750             0.745      0.803      0.780                   NaN        NaN
       18        2                                         ecmwf_ifs 2025-10-02   339   22.0      0.862         0.354 0.735       0.658            0.752               NaN        NaN        NaN                 0.729        NaN
       18        2                                      ecmwf_ifs00z 2024-03-16   914   57.0      0.859         0.378 0.741       0.677            0.742             0.741      0.750      0.765                 0.748        NaN
       18        2                            Mittel (langes Archiv) 2024-03-16   914   57.0        NaN           NaN 0.748       0.683              NaN               NaN        NaN        NaN                 0.748        NaN
       18        2               Mittel (langes Archiv), angeglichen 2024-03-16   914   57.0        NaN           NaN 0.752       0.689              NaN               NaN        NaN        NaN                 0.748        NaN
       18        2 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   623   42.0        NaN           NaN 0.754       0.692              NaN               NaN        NaN        NaN                 0.749        NaN
       18        3                                      ecmwf_ifs025 2024-02-06   954   57.0      0.858         0.372 0.767       0.709            0.767             0.767      0.818      0.794                   NaN        NaN
       18        3                                         ecmwf_ifs 2025-10-03   338   22.0      0.838         0.381 0.736       0.656            0.781               NaN        NaN        NaN                 0.733        NaN
       18        3                                      ecmwf_ifs00z 2024-03-17   911   57.0      0.837         0.406 0.765       0.701            0.763             0.765      0.798      0.801                 0.770        NaN
       18        3                            Mittel (langes Archiv) 2024-03-17   911   57.0        NaN           NaN 0.768       0.704              NaN               NaN        NaN        NaN                 0.770        NaN
       18        3               Mittel (langes Archiv), angeglichen 2024-03-17   911   57.0        NaN           NaN 0.769       0.705              NaN               NaN        NaN        NaN                 0.770        NaN
       18        3 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621   42.0        NaN           NaN 0.734       0.666              NaN               NaN        NaN        NaN                 0.755        NaN
       18        4                                      ecmwf_ifs025 2024-02-07   953   57.0      0.829         0.403 0.740       0.674            0.751             0.740      0.815      0.804                   NaN        NaN
       18        4                                      ecmwf_ifs00z 2024-03-18   910   57.0      0.798         0.443 0.742       0.671            0.729             0.742      0.742      0.736                 0.744        NaN
       18        4                            Mittel (langes Archiv) 2024-03-18   910   57.0        NaN           NaN 0.758       0.688              NaN               NaN        NaN        NaN                 0.744        NaN
       18        4               Mittel (langes Archiv), angeglichen 2024-03-18   910   57.0        NaN           NaN 0.753       0.688              NaN               NaN        NaN        NaN                 0.744        NaN
       18        4 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621   42.0        NaN           NaN 0.746       0.676              NaN               NaN        NaN        NaN                 0.726        NaN
       18        5                                      ecmwf_ifs025 2024-02-08   952   57.0      0.785         0.455 0.721       0.656            0.739             0.721      0.779      0.746                   NaN        NaN
       18        5                                         ecmwf_ifs 2025-10-05   347   28.0      0.773         0.461 0.763       0.684            0.761               NaN        NaN        NaN                 0.782        NaN
       18        5                                      ecmwf_ifs00z 2024-03-19   909   57.0      0.745         0.498 0.755       0.687            0.718             0.755      0.737      0.763                 0.725        NaN
       18        5                            Mittel (langes Archiv) 2024-03-19   909   57.0        NaN           NaN 0.755       0.687              NaN               NaN        NaN        NaN                 0.725        NaN
       18        5               Mittel (langes Archiv), angeglichen 2024-03-19   909   57.0        NaN           NaN 0.749       0.682              NaN               NaN        NaN        NaN                 0.725        NaN
       18        5 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621   42.0        NaN           NaN 0.733       0.668              NaN               NaN        NaN        NaN                 0.726        NaN
       18        6                                      ecmwf_ifs025 2024-02-09   951   57.0      0.705         0.530 0.716       0.653            0.739             0.716      0.758      0.736                   NaN        NaN
       18        6                                      ecmwf_ifs00z 2024-03-20   908   56.0      0.694         0.544 0.747       0.674            0.741             0.747      0.781      0.784                 0.730        NaN
       18        6                            Mittel (langes Archiv) 2024-03-20   908   56.0        NaN           NaN 0.758       0.685              NaN               NaN        NaN        NaN                 0.730        NaN
       18        6               Mittel (langes Archiv), angeglichen 2024-03-20   908   56.0        NaN           NaN 0.758       0.686              NaN               NaN        NaN        NaN                 0.730        NaN
       18        6 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621   42.0        NaN           NaN 0.736       0.676              NaN               NaN        NaN        NaN                 0.747        NaN
       18        7                                      ecmwf_ifs025 2024-02-10   950   57.0      0.667         0.588 0.743       0.678            0.738             0.743      0.725      0.754                   NaN        NaN
       18        7                                         ecmwf_ifs 2025-10-07   345   28.0      0.662         0.565 0.795       0.713            0.789               NaN        NaN        NaN                 0.814        NaN
       18        7                                      ecmwf_ifs00z 2024-03-21   907   56.0      0.637         0.595 0.727       0.659            0.709             0.727      0.780      0.759                 0.753        NaN
       18        7                            Mittel (langes Archiv) 2024-03-21   907   56.0        NaN           NaN 0.754       0.683              NaN               NaN        NaN        NaN                 0.753        NaN
       18        7               Mittel (langes Archiv), angeglichen 2024-03-21   907   56.0        NaN           NaN 0.739       0.666              NaN               NaN        NaN        NaN                 0.753        NaN
       18        7 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621   42.0        NaN           NaN 0.752       0.686              NaN               NaN        NaN        NaN                 0.773        NaN
```

Unterschied zu ecmwf_ifs025 (Bootstrap über Wochen, 90 %-Bereich; schließt er 0 aus, ist der Unterschied belastbar):

```
 vorlauf                                               modell  tage    auc      bereich_90
       1                           Δ ecmwf_ifs − ecmwf_ifs025   340  0.038 +0.002 … +0.081
       1                         Δ ecmwf_ifs|q − ecmwf_ifs025   340  0.056 +0.018 … +0.104
       1                        Δ ecmwf_ifs00z − ecmwf_ifs025   915  0.024 +0.001 … +0.050
       1                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   915  0.002 -0.025 … +0.029
       1                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   915  0.021 -0.011 … +0.054
       1              Δ Mittel (langes Archiv) − ecmwf_ifs025   915  0.018 +0.007 … +0.032
       1 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   915  0.011 -0.008 … +0.029
       2                           Δ ecmwf_ifs − ecmwf_ifs025   339  0.006 -0.034 … +0.050
       2                         Δ ecmwf_ifs|q − ecmwf_ifs025   339  0.023 -0.054 … +0.094
       2                        Δ ecmwf_ifs00z − ecmwf_ifs025   914 -0.007 -0.037 … +0.025
       2                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   914 -0.006 -0.042 … +0.029
       2                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   914  0.018 -0.012 … +0.050
       2              Δ Mittel (langes Archiv) − ecmwf_ifs025   914  0.001 -0.015 … +0.018
       2 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   914  0.004 -0.023 … +0.030
       3                           Δ ecmwf_ifs − ecmwf_ifs025   338  0.003 -0.043 … +0.059
       3                         Δ ecmwf_ifs|q − ecmwf_ifs025   338  0.048 -0.011 … +0.133
       3                        Δ ecmwf_ifs00z − ecmwf_ifs025   911 -0.005 -0.026 … +0.018
       3                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   911 -0.007 -0.035 … +0.021
       3                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   911  0.031 +0.007 … +0.056
       3              Δ Mittel (langes Archiv) − ecmwf_ifs025   911 -0.002 -0.015 … +0.011
       3 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   911 -0.001 -0.024 … +0.021
       4                        Δ ecmwf_ifs00z − ecmwf_ifs025   910 -0.002 -0.043 … +0.037
       4                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   910 -0.015 -0.065 … +0.031
       4                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   910 -0.008 -0.054 … +0.038
       4              Δ Mittel (langes Archiv) − ecmwf_ifs025   910  0.014 -0.003 … +0.032
       4 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   910  0.009 -0.018 … +0.036
       5                           Δ ecmwf_ifs − ecmwf_ifs025   347 -0.019 -0.063 … +0.023
       5                         Δ ecmwf_ifs|q − ecmwf_ifs025   347 -0.021 -0.068 … +0.026
       5                        Δ ecmwf_ifs00z − ecmwf_ifs025   909  0.030 -0.015 … +0.072
       5                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   909 -0.007 -0.054 … +0.036
       5                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   909  0.039 -0.002 … +0.083
       5              Δ Mittel (langes Archiv) − ecmwf_ifs025   909  0.031 +0.008 … +0.055
       5 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   909  0.025 +0.004 … +0.048
       6                        Δ ecmwf_ifs00z − ecmwf_ifs025   908  0.018 -0.031 … +0.074
       6                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   908  0.012 -0.035 … +0.058
       6                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   908  0.055 +0.004 … +0.111
       6              Δ Mittel (langes Archiv) − ecmwf_ifs025   908  0.028 +0.001 … +0.061
       6 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   908  0.029 -0.000 … +0.061
       7                           Δ ecmwf_ifs − ecmwf_ifs025   345 -0.019 -0.065 … +0.030
       7                         Δ ecmwf_ifs|q − ecmwf_ifs025   345 -0.025 -0.064 … +0.011
       7                        Δ ecmwf_ifs00z − ecmwf_ifs025   907 -0.026 -0.084 … +0.026
       7                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   907 -0.043 -0.097 … +0.006
       7                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   907  0.007 -0.044 … +0.059
       7              Δ Mittel (langes Archiv) − ecmwf_ifs025   907  0.001 -0.023 … +0.026
       7 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   907 -0.013 -0.045 … +0.016
```
