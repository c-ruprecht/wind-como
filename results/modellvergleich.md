# Wettermodelle als Eingang für die 7-Tage-Breva-Vorhersage

Je Testjahr ab 2024 ein Modell an ERA5 aller anderen Jahre (Ziel B), getestet mit den echten, archivierten Vorhersagen jedes Modells. Vergleich je Vorlauf nur auf den Tagen, die alle Modelle dieses Vorlaufs haben.


**Bestes Modell je Merkmal, Vorlauf 1 (gewählt 2024):** rad_chiavenna → ecmwf_ifs025, wind_see_15_sued → ecmwf_ifs025, rad_spaet_chiavenna → ecmwf_ifs025, doy_sin → ecmwf_ifs00z, doy_cos → ecmwf_ifs00z, geo_aus_sued → ecmwf_ifs025, dp_lyon_venezia_12 → ecmwf_ifs025, dp_zurich_milano_12 → ecmwf_ifs025, wind_see_15 → ecmwf_ifs025, dp_bergamo_sondrio_15 → ecmwf_ifs025, wind_milano_12 → icon_eu, regen_see → ecmwf_ifs025

**Bestes Modell je Merkmal, Vorlauf 3 (gewählt 2024):** rad_chiavenna → ecmwf_ifs025, wind_see_15_sued → icon_eu, rad_spaet_chiavenna → ecmwf_ifs025, doy_sin → ecmwf_ifs00z, doy_cos → ecmwf_ifs00z, geo_aus_sued → ecmwf_ifs025, dp_lyon_venezia_12 → ecmwf_ifs025, dp_zurich_milano_12 → ecmwf_ifs025, wind_see_15 → ecmwf_ifs025, dp_bergamo_sondrio_15 → ecmwf_ifs025, wind_milano_12 → ecmwf_ifs025, regen_see → icon_seamless

## ≥ 14 kn

merkmal_r: Übereinstimmung der Merkmale mit ERA5 (Korrelation, gewichtet mit der Wichtigkeit im Modell); auc_angeglichen: Merkmale vorher per Quantil-Angleichung auf ERA5-Verteilung gebracht; auc_eigen: Modell nur auf den eigenen Vorhersagen dieses Wettermodells trainiert (andere Jahre); auc_kombi: ERA5 + eigene Vorhersagen (3-fach gewichtet); auc_gleiche_tage: die ERA5-Variante auf genau diesen Tagen (Vergleichswert für eigen/kombi); ref_auc_gleiche_tage: ECMWF 0.25° auf denselben Tagen wie das Modell (paarweiser Vergleich). Alles je Jahr out-of-fold.

