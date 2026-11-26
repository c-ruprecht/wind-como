# Trainingsbasis: ERA5 oder ECMWF IFS 9 km

Out-of-fold je Testjahr 2024–2026, Ziel B. Alle Basen je Zeile auf denselben Tagen. Δ: Unterschied zu „ERA5 ab 2014“ (Wochen-Bootstrap, 90 %-Bereich).


## ≥ 14 kn – AUC

```
basis                 ERA5 + IFS 9 km  ERA5 ab 2014  ERA5 ab 2017  IFS 9 km ab 2017
quelle       vorlauf                                                               
ecmwf_ifs025 1                  0.873         0.886         0.867             0.860
             2                  0.860         0.874         0.850             0.851
             3                  0.858         0.865         0.846             0.850
             4                  0.839         0.844         0.820             0.834
             5                  0.820         0.824         0.804             0.814
             6                  0.808         0.802         0.774             0.801
             7                  0.793         0.801         0.778             0.782
```

Unterschied zu ERA5 ab 2014:

```
      quelle  vorlauf            basis  delta      bereich_90
ecmwf_ifs025        1     ERA5 ab 2017 -0.020 -0.032 … -0.007
ecmwf_ifs025        1 IFS 9 km ab 2017 -0.026 -0.041 … -0.011
ecmwf_ifs025        1  ERA5 + IFS 9 km -0.013 -0.024 … -0.002
ecmwf_ifs025        2     ERA5 ab 2017 -0.024 -0.036 … -0.013
ecmwf_ifs025        2 IFS 9 km ab 2017 -0.023 -0.037 … -0.008
ecmwf_ifs025        2  ERA5 + IFS 9 km -0.014 -0.024 … -0.004
ecmwf_ifs025        3     ERA5 ab 2017 -0.018 -0.031 … -0.006
ecmwf_ifs025        3 IFS 9 km ab 2017 -0.015 -0.028 … -0.002
ecmwf_ifs025        3  ERA5 + IFS 9 km -0.006 -0.016 … +0.004
ecmwf_ifs025        4     ERA5 ab 2017 -0.024 -0.037 … -0.012
ecmwf_ifs025        4 IFS 9 km ab 2017 -0.010 -0.026 … +0.005
ecmwf_ifs025        4  ERA5 + IFS 9 km -0.005 -0.015 … +0.007
ecmwf_ifs025        5     ERA5 ab 2017 -0.020 -0.032 … -0.008
ecmwf_ifs025        5 IFS 9 km ab 2017 -0.009 -0.022 … +0.003
ecmwf_ifs025        5  ERA5 + IFS 9 km -0.004 -0.013 … +0.005
ecmwf_ifs025        6     ERA5 ab 2017 -0.027 -0.040 … -0.015
ecmwf_ifs025        6 IFS 9 km ab 2017 -0.001 -0.016 … +0.014
ecmwf_ifs025        6  ERA5 + IFS 9 km  0.006 -0.005 … +0.018
ecmwf_ifs025        7     ERA5 ab 2017 -0.024 -0.038 … -0.010
ecmwf_ifs025        7 IFS 9 km ab 2017 -0.020 -0.033 … -0.006
ecmwf_ifs025        7  ERA5 + IFS 9 km -0.009 -0.020 … +0.003
```

## ≥ 18 kn – AUC

```
basis                 ERA5 + IFS 9 km  ERA5 ab 2014  ERA5 ab 2017  IFS 9 km ab 2017
quelle       vorlauf                                                               
ecmwf_ifs025 1                  0.764         0.745         0.726             0.772
             2                  0.754         0.746         0.733             0.746
             3                  0.779         0.768         0.763             0.784
             4                  0.765         0.741         0.756             0.761
             5                  0.747         0.723         0.723             0.757
             6                  0.729         0.718         0.692             0.738
             7                  0.728         0.745         0.735             0.724
```

Unterschied zu ERA5 ab 2014:

```
      quelle  vorlauf            basis  delta      bereich_90
ecmwf_ifs025        1     ERA5 ab 2017 -0.019 -0.041 … +0.002
ecmwf_ifs025        1 IFS 9 km ab 2017  0.027 -0.003 … +0.054
ecmwf_ifs025        1  ERA5 + IFS 9 km  0.019 -0.002 … +0.040
ecmwf_ifs025        2     ERA5 ab 2017 -0.013 -0.037 … +0.007
ecmwf_ifs025        2 IFS 9 km ab 2017  0.000 -0.030 … +0.030
ecmwf_ifs025        2  ERA5 + IFS 9 km  0.008 -0.018 … +0.034
ecmwf_ifs025        3     ERA5 ab 2017 -0.005 -0.024 … +0.016
ecmwf_ifs025        3 IFS 9 km ab 2017  0.016 -0.011 … +0.042
ecmwf_ifs025        3  ERA5 + IFS 9 km  0.010 -0.008 … +0.029
ecmwf_ifs025        4     ERA5 ab 2017  0.015 -0.006 … +0.035
ecmwf_ifs025        4 IFS 9 km ab 2017  0.020 -0.008 … +0.052
ecmwf_ifs025        4  ERA5 + IFS 9 km  0.024 +0.001 … +0.047
ecmwf_ifs025        5     ERA5 ab 2017  0.000 -0.017 … +0.016
ecmwf_ifs025        5 IFS 9 km ab 2017  0.034 +0.002 … +0.068
ecmwf_ifs025        5  ERA5 + IFS 9 km  0.024 +0.004 … +0.047
ecmwf_ifs025        6     ERA5 ab 2017 -0.026 -0.046 … -0.006
ecmwf_ifs025        6 IFS 9 km ab 2017  0.020 -0.011 … +0.054
ecmwf_ifs025        6  ERA5 + IFS 9 km  0.011 -0.010 … +0.035
ecmwf_ifs025        7     ERA5 ab 2017 -0.010 -0.031 … +0.011
ecmwf_ifs025        7 IFS 9 km ab 2017 -0.020 -0.049 … +0.006
ecmwf_ifs025        7  ERA5 + IFS 9 km -0.017 -0.039 … +0.004
```
