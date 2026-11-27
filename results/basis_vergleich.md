# Trainingsbasis: ERA5 oder ECMWF IFS 9 km

Out-of-fold je Testjahr 2024–2026, Ziel B. Alle Basen je Zeile auf denselben Tagen. Δ: Unterschied zu „ERA5 ab 2014“ (Wochen-Bootstrap, 90 %-Bereich).


## ≥ 14 kn – AUC

```
basis                 ERA5 + IFS 9 km  ERA5 ab 2014  ERA5 ab 2017  IFS 9 km ab 2017
quelle       vorlauf                                                               
ecmwf_ifs00z 0                  0.879         0.881         0.863             0.882
             1                  0.875         0.882         0.866             0.869
             2                  0.860         0.868         0.850             0.859
             3                  0.852         0.851         0.839             0.848
             4                  0.840         0.835         0.823             0.846
             5                  0.821         0.814         0.796             0.821
             6                  0.817         0.814         0.802             0.814
             7                  0.769         0.766         0.752             0.773
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
ecmwf_ifs00z        0     ERA5 ab 2017 -0.018 -0.028 … -0.007
ecmwf_ifs00z        0 IFS 9 km ab 2017  0.001 -0.012 … +0.015
ecmwf_ifs00z        0  ERA5 + IFS 9 km -0.001 -0.012 … +0.009
ecmwf_ifs00z        1     ERA5 ab 2017 -0.016 -0.026 … -0.006
ecmwf_ifs00z        1 IFS 9 km ab 2017 -0.013 -0.027 … +0.000
ecmwf_ifs00z        1  ERA5 + IFS 9 km -0.007 -0.017 … +0.004
ecmwf_ifs00z        2     ERA5 ab 2017 -0.018 -0.029 … -0.008
ecmwf_ifs00z        2 IFS 9 km ab 2017 -0.009 -0.023 … +0.006
ecmwf_ifs00z        2  ERA5 + IFS 9 km -0.008 -0.018 … +0.003
ecmwf_ifs00z        3     ERA5 ab 2017 -0.013 -0.024 … -0.002
ecmwf_ifs00z        3 IFS 9 km ab 2017 -0.003 -0.017 … +0.011
ecmwf_ifs00z        3  ERA5 + IFS 9 km  0.001 -0.010 … +0.012
ecmwf_ifs00z        4     ERA5 ab 2017 -0.012 -0.023 … -0.002
ecmwf_ifs00z        4 IFS 9 km ab 2017  0.011 -0.001 … +0.022
ecmwf_ifs00z        4  ERA5 + IFS 9 km  0.005 -0.003 … +0.014
ecmwf_ifs00z        5     ERA5 ab 2017 -0.018 -0.029 … -0.006
ecmwf_ifs00z        5 IFS 9 km ab 2017  0.007 -0.007 … +0.022
ecmwf_ifs00z        5  ERA5 + IFS 9 km  0.008 -0.003 … +0.018
ecmwf_ifs00z        6     ERA5 ab 2017 -0.012 -0.023 … -0.002
ecmwf_ifs00z        6 IFS 9 km ab 2017  0.000 -0.015 … +0.016
ecmwf_ifs00z        6  ERA5 + IFS 9 km  0.003 -0.009 … +0.015
ecmwf_ifs00z        7     ERA5 ab 2017 -0.014 -0.028 … -0.000
ecmwf_ifs00z        7 IFS 9 km ab 2017  0.007 -0.006 … +0.020
ecmwf_ifs00z        7  ERA5 + IFS 9 km  0.003 -0.007 … +0.014
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
ecmwf_ifs00z 0                  0.781         0.793         0.774             0.796
             1                  0.754         0.769         0.755             0.761
             2                  0.750         0.742         0.726             0.759
             3                  0.785         0.766         0.765             0.797
             4                  0.757         0.743         0.752             0.765
             5                  0.739         0.756         0.744             0.748
             6                  0.756         0.749         0.720             0.763
             7                  0.717         0.728         0.718             0.736
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
ecmwf_ifs00z        0     ERA5 ab 2017 -0.019 -0.040 … -0.001
ecmwf_ifs00z        0 IFS 9 km ab 2017  0.003 -0.016 … +0.025
ecmwf_ifs00z        0  ERA5 + IFS 9 km -0.012 -0.037 … +0.013
ecmwf_ifs00z        1     ERA5 ab 2017 -0.013 -0.029 … +0.001
ecmwf_ifs00z        1 IFS 9 km ab 2017 -0.008 -0.028 … +0.015
ecmwf_ifs00z        1  ERA5 + IFS 9 km -0.015 -0.033 … +0.004
ecmwf_ifs00z        2     ERA5 ab 2017 -0.016 -0.033 … +0.001
ecmwf_ifs00z        2 IFS 9 km ab 2017  0.017 -0.011 … +0.045
ecmwf_ifs00z        2  ERA5 + IFS 9 km  0.008 -0.016 … +0.030
ecmwf_ifs00z        3     ERA5 ab 2017 -0.001 -0.022 … +0.018
ecmwf_ifs00z        3 IFS 9 km ab 2017  0.031 +0.005 … +0.062
ecmwf_ifs00z        3  ERA5 + IFS 9 km  0.019 -0.004 … +0.042
ecmwf_ifs00z        4     ERA5 ab 2017  0.009 -0.009 … +0.028
ecmwf_ifs00z        4 IFS 9 km ab 2017  0.022 -0.002 … +0.049
ecmwf_ifs00z        4  ERA5 + IFS 9 km  0.014 -0.006 … +0.037
ecmwf_ifs00z        5     ERA5 ab 2017 -0.012 -0.029 … +0.003
ecmwf_ifs00z        5 IFS 9 km ab 2017 -0.008 -0.033 … +0.020
ecmwf_ifs00z        5  ERA5 + IFS 9 km -0.017 -0.040 … +0.005
ecmwf_ifs00z        6     ERA5 ab 2017 -0.029 -0.052 … -0.006
ecmwf_ifs00z        6 IFS 9 km ab 2017  0.014 -0.022 … +0.050
ecmwf_ifs00z        6  ERA5 + IFS 9 km  0.008 -0.016 … +0.030
ecmwf_ifs00z        7     ERA5 ab 2017 -0.010 -0.031 … +0.010
ecmwf_ifs00z        7 IFS 9 km ab 2017  0.008 -0.021 … +0.040
ecmwf_ifs00z        7  ERA5 + IFS 9 km -0.011 -0.035 … +0.014
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