```
 schwelle  vorlauf                                            modell         ab  tage  breva  merkmal_r  merkmal_nmae   auc  auc_saison  auc_angeglichen  auc_gleiche_tage  auc_eigen  auc_kombi  ref_auc_gleiche_tage bereich_90
       14        1                                      ecmwf_ifs025 2024-02-04   956  198.0      0.897         0.320 0.886       0.834            0.886             0.886      0.847      0.886                   NaN        NaN
       14        1                              ecmwf_aifs025_single 2025-03-01   565  140.0      0.921         0.284 0.883       0.836            0.897             0.883      0.833      0.877                 0.890        NaN
       14        1                                         ecmwf_ifs 2025-10-01   340   71.0      0.887         0.328 0.924       0.878            0.906             0.925      0.867      0.961                 0.920        NaN
       14        1                                      ecmwf_ifs00z 2024-03-15   915  195.0      0.884         0.351 0.881       0.831            0.877             0.881      0.845      0.883                 0.884        NaN
       14        1                                      gfs_seamless 2024-02-04   956  198.0      0.836         0.459 0.851       0.786            0.849             0.851      0.835      0.850                 0.886        NaN
       14        1                                           icon_eu 2024-02-04   956  198.0      0.898         0.386 0.870       0.813            0.875             0.870      0.858      0.876                 0.886        NaN
       14        1                                     icon_seamless 2024-02-04   956  198.0      0.840         0.610 0.856       0.792            0.871             0.856      0.868      0.867                 0.886        NaN
       14        1                        italia_meteo_arpae_icon_2i 2025-04-14   502  118.0      0.823         0.530 0.860       0.795            0.879             0.860      0.818      0.853                 0.895        NaN
       14        1                              meteofrance_seamless 2024-02-04   956  198.0      0.803         0.615 0.839       0.782            0.843             0.839      0.864      0.882                 0.886        NaN
       14        1                               meteoswiss_icon_ch2 2025-07-04   440   92.0      0.840         0.667 0.871       0.812            0.870             0.871      0.796      0.858                 0.911        NaN
       14        1                                     ukmo_seamless 2024-08-08   753  144.0      0.842         0.552 0.851       0.784            0.860             0.851      0.828      0.853                 0.904        NaN
       14        1                            Mittel (langes Archiv) 2024-03-15   915  195.0        NaN           NaN 0.884       0.830              NaN               NaN        NaN        NaN                 0.884        NaN
       14        1               Mittel (langes Archiv), angeglichen 2024-03-15   915  195.0        NaN           NaN 0.886       0.835              NaN               NaN        NaN        NaN                 0.884        NaN
       14        1 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   623  142.0        NaN           NaN 0.887       0.828              NaN               NaN        NaN        NaN                 0.899        NaN
       14        2                                      ecmwf_ifs025 2024-02-05   955  198.0      0.883         0.340 0.873       0.818            0.862             0.873      0.841      0.872                   NaN        NaN
       14        2                              ecmwf_aifs025_single 2025-03-01   565  140.0      0.912         0.299 0.880       0.830            0.886             0.880      0.824      0.869                 0.879        NaN
       14        2                                         ecmwf_ifs 2025-10-02   339   70.0      0.872         0.342 0.899       0.836            0.880             0.947      0.747      0.947                 0.911        NaN
       14        2                                      ecmwf_ifs00z 2024-03-16   914  195.0      0.868         0.370 0.867       0.811            0.865             0.867      0.836      0.867                 0.874        NaN
       14        2                                      gfs_seamless 2024-02-05   955  198.0      0.817         0.481 0.846       0.780            0.843             0.846      0.821      0.854                 0.873        NaN
       14        2                                           icon_eu 2024-02-05   955  198.0      0.880         0.409 0.867       0.811            0.865             0.867      0.850      0.867                 0.873        NaN
       14        2                                     icon_seamless 2024-02-05   955  198.0      0.880         0.409 0.867       0.811            0.865             0.867      0.850      0.867                 0.873        NaN
       14        2                        italia_meteo_arpae_icon_2i 2025-04-15   490  111.0      0.815         0.550 0.849       0.780            0.862             0.849      0.807      0.823                 0.884        NaN
       14        2                              meteofrance_seamless 2024-02-05   955  198.0      0.811         0.449 0.806       0.763            0.805             0.806      0.844      0.865                 0.873        NaN
       14        2                               meteoswiss_icon_ch2 2025-07-05   439   92.0      0.826         0.686 0.878       0.819            0.870             0.878      0.795      0.848                 0.904        NaN
       14        2                                     ukmo_seamless 2024-08-07   581  118.0      0.614         0.756 0.857       0.788            0.869             0.857      0.819      0.863                 0.902        NaN
       14        2                            Mittel (langes Archiv) 2024-03-16   914  195.0        NaN           NaN 0.882       0.828              NaN               NaN        NaN        NaN                 0.874        NaN
       14        2               Mittel (langes Archiv), angeglichen 2024-03-16   914  195.0        NaN           NaN 0.875       0.821              NaN               NaN        NaN        NaN                 0.874        NaN
       14        2 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   623  142.0        NaN           NaN 0.878       0.814              NaN               NaN        NaN        NaN                 0.887        NaN
       14        3                                      ecmwf_ifs025 2024-02-06   954  197.0      0.867         0.364 0.864       0.802            0.859             0.864      0.827      0.864                   NaN        NaN
       14        3                              ecmwf_aifs025_single 2025-03-01   565  140.0      0.890         0.322 0.878       0.828            0.883             0.878      0.836      0.852                 0.863        NaN
       14        3                                         ecmwf_ifs 2025-10-03   338   70.0      0.850         0.370 0.896       0.838            0.888             0.899      0.679      0.899                 0.903        NaN
       14        3                                      ecmwf_ifs00z 2024-03-17   911  195.0      0.848         0.398 0.851       0.791            0.850             0.851      0.821      0.855                 0.862        NaN
       14        3                                      gfs_seamless 2024-02-06   954  197.0      0.791         0.512 0.843       0.775            0.839             0.843      0.804      0.847                 0.864        NaN
       14        3                                           icon_eu 2024-02-06   954  197.0      0.854         0.445 0.853       0.792            0.858             0.853      0.827      0.855                 0.864        NaN
       14        3                                     icon_seamless 2024-02-06   954  197.0      0.854         0.445 0.853       0.792            0.858             0.853      0.827      0.855                 0.864        NaN
       14        3                              meteofrance_seamless 2024-02-06   954  197.0      0.794         0.485 0.802       0.757            0.796             0.802      0.820      0.848                 0.864        NaN
       14        3                               meteoswiss_icon_ch2 2025-07-06   438   92.0      0.807         0.708 0.872       0.810            0.859             0.872      0.817      0.857                 0.893        NaN
       14        3                                     ukmo_seamless 2024-08-08   560  103.0      0.607         0.759 0.842       0.787            0.843             0.842      0.857      0.888                 0.892        NaN
       14        3                            Mittel (langes Archiv) 2024-03-17   911  195.0        NaN           NaN 0.870       0.815              NaN               NaN        NaN        NaN                 0.862        NaN
       14        3               Mittel (langes Archiv), angeglichen 2024-03-17   911  195.0        NaN           NaN 0.867       0.811              NaN               NaN        NaN        NaN                 0.862        NaN
       14        3 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621  142.0        NaN           NaN 0.866       0.803              NaN               NaN        NaN        NaN                 0.873        NaN
       14        4                                      ecmwf_ifs025 2024-02-07   953  197.0      0.839         0.394 0.843       0.773            0.840             0.843      0.814      0.838                   NaN        NaN
       14        4                                      ecmwf_ifs00z 2024-03-18   910  194.0      0.813         0.429 0.834       0.770            0.839             0.834      0.827      0.850                 0.843        NaN
       14        4                            Mittel (langes Archiv) 2024-03-18   910  194.0        NaN           NaN 0.849       0.786              NaN               NaN        NaN        NaN                 0.843        NaN
       14        4               Mittel (langes Archiv), angeglichen 2024-03-18   910  194.0        NaN           NaN 0.851       0.788              NaN               NaN        NaN        NaN                 0.843        NaN
       14        4 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621  141.0        NaN           NaN 0.858       0.790              NaN               NaN        NaN        NaN                 0.852        NaN
       14        5                                      ecmwf_ifs025 2024-02-08   952  197.0      0.799         0.444 0.823       0.754            0.822             0.823      0.803      0.828                   NaN        NaN
       14        5                              ecmwf_aifs025_single 2025-03-01   560  137.0      0.836         0.385 0.854       0.796            0.861             0.854      0.829      0.839                 0.825        NaN
       14        5                                         ecmwf_ifs 2025-10-05   347   77.0      0.781         0.452 0.875       0.804            0.859             0.921      0.988      0.945                 0.874        NaN
       14        5                                      ecmwf_ifs00z 2024-03-19   909  196.0      0.762         0.487 0.812       0.741            0.821             0.812      0.788      0.821                 0.822        NaN
       14        5                                      gfs_seamless 2024-02-08   952  197.0      0.714         0.592 0.826       0.751            0.821             0.826      0.794      0.828                 0.823        NaN
       14        5                                     icon_seamless 2024-02-08   952  197.0      0.760         0.507 0.819       0.753            0.812             0.819      0.798      0.820                 0.823        NaN
       14        5                                     ukmo_seamless 2024-08-16   565   97.0      0.528         0.830 0.798       0.710            0.796             0.798      0.779      0.855                 0.845        NaN
       14        5                            Mittel (langes Archiv) 2024-03-19   909  196.0        NaN           NaN 0.851       0.787              NaN               NaN        NaN        NaN                 0.822        NaN
       14        5               Mittel (langes Archiv), angeglichen 2024-03-19   909  196.0        NaN           NaN 0.849       0.782              NaN               NaN        NaN        NaN                 0.822        NaN
       14        5 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621  143.0        NaN           NaN 0.827       0.755              NaN               NaN        NaN        NaN                 0.834        NaN
       14        6                                      ecmwf_ifs025 2024-02-09   951  197.0      0.710         0.546 0.801       0.722            0.797             0.801      0.789      0.807                   NaN        NaN
       14        6                                      ecmwf_ifs00z 2024-03-20   908  194.0      0.714         0.530 0.813       0.735            0.810             0.813      0.796      0.834                 0.800        NaN
       14        6                            Mittel (langes Archiv) 2024-03-20   908  194.0        NaN           NaN 0.823       0.747              NaN               NaN        NaN        NaN                 0.800        NaN
       14        6               Mittel (langes Archiv), angeglichen 2024-03-20   908  194.0        NaN           NaN 0.819       0.743              NaN               NaN        NaN        NaN                 0.800        NaN
       14        6 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621  142.0        NaN           NaN 0.822       0.744              NaN               NaN        NaN        NaN                 0.820        NaN
       14        7                                      ecmwf_ifs025 2024-02-10   950  197.0      0.681         0.607 0.800       0.716            0.793             0.800      0.744      0.804                   NaN        NaN
       14        7                              ecmwf_aifs025_single 2025-03-01   565  140.0      0.745         0.472 0.832       0.765            0.835             0.832      0.757      0.816                 0.821        NaN
       14        7                                         ecmwf_ifs 2025-10-07   345   77.0      0.677         0.554 0.856       0.747            0.829             0.637      0.781      0.606                 0.878        NaN
       14        7                                      ecmwf_ifs00z 2024-03-21   907  192.0      0.660         0.580 0.764       0.678            0.770             0.764      0.737      0.775                 0.804        NaN
       14        7                                      gfs_seamless 2024-02-10   950  197.0      0.611         0.671 0.785       0.702            0.792             0.785      0.772      0.795                 0.800        NaN
       14        7                            Mittel (langes Archiv) 2024-03-21   907  192.0        NaN           NaN 0.820       0.740              NaN               NaN        NaN        NaN                 0.804        NaN
       14        7               Mittel (langes Archiv), angeglichen 2024-03-21   907  192.0        NaN           NaN 0.821       0.740              NaN               NaN        NaN        NaN                 0.804        NaN
       14        7 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621  141.0        NaN           NaN 0.840       0.767              NaN               NaN        NaN        NaN                 0.832        NaN
```

Unterschied zu ecmwf_ifs025 (Bootstrap über Wochen, 90 %-Bereich; schließt er 0 aus, ist der Unterschied belastbar):

```
 vorlauf                                               modell  tage    auc      bereich_90
       1                Δ ecmwf_aifs025_single − ecmwf_ifs025   565 -0.007 -0.021 … +0.007
       1              Δ ecmwf_aifs025_single|q − ecmwf_ifs025   565  0.006 -0.007 … +0.022
       1          Δ ecmwf_aifs025_single|kombi − ecmwf_ifs025   565 -0.013 -0.030 … +0.005
       1                           Δ ecmwf_ifs − ecmwf_ifs025   340  0.004 -0.013 … +0.021
       1                         Δ ecmwf_ifs|q − ecmwf_ifs025   340 -0.013 -0.033 … +0.004
       1                        Δ ecmwf_ifs00z − ecmwf_ifs025   915 -0.003 -0.016 … +0.011
       1                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   915 -0.007 -0.022 … +0.007
       1                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   915 -0.001 -0.014 … +0.012
       1                        Δ gfs_seamless − ecmwf_ifs025   956 -0.034 -0.051 … -0.017
       1                      Δ gfs_seamless|q − ecmwf_ifs025   956 -0.036 -0.054 … -0.019
       1                  Δ gfs_seamless|kombi − ecmwf_ifs025   956 -0.036 -0.053 … -0.017
       1                             Δ icon_eu − ecmwf_ifs025   956 -0.016 -0.030 … +0.000
       1                           Δ icon_eu|q − ecmwf_ifs025   956 -0.010 -0.026 … +0.005
       1                       Δ icon_eu|kombi − ecmwf_ifs025   956 -0.009 -0.023 … +0.004
       1                       Δ icon_seamless − ecmwf_ifs025   956 -0.029 -0.045 … -0.013
       1                     Δ icon_seamless|q − ecmwf_ifs025   956 -0.014 -0.029 … +0.001
       1                 Δ icon_seamless|kombi − ecmwf_ifs025   956 -0.019 -0.034 … -0.004
       1          Δ italia_meteo_arpae_icon_2i − ecmwf_ifs025   502 -0.035 -0.064 … -0.007
       1        Δ italia_meteo_arpae_icon_2i|q − ecmwf_ifs025   502 -0.016 -0.040 … +0.009
       1    Δ italia_meteo_arpae_icon_2i|kombi − ecmwf_ifs025   502 -0.042 -0.073 … -0.016
       1                Δ meteofrance_seamless − ecmwf_ifs025   956 -0.047 -0.063 … -0.031
       1              Δ meteofrance_seamless|q − ecmwf_ifs025   956 -0.043 -0.061 … -0.024
       1          Δ meteofrance_seamless|kombi − ecmwf_ifs025   956 -0.004 -0.022 … +0.016
       1                 Δ meteoswiss_icon_ch2 − ecmwf_ifs025   440 -0.040 -0.074 … -0.005
       1               Δ meteoswiss_icon_ch2|q − ecmwf_ifs025   440 -0.041 -0.074 … -0.007
       1           Δ meteoswiss_icon_ch2|kombi − ecmwf_ifs025   440 -0.052 -0.086 … -0.017
       1                       Δ ukmo_seamless − ecmwf_ifs025   753 -0.053 -0.075 … -0.032
       1                     Δ ukmo_seamless|q − ecmwf_ifs025   753 -0.044 -0.062 … -0.026
       1                 Δ ukmo_seamless|kombi − ecmwf_ifs025   753 -0.051 -0.071 … -0.031
       1              Δ Mittel (langes Archiv) − ecmwf_ifs025   915 -0.000 -0.011 … +0.010
       1 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   915  0.002 -0.009 … +0.013
       2                Δ ecmwf_aifs025_single − ecmwf_ifs025   565  0.002 -0.016 … +0.018
       2              Δ ecmwf_aifs025_single|q − ecmwf_ifs025   565  0.007 -0.008 … +0.024
       2          Δ ecmwf_aifs025_single|kombi − ecmwf_ifs025   565 -0.009 -0.029 … +0.010
       2                           Δ ecmwf_ifs − ecmwf_ifs025   339 -0.012 -0.028 … +0.003
       2                         Δ ecmwf_ifs|q − ecmwf_ifs025   339 -0.031 -0.054 … -0.007
       2                        Δ ecmwf_ifs00z − ecmwf_ifs025   914 -0.007 -0.019 … +0.006
       2                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   914 -0.009 -0.021 … +0.004
       2                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   914 -0.007 -0.019 … +0.004
       2                        Δ gfs_seamless − ecmwf_ifs025   955 -0.027 -0.045 … -0.008
       2                      Δ gfs_seamless|q − ecmwf_ifs025   955 -0.030 -0.048 … -0.011
       2                  Δ gfs_seamless|kombi − ecmwf_ifs025   955 -0.019 -0.036 … -0.003
       2                             Δ icon_eu − ecmwf_ifs025   955 -0.006 -0.023 … +0.009
       2                           Δ icon_eu|q − ecmwf_ifs025   955 -0.008 -0.025 … +0.008
       2                       Δ icon_eu|kombi − ecmwf_ifs025   955 -0.006 -0.022 … +0.010
       2                       Δ icon_seamless − ecmwf_ifs025   955 -0.006 -0.023 … +0.009
       2                     Δ icon_seamless|q − ecmwf_ifs025   955 -0.008 -0.025 … +0.008
       2                 Δ icon_seamless|kombi − ecmwf_ifs025   955 -0.006 -0.022 … +0.010
       2          Δ italia_meteo_arpae_icon_2i − ecmwf_ifs025   490 -0.035 -0.065 … -0.007
       2        Δ italia_meteo_arpae_icon_2i|q − ecmwf_ifs025   490 -0.022 -0.044 … +0.002
       2    Δ italia_meteo_arpae_icon_2i|kombi − ecmwf_ifs025   490 -0.062 -0.096 … -0.031
       2                Δ meteofrance_seamless − ecmwf_ifs025   955 -0.067 -0.098 … -0.037
       2              Δ meteofrance_seamless|q − ecmwf_ifs025   955 -0.068 -0.101 … -0.037
       2          Δ meteofrance_seamless|kombi − ecmwf_ifs025   955 -0.008 -0.024 … +0.008
       2                 Δ meteoswiss_icon_ch2 − ecmwf_ifs025   439 -0.026 -0.057 … +0.005
       2               Δ meteoswiss_icon_ch2|q − ecmwf_ifs025   439 -0.034 -0.068 … -0.002
       2           Δ meteoswiss_icon_ch2|kombi − ecmwf_ifs025   439 -0.056 -0.094 … -0.018
       2                       Δ ukmo_seamless − ecmwf_ifs025   581 -0.045 -0.073 … -0.018
       2                     Δ ukmo_seamless|q − ecmwf_ifs025   581 -0.033 -0.060 … -0.007
       2                 Δ ukmo_seamless|kombi − ecmwf_ifs025   581 -0.039 -0.067 … -0.015
       2              Δ Mittel (langes Archiv) − ecmwf_ifs025   914  0.008 -0.004 … +0.021
       2 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   914  0.001 -0.013 … +0.016
       3                Δ ecmwf_aifs025_single − ecmwf_ifs025   565  0.014 -0.005 … +0.033
       3              Δ ecmwf_aifs025_single|q − ecmwf_ifs025   565  0.020 +0.002 … +0.039
       3          Δ ecmwf_aifs025_single|kombi − ecmwf_ifs025   565 -0.011 -0.035 … +0.012
       3                           Δ ecmwf_ifs − ecmwf_ifs025   338 -0.008 -0.021 … +0.006
       3                         Δ ecmwf_ifs|q − ecmwf_ifs025   338 -0.015 -0.038 … +0.006
       3                        Δ ecmwf_ifs00z − ecmwf_ifs025   911 -0.011 -0.026 … +0.003
       3                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   911 -0.012 -0.026 … +0.003
       3                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   911 -0.007 -0.022 … +0.007
       3                        Δ gfs_seamless − ecmwf_ifs025   954 -0.021 -0.043 … +0.002
       3                      Δ gfs_seamless|q − ecmwf_ifs025   954 -0.025 -0.047 … -0.003
       3                  Δ gfs_seamless|kombi − ecmwf_ifs025   954 -0.017 -0.036 … +0.003
       3                             Δ icon_eu − ecmwf_ifs025   954 -0.011 -0.030 … +0.011
       3                           Δ icon_eu|q − ecmwf_ifs025   954 -0.006 -0.027 … +0.017
       3                       Δ icon_eu|kombi − ecmwf_ifs025   954 -0.009 -0.026 … +0.010
       3                       Δ icon_seamless − ecmwf_ifs025   954 -0.011 -0.030 … +0.011
       3                     Δ icon_seamless|q − ecmwf_ifs025   954 -0.006 -0.027 … +0.017
       3                 Δ icon_seamless|kombi − ecmwf_ifs025   954 -0.009 -0.026 … +0.010
       3                Δ meteofrance_seamless − ecmwf_ifs025   954 -0.061 -0.096 … -0.027
       3              Δ meteofrance_seamless|q − ecmwf_ifs025   954 -0.068 -0.103 … -0.031
       3          Δ meteofrance_seamless|kombi − ecmwf_ifs025   954 -0.016 -0.031 … +0.002
       3                 Δ meteoswiss_icon_ch2 − ecmwf_ifs025   438 -0.021 -0.053 … +0.010
       3               Δ meteoswiss_icon_ch2|q − ecmwf_ifs025   438 -0.035 -0.068 … -0.001
       3           Δ meteoswiss_icon_ch2|kombi − ecmwf_ifs025   438 -0.036 -0.072 … -0.001
       3                       Δ ukmo_seamless − ecmwf_ifs025   560 -0.049 -0.079 … -0.018
       3                     Δ ukmo_seamless|q − ecmwf_ifs025   560 -0.048 -0.080 … -0.019
       3                 Δ ukmo_seamless|kombi − ecmwf_ifs025   560 -0.004 -0.022 … +0.013
       3              Δ Mittel (langes Archiv) − ecmwf_ifs025   911  0.008 -0.007 … +0.024
       3 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   911  0.005 -0.010 … +0.022
       4                        Δ ecmwf_ifs00z − ecmwf_ifs025   910 -0.008 -0.028 … +0.010
       4                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   910 -0.004 -0.023 … +0.014
       4                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   910  0.007 -0.009 … +0.024
       4              Δ Mittel (langes Archiv) − ecmwf_ifs025   910  0.007 -0.003 … +0.016
       4 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   910  0.008 -0.003 … +0.019
       5                Δ ecmwf_aifs025_single − ecmwf_ifs025   560  0.029 +0.005 … +0.053
       5              Δ ecmwf_aifs025_single|q − ecmwf_ifs025   560  0.037 +0.013 … +0.062
       5          Δ ecmwf_aifs025_single|kombi − ecmwf_ifs025   560  0.014 -0.016 … +0.045
       5                           Δ ecmwf_ifs − ecmwf_ifs025   347  0.001 -0.015 … +0.017
       5                         Δ ecmwf_ifs|q − ecmwf_ifs025   347 -0.015 -0.034 … +0.005
       5                        Δ ecmwf_ifs00z − ecmwf_ifs025   909 -0.010 -0.031 … +0.011
       5                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   909 -0.001 -0.025 … +0.021
       5                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   909 -0.001 -0.021 … +0.018
       5                        Δ gfs_seamless − ecmwf_ifs025   952  0.003 -0.021 … +0.029
       5                      Δ gfs_seamless|q − ecmwf_ifs025   952 -0.002 -0.025 … +0.023
       5                  Δ gfs_seamless|kombi − ecmwf_ifs025   952  0.005 -0.018 … +0.028
       5                       Δ icon_seamless − ecmwf_ifs025   952 -0.003 -0.025 … +0.018
       5                     Δ icon_seamless|q − ecmwf_ifs025   952 -0.011 -0.033 … +0.011
       5                 Δ icon_seamless|kombi − ecmwf_ifs025   952 -0.003 -0.024 … +0.017
       5                       Δ ukmo_seamless − ecmwf_ifs025   565 -0.048 -0.088 … -0.010
       5                     Δ ukmo_seamless|q − ecmwf_ifs025   565 -0.050 -0.088 … -0.010
       5                 Δ ukmo_seamless|kombi − ecmwf_ifs025   565  0.010 -0.023 … +0.044
       5              Δ Mittel (langes Archiv) − ecmwf_ifs025   909  0.029 +0.014 … +0.045
       5 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   909  0.027 +0.011 … +0.045
       6                        Δ ecmwf_ifs00z − ecmwf_ifs025   908  0.013 -0.008 … +0.033
       6                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   908  0.010 -0.012 … +0.032
       6                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   908  0.033 +0.011 … +0.055
       6              Δ Mittel (langes Archiv) − ecmwf_ifs025   908  0.023 +0.011 … +0.035
       6 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   908  0.019 +0.004 … +0.035
       7                Δ ecmwf_aifs025_single − ecmwf_ifs025   565  0.010 -0.020 … +0.040
       7              Δ ecmwf_aifs025_single|q − ecmwf_ifs025   565  0.014 -0.016 … +0.044
       7          Δ ecmwf_aifs025_single|kombi − ecmwf_ifs025   565 -0.005 -0.038 … +0.028
       7                           Δ ecmwf_ifs − ecmwf_ifs025   345 -0.023 -0.048 … +0.002
       7                         Δ ecmwf_ifs|q − ecmwf_ifs025   345 -0.049 -0.083 … -0.018
       7                        Δ ecmwf_ifs00z − ecmwf_ifs025   907 -0.039 -0.070 … -0.010
       7                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   907 -0.033 -0.064 … -0.003
       7                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   907 -0.029 -0.057 … -0.001
       7                        Δ gfs_seamless − ecmwf_ifs025   950 -0.015 -0.050 … +0.020
       7                      Δ gfs_seamless|q − ecmwf_ifs025   950 -0.008 -0.040 … +0.025
       7                  Δ gfs_seamless|kombi − ecmwf_ifs025   950 -0.006 -0.034 … +0.023
       7              Δ Mittel (langes Archiv) − ecmwf_ifs025   907  0.017 -0.004 … +0.038
       7 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   907  0.018 -0.005 … +0.040
```

## ≥ 18 kn

merkmal_r: Übereinstimmung der Merkmale mit ERA5 (Korrelation, gewichtet mit der Wichtigkeit im Modell); auc_angeglichen: Merkmale vorher per Quantil-Angleichung auf ERA5-Verteilung gebracht; auc_eigen: Modell nur auf den eigenen Vorhersagen dieses Wettermodells trainiert (andere Jahre); auc_kombi: ERA5 + eigene Vorhersagen (3-fach gewichtet); auc_gleiche_tage: die ERA5-Variante auf genau diesen Tagen (Vergleichswert für eigen/kombi); ref_auc_gleiche_tage: ECMWF 0.25° auf denselben Tagen wie das Modell (paarweiser Vergleich). Alles je Jahr out-of-fold.

```
 schwelle  vorlauf                                            modell         ab  tage  breva  merkmal_r  merkmal_nmae   auc  auc_saison  auc_angeglichen  auc_gleiche_tage  auc_eigen  auc_kombi  ref_auc_gleiche_tage bereich_90
       18        1                                      ecmwf_ifs025 2024-02-04   956   57.0      0.892         0.328 0.744       0.682            0.752             0.744      0.736      0.766                   NaN        NaN
       18        1                              ecmwf_aifs025_single 2025-03-01   565   42.0      0.916         0.290 0.787       0.733            0.810             0.787      0.766      0.790                 0.731        NaN
       18        1                                         ecmwf_ifs 2025-10-01   340   22.0      0.881         0.336 0.753       0.673            0.771               NaN        NaN        NaN                 0.715        NaN
       18        1                                      ecmwf_ifs00z 2024-03-15   915   56.0      0.876         0.358 0.768       0.704            0.745             0.768      0.759      0.765                 0.744        NaN
       18        1                                      gfs_seamless 2024-02-04   956   57.0      0.823         0.465 0.831       0.763            0.808             0.831      0.740      0.780                 0.744        NaN
       18        1                                           icon_eu 2024-02-04   956   57.0      0.891         0.389 0.822       0.766            0.804             0.822      0.810      0.798                 0.744        NaN
       18        1                                     icon_seamless 2024-02-04   956   57.0      0.825         0.610 0.811       0.742            0.811             0.811      0.765      0.775                 0.744        NaN
       18        1                        italia_meteo_arpae_icon_2i 2025-04-14   502   37.0      0.810         0.545 0.825       0.773            0.820             0.825      0.720      0.791                 0.752        NaN
       18        1                              meteofrance_seamless 2024-02-04   956   57.0      0.786         0.613 0.755       0.693            0.778             0.755      0.783      0.818                 0.744        NaN
       18        1                               meteoswiss_icon_ch2 2025-07-04   440   31.0      0.824         0.669 0.833       0.777            0.803             0.833      0.537      0.803                 0.772        NaN
       18        1                                     ukmo_seamless 2024-08-08   753   39.0      0.832         0.549 0.793       0.718            0.775             0.793      0.741      0.762                 0.739        NaN
       18        1                            Mittel (langes Archiv) 2024-03-15   915   56.0        NaN           NaN 0.815       0.753              NaN               NaN        NaN        NaN                 0.744        NaN
       18        1               Mittel (langes Archiv), angeglichen 2024-03-15   915   56.0        NaN           NaN 0.795       0.745              NaN               NaN        NaN        NaN                 0.744        NaN
       18        1 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   623   41.0        NaN           NaN 0.743       0.671              NaN               NaN        NaN        NaN                 0.734        NaN
       18        2                                      ecmwf_ifs025 2024-02-05   955   57.0      0.876         0.348 0.745       0.683            0.750             0.745      0.803      0.780                   NaN        NaN
       18        2                              ecmwf_aifs025_single 2025-03-01   565   42.0      0.905         0.306 0.779       0.725            0.778             0.779      0.763      0.793                 0.742        NaN
       18        2                                         ecmwf_ifs 2025-10-02   339   22.0      0.862         0.354 0.735       0.658            0.752               NaN        NaN        NaN                 0.729        NaN
       18        2                                      ecmwf_ifs00z 2024-03-16   914   57.0      0.859         0.378 0.741       0.677            0.742             0.741      0.750      0.765                 0.748        NaN
       18        2                                      gfs_seamless 2024-02-05   955   57.0      0.801         0.489 0.829       0.762            0.799             0.829      0.758      0.757                 0.745        NaN
       18        2                                           icon_eu 2024-02-05   955   57.0      0.870         0.413 0.819       0.761            0.810             0.819      0.798      0.805                 0.745        NaN
       18        2                                     icon_seamless 2024-02-05   955   57.0      0.870         0.413 0.819       0.761            0.810             0.819      0.798      0.805                 0.745        NaN
       18        2                        italia_meteo_arpae_icon_2i 2025-04-15   490   30.0      0.802         0.565 0.763       0.696            0.743             0.763      0.606      0.739                 0.704        NaN
       18        2                              meteofrance_seamless 2024-02-05   955   57.0      0.804         0.465 0.731       0.699            0.704             0.731      0.758      0.781                 0.745        NaN
       18        2                               meteoswiss_icon_ch2 2025-07-05   439   31.0      0.807         0.691 0.854       0.797            0.828             0.854      0.523      0.807                 0.780        NaN
       18        2                                     ukmo_seamless 2024-08-07   581   36.0      0.703         0.604 0.841       0.769            0.842             0.841      0.762      0.834                 0.763        NaN
       18        2                            Mittel (langes Archiv) 2024-03-16   914   57.0        NaN           NaN 0.815       0.761              NaN               NaN        NaN        NaN                 0.748        NaN
       18        2               Mittel (langes Archiv), angeglichen 2024-03-16   914   57.0        NaN           NaN 0.767       0.722              NaN               NaN        NaN        NaN                 0.748        NaN
       18        2 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   623   42.0        NaN           NaN 0.762       0.697              NaN               NaN        NaN        NaN                 0.749        NaN
       18        3                                      ecmwf_ifs025 2024-02-06   954   57.0      0.858         0.372 0.767       0.709            0.767             0.767      0.818      0.794                   NaN        NaN
       18        3                              ecmwf_aifs025_single 2025-03-01   565   42.0      0.885         0.328 0.782       0.730            0.773             0.782      0.747      0.772                 0.747        NaN
       18        3                                         ecmwf_ifs 2025-10-03   338   22.0      0.838         0.381 0.736       0.656            0.781               NaN        NaN        NaN                 0.733        NaN
       18        3                                      ecmwf_ifs00z 2024-03-17   911   57.0      0.837         0.406 0.765       0.701            0.763             0.765      0.798      0.801                 0.770        NaN
       18        3                                      gfs_seamless 2024-02-06   954   57.0      0.772         0.521 0.800       0.728            0.797             0.800      0.773      0.781                 0.767        NaN
       18        3                                           icon_eu 2024-02-06   954   57.0      0.843         0.448 0.820       0.758            0.815             0.820      0.812      0.823                 0.767        NaN
       18        3                                     icon_seamless 2024-02-06   954   57.0      0.843         0.448 0.820       0.758            0.815             0.820      0.812      0.823                 0.767        NaN
       18        3                              meteofrance_seamless 2024-02-06   954   57.0      0.785         0.501 0.701       0.675            0.702             0.701      0.767      0.762                 0.767        NaN
       18        3                               meteoswiss_icon_ch2 2025-07-06   438   31.0      0.786         0.715 0.854       0.798            0.825             0.854      0.507      0.815                 0.784        NaN
       18        3                                     ukmo_seamless 2024-08-08   560   29.0      0.696         0.610 0.777       0.711            0.747             0.777      0.615      0.803                 0.740        NaN
       18        3                            Mittel (langes Archiv) 2024-03-17   911   57.0        NaN           NaN 0.799       0.741              NaN               NaN        NaN        NaN                 0.770        NaN
       18        3               Mittel (langes Archiv), angeglichen 2024-03-17   911   57.0        NaN           NaN 0.769       0.727              NaN               NaN        NaN        NaN                 0.770        NaN
       18        3 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621   42.0        NaN           NaN 0.790       0.716              NaN               NaN        NaN        NaN                 0.755        NaN
       18        4                                      ecmwf_ifs025 2024-02-07   953   57.0      0.829         0.403 0.740       0.674            0.751             0.740      0.815      0.804                   NaN        NaN
       18        4                                      ecmwf_ifs00z 2024-03-18   910   57.0      0.798         0.443 0.742       0.671            0.729             0.742      0.742      0.736                 0.744        NaN
       18        4                            Mittel (langes Archiv) 2024-03-18   910   57.0        NaN           NaN 0.758       0.688              NaN               NaN        NaN        NaN                 0.744        NaN
       18        4               Mittel (langes Archiv), angeglichen 2024-03-18   910   57.0        NaN           NaN 0.753       0.688              NaN               NaN        NaN        NaN                 0.744        NaN
       18        4 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621   42.0        NaN           NaN 0.746       0.676              NaN               NaN        NaN        NaN                 0.726        NaN
       18        5                                      ecmwf_ifs025 2024-02-08   952   57.0      0.785         0.455 0.721       0.656            0.739             0.721      0.779      0.746                   NaN        NaN
       18        5                              ecmwf_aifs025_single 2025-03-01   560   39.0      0.823         0.397 0.797       0.741            0.787             0.797      0.806      0.792                 0.702        NaN
       18        5                                         ecmwf_ifs 2025-10-05   347   28.0      0.773         0.461 0.763       0.684            0.761               NaN        NaN        NaN                 0.782        NaN
       18        5                                      ecmwf_ifs00z 2024-03-19   909   57.0      0.745         0.498 0.755       0.687            0.718             0.755      0.737      0.763                 0.725        NaN
       18        5                                      gfs_seamless 2024-02-08   952   57.0      0.692         0.598 0.788       0.719            0.792             0.788      0.748      0.772                 0.721        NaN
       18        5                                     icon_seamless 2024-02-08   952   57.0      0.744         0.518 0.734       0.654            0.740             0.734      0.745      0.714                 0.721        NaN
       18        5                                     ukmo_seamless 2024-08-16   565   26.0      0.604         0.692 0.763       0.682            0.753             0.763      0.587      0.780                 0.691        NaN
       18        5                            Mittel (langes Archiv) 2024-03-19   909   57.0        NaN           NaN 0.785       0.713              NaN               NaN        NaN        NaN                 0.725        NaN
       18        5               Mittel (langes Archiv), angeglichen 2024-03-19   909   57.0        NaN           NaN 0.787       0.722              NaN               NaN        NaN        NaN                 0.725        NaN
       18        5 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621   42.0        NaN           NaN 0.741       0.672              NaN               NaN        NaN        NaN                 0.726        NaN
       18        6                                      ecmwf_ifs025 2024-02-09   951   57.0      0.705         0.530 0.716       0.653            0.739             0.716      0.758      0.736                   NaN        NaN
       18        6                                      ecmwf_ifs00z 2024-03-20   908   56.0      0.694         0.544 0.747       0.674            0.741             0.747      0.781      0.784                 0.730        NaN
       18        6                            Mittel (langes Archiv) 2024-03-20   908   56.0        NaN           NaN 0.758       0.685              NaN               NaN        NaN        NaN                 0.730        NaN
       18        6               Mittel (langes Archiv), angeglichen 2024-03-20   908   56.0        NaN           NaN 0.758       0.686              NaN               NaN        NaN        NaN                 0.730        NaN
       18        6 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621   42.0        NaN           NaN 0.736       0.676              NaN               NaN        NaN        NaN                 0.747        NaN
       18        7                                      ecmwf_ifs025 2024-02-10   950   57.0      0.667         0.588 0.743       0.678            0.738             0.743      0.725      0.754                   NaN        NaN
       18        7                              ecmwf_aifs025_single 2025-03-01   565   42.0      0.724         0.485 0.763       0.710            0.734             0.763      0.761      0.768                 0.766        NaN
       18        7                                         ecmwf_ifs 2025-10-07   345   28.0      0.662         0.565 0.795       0.713            0.789               NaN        NaN        NaN                 0.814        NaN
       18        7                                      ecmwf_ifs00z 2024-03-21   907   56.0      0.637         0.595 0.727       0.659            0.709             0.727      0.780      0.759                 0.753        NaN
       18        7                                      gfs_seamless 2024-02-10   950   57.0      0.581         0.680 0.756       0.681            0.764             0.756      0.728      0.751                 0.743        NaN
       18        7                            Mittel (langes Archiv) 2024-03-21   907   56.0        NaN           NaN 0.787       0.713              NaN               NaN        NaN        NaN                 0.753        NaN
       18        7               Mittel (langes Archiv), angeglichen 2024-03-21   907   56.0        NaN           NaN 0.788       0.720              NaN               NaN        NaN        NaN                 0.753        NaN
       18        7 je Merkmal bestes (gewählt 2024, bewertet danach)        NaN   621   42.0        NaN           NaN 0.747       0.679              NaN               NaN        NaN        NaN                 0.773        NaN
```

Unterschied zu ecmwf_ifs025 (Bootstrap über Wochen, 90 %-Bereich; schließt er 0 aus, ist der Unterschied belastbar):

```
 vorlauf                                               modell  tage    auc      bereich_90
       1                Δ ecmwf_aifs025_single − ecmwf_ifs025   565  0.055 +0.019 … +0.094
       1              Δ ecmwf_aifs025_single|q − ecmwf_ifs025   565  0.078 +0.044 … +0.117
       1          Δ ecmwf_aifs025_single|kombi − ecmwf_ifs025   565  0.059 +0.013 … +0.107
       1                           Δ ecmwf_ifs − ecmwf_ifs025   340  0.038 +0.002 … +0.081
       1                         Δ ecmwf_ifs|q − ecmwf_ifs025   340  0.056 +0.018 … +0.104
       1                        Δ ecmwf_ifs00z − ecmwf_ifs025   915  0.024 +0.001 … +0.050
       1                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   915  0.002 -0.025 … +0.029
       1                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   915  0.021 -0.011 … +0.054
       1                        Δ gfs_seamless − ecmwf_ifs025   956  0.087 +0.043 … +0.139
       1                      Δ gfs_seamless|q − ecmwf_ifs025   956  0.065 +0.030 … +0.104
       1                  Δ gfs_seamless|kombi − ecmwf_ifs025   956  0.036 -0.003 … +0.086
       1                             Δ icon_eu − ecmwf_ifs025   956  0.078 +0.047 … +0.110
       1                           Δ icon_eu|q − ecmwf_ifs025   956  0.060 +0.028 … +0.093
       1                       Δ icon_eu|kombi − ecmwf_ifs025   956  0.054 +0.020 … +0.089
       1                       Δ icon_seamless − ecmwf_ifs025   956  0.067 +0.026 … +0.112
       1                     Δ icon_seamless|q − ecmwf_ifs025   956  0.067 +0.033 … +0.103
       1                 Δ icon_seamless|kombi − ecmwf_ifs025   956  0.032 -0.010 … +0.075
       1          Δ italia_meteo_arpae_icon_2i − ecmwf_ifs025   502  0.073 +0.029 … +0.120
       1        Δ italia_meteo_arpae_icon_2i|q − ecmwf_ifs025   502  0.069 +0.031 … +0.105
       1    Δ italia_meteo_arpae_icon_2i|kombi − ecmwf_ifs025   502  0.039 -0.002 … +0.080
       1                Δ meteofrance_seamless − ecmwf_ifs025   956  0.011 -0.028 … +0.051
       1              Δ meteofrance_seamless|q − ecmwf_ifs025   956  0.034 -0.004 … +0.068
       1          Δ meteofrance_seamless|kombi − ecmwf_ifs025   956  0.074 +0.025 … +0.134
       1                 Δ meteoswiss_icon_ch2 − ecmwf_ifs025   440  0.061 +0.004 … +0.118
       1               Δ meteoswiss_icon_ch2|q − ecmwf_ifs025   440  0.031 -0.008 … +0.072
       1           Δ meteoswiss_icon_ch2|kombi − ecmwf_ifs025   440  0.031 -0.021 … +0.078
       1                       Δ ukmo_seamless − ecmwf_ifs025   753  0.054 +0.005 … +0.103
       1                     Δ ukmo_seamless|q − ecmwf_ifs025   753  0.036 -0.010 … +0.079
       1                 Δ ukmo_seamless|kombi − ecmwf_ifs025   753  0.024 -0.027 … +0.078
       1              Δ Mittel (langes Archiv) − ecmwf_ifs025   915  0.071 +0.043 … +0.102
       1 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   915  0.052 +0.028 … +0.077
       2                Δ ecmwf_aifs025_single − ecmwf_ifs025   565  0.036 -0.005 … +0.078
       2              Δ ecmwf_aifs025_single|q − ecmwf_ifs025   565  0.036 +0.005 … +0.070
       2          Δ ecmwf_aifs025_single|kombi − ecmwf_ifs025   565  0.051 +0.005 … +0.101
       2                           Δ ecmwf_ifs − ecmwf_ifs025   339  0.006 -0.034 … +0.050
       2                         Δ ecmwf_ifs|q − ecmwf_ifs025   339  0.023 -0.054 … +0.094
       2                        Δ ecmwf_ifs00z − ecmwf_ifs025   914 -0.007 -0.037 … +0.025
       2                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   914 -0.006 -0.042 … +0.029
       2                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   914  0.018 -0.012 … +0.050
       2                        Δ gfs_seamless − ecmwf_ifs025   955  0.085 +0.045 … +0.129
       2                      Δ gfs_seamless|q − ecmwf_ifs025   955  0.054 +0.021 … +0.091
       2                  Δ gfs_seamless|kombi − ecmwf_ifs025   955  0.012 -0.034 … +0.058
       2                             Δ icon_eu − ecmwf_ifs025   955  0.075 +0.046 … +0.104
       2                           Δ icon_eu|q − ecmwf_ifs025   955  0.065 +0.043 … +0.092
       2                       Δ icon_eu|kombi − ecmwf_ifs025   955  0.060 +0.028 … +0.095
       2                       Δ icon_seamless − ecmwf_ifs025   955  0.075 +0.046 … +0.104
       2                     Δ icon_seamless|q − ecmwf_ifs025   955  0.065 +0.043 … +0.092
       2                 Δ icon_seamless|kombi − ecmwf_ifs025   955  0.060 +0.028 … +0.095
       2          Δ italia_meteo_arpae_icon_2i − ecmwf_ifs025   490  0.059 +0.016 … +0.101
       2        Δ italia_meteo_arpae_icon_2i|q − ecmwf_ifs025   490  0.039 -0.006 … +0.085
       2    Δ italia_meteo_arpae_icon_2i|kombi − ecmwf_ifs025   490  0.035 -0.025 … +0.088
       2                Δ meteofrance_seamless − ecmwf_ifs025   955 -0.014 -0.061 … +0.026
       2              Δ meteofrance_seamless|q − ecmwf_ifs025   955 -0.041 -0.090 … +0.005
       2          Δ meteofrance_seamless|kombi − ecmwf_ifs025   955  0.036 -0.007 … +0.079
       2                 Δ meteoswiss_icon_ch2 − ecmwf_ifs025   439  0.074 +0.017 … +0.138
       2               Δ meteoswiss_icon_ch2|q − ecmwf_ifs025   439  0.048 -0.003 … +0.103
       2           Δ meteoswiss_icon_ch2|kombi − ecmwf_ifs025   439  0.027 -0.029 … +0.084
       2                       Δ ukmo_seamless − ecmwf_ifs025   581  0.077 +0.025 … +0.137
       2                     Δ ukmo_seamless|q − ecmwf_ifs025   581  0.079 +0.027 … +0.134
       2                 Δ ukmo_seamless|kombi − ecmwf_ifs025   581  0.070 +0.019 … +0.126
       2              Δ Mittel (langes Archiv) − ecmwf_ifs025   914  0.067 +0.047 … +0.092
       2 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   914  0.020 -0.009 … +0.053
       3                Δ ecmwf_aifs025_single − ecmwf_ifs025   565  0.034 +0.002 … +0.071
       3              Δ ecmwf_aifs025_single|q − ecmwf_ifs025   565  0.026 +0.002 … +0.051
       3          Δ ecmwf_aifs025_single|kombi − ecmwf_ifs025   565  0.025 -0.009 … +0.061
       3                           Δ ecmwf_ifs − ecmwf_ifs025   338  0.003 -0.043 … +0.059
       3                         Δ ecmwf_ifs|q − ecmwf_ifs025   338  0.048 -0.011 … +0.133
       3                        Δ ecmwf_ifs00z − ecmwf_ifs025   911 -0.005 -0.026 … +0.018
       3                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   911 -0.007 -0.035 … +0.021
       3                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   911  0.031 +0.007 … +0.056
       3                        Δ gfs_seamless − ecmwf_ifs025   954  0.032 -0.014 … +0.081
       3                      Δ gfs_seamless|q − ecmwf_ifs025   954  0.030 -0.013 … +0.073
       3                  Δ gfs_seamless|kombi − ecmwf_ifs025   954  0.013 -0.022 … +0.054
       3                             Δ icon_eu − ecmwf_ifs025   954  0.053 +0.022 … +0.086
       3                           Δ icon_eu|q − ecmwf_ifs025   954  0.047 +0.020 … +0.074
       3                       Δ icon_eu|kombi − ecmwf_ifs025   954  0.056 +0.024 … +0.088
       3                       Δ icon_seamless − ecmwf_ifs025   954  0.053 +0.022 … +0.086
       3                     Δ icon_seamless|q − ecmwf_ifs025   954  0.047 +0.020 … +0.074
       3                 Δ icon_seamless|kombi − ecmwf_ifs025   954  0.056 +0.024 … +0.088
       3                Δ meteofrance_seamless − ecmwf_ifs025   954 -0.066 -0.116 … -0.028
       3              Δ meteofrance_seamless|q − ecmwf_ifs025   954 -0.065 -0.114 … -0.024
       3          Δ meteofrance_seamless|kombi − ecmwf_ifs025   954 -0.005 -0.042 … +0.028
       3                 Δ meteoswiss_icon_ch2 − ecmwf_ifs025   438  0.071 +0.034 … +0.119
       3               Δ meteoswiss_icon_ch2|q − ecmwf_ifs025   438  0.041 +0.007 … +0.078
       3           Δ meteoswiss_icon_ch2|kombi − ecmwf_ifs025   438  0.031 -0.002 … +0.071
       3                       Δ ukmo_seamless − ecmwf_ifs025   560  0.037 -0.033 … +0.099
       3                     Δ ukmo_seamless|q − ecmwf_ifs025   560  0.007 -0.060 … +0.063
       3                 Δ ukmo_seamless|kombi − ecmwf_ifs025   560  0.063 -0.014 … +0.137
       3              Δ Mittel (langes Archiv) − ecmwf_ifs025   911  0.029 +0.004 … +0.055
       3 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   911 -0.001 -0.031 … +0.029
       4                        Δ ecmwf_ifs00z − ecmwf_ifs025   910 -0.002 -0.043 … +0.037
       4                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   910 -0.015 -0.065 … +0.031
       4                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   910 -0.008 -0.054 … +0.038
       4              Δ Mittel (langes Archiv) − ecmwf_ifs025   910  0.014 -0.003 … +0.032
       4 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   910  0.009 -0.018 … +0.036
       5                Δ ecmwf_aifs025_single − ecmwf_ifs025   560  0.095 +0.049 … +0.148
       5              Δ ecmwf_aifs025_single|q − ecmwf_ifs025   560  0.085 +0.035 … +0.140
       5          Δ ecmwf_aifs025_single|kombi − ecmwf_ifs025   560  0.090 +0.037 … +0.148
       5                           Δ ecmwf_ifs − ecmwf_ifs025   347 -0.019 -0.063 … +0.023
       5                         Δ ecmwf_ifs|q − ecmwf_ifs025   347 -0.021 -0.068 … +0.026
       5                        Δ ecmwf_ifs00z − ecmwf_ifs025   909  0.030 -0.015 … +0.072
       5                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   909 -0.007 -0.054 … +0.036
       5                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   909  0.039 -0.002 … +0.083
       5                        Δ gfs_seamless − ecmwf_ifs025   952  0.067 +0.013 … +0.125
       5                      Δ gfs_seamless|q − ecmwf_ifs025   952  0.070 +0.019 … +0.127
       5                  Δ gfs_seamless|kombi − ecmwf_ifs025   952  0.051 -0.002 … +0.102
       5                       Δ icon_seamless − ecmwf_ifs025   952  0.013 -0.031 … +0.054
       5                     Δ icon_seamless|q − ecmwf_ifs025   952  0.018 -0.025 … +0.060
       5                 Δ icon_seamless|kombi − ecmwf_ifs025   952 -0.007 -0.056 … +0.040
       5                       Δ ukmo_seamless − ecmwf_ifs025   565  0.072 -0.017 … +0.158
       5                     Δ ukmo_seamless|q − ecmwf_ifs025   565  0.062 -0.031 … +0.153
       5                 Δ ukmo_seamless|kombi − ecmwf_ifs025   565  0.089 +0.010 … +0.167
       5              Δ Mittel (langes Archiv) − ecmwf_ifs025   909  0.061 +0.019 … +0.106
       5 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   909  0.063 +0.025 … +0.105
       6                        Δ ecmwf_ifs00z − ecmwf_ifs025   908  0.018 -0.031 … +0.074
       6                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   908  0.012 -0.035 … +0.058
       6                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   908  0.055 +0.004 … +0.111
       6              Δ Mittel (langes Archiv) − ecmwf_ifs025   908  0.028 +0.001 … +0.061
       6 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   908  0.029 -0.000 … +0.061
       7                Δ ecmwf_aifs025_single − ecmwf_ifs025   565 -0.003 -0.055 … +0.046
       7              Δ ecmwf_aifs025_single|q − ecmwf_ifs025   565 -0.032 -0.082 … +0.016
       7          Δ ecmwf_aifs025_single|kombi − ecmwf_ifs025   565  0.001 -0.058 … +0.055
       7                           Δ ecmwf_ifs − ecmwf_ifs025   345 -0.019 -0.065 … +0.030
       7                         Δ ecmwf_ifs|q − ecmwf_ifs025   345 -0.025 -0.064 … +0.011
       7                        Δ ecmwf_ifs00z − ecmwf_ifs025   907 -0.026 -0.084 … +0.026
       7                      Δ ecmwf_ifs00z|q − ecmwf_ifs025   907 -0.043 -0.097 … +0.006
       7                  Δ ecmwf_ifs00z|kombi − ecmwf_ifs025   907  0.007 -0.044 … +0.059
       7                        Δ gfs_seamless − ecmwf_ifs025   950  0.012 -0.044 … +0.072
       7                      Δ gfs_seamless|q − ecmwf_ifs025   950  0.021 -0.040 … +0.085
       7                  Δ gfs_seamless|kombi − ecmwf_ifs025   950  0.008 -0.043 … +0.064
       7              Δ Mittel (langes Archiv) − ecmwf_ifs025   907  0.034 -0.003 … +0.075
       7 Δ Mittel (langes Archiv), angeglichen − ecmwf_ifs025   907  0.036 +0.000 … +0.073
```
