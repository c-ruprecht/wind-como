# Same-Day-Modell, stündlich

Prüfung 2024–2026 je Jahr out-of-fold; Vorhersage-Teil aus ecmwf_ifs025 (Vorlauf 1). Stufen: V nur Vorhersage, W + gemessener Wind, A + ARPA-Treiber.


## Kommt nach dieser Stunde noch ≥ 14 kn (≥ 2 h)? – AUC März–Oktober

```
stufe   A + ARPA-Treiber  V Vorhersage  W + Wind
stunde                                          
8.0                0.843         0.838     0.839
9.0                0.853         0.838     0.845
10.0               0.859         0.836     0.844
11.0               0.871         0.838     0.858
12.0               0.887         0.842     0.878
13.0               0.901         0.847     0.897
14.0               0.913         0.851     0.907
15.0               0.920         0.854     0.915
16.0               0.937         0.861     0.928
17.0               0.941         0.850     0.931
```

## Kommt nach dieser Stunde noch ≥ 18 kn (≥ 2 h)? – AUC März–Oktober

```
stufe   A + ARPA-Treiber  V Vorhersage  W + Wind
stunde                                          
8.0                0.729         0.686     0.701
9.0                0.740         0.686     0.702
10.0               0.744         0.686     0.714
11.0               0.756         0.686     0.730
12.0               0.772         0.691     0.752
13.0               0.794         0.686     0.780
14.0               0.827         0.694     0.811
15.0               0.831         0.691     0.820
16.0               0.905         0.761     0.899
17.0               0.897         0.740     0.884
```

## Wind auf dem See in k Stunden – mittlerer Fehler (kn), März–Oktober, 9–16 Uhr

```
stufe           A + ARPA-Treiber  V Vorhersage  W + Wind  Persistenz
stunden_voraus                                                      
1.0                         2.19          3.72      2.26        2.38
2.0                         3.18          4.04      3.34        3.91
3.0                         3.62          4.20      3.79        4.99
4.0                         3.79          4.18      3.92        5.73
5.0                         3.76          4.01      3.86        6.17
6.0                         3.52          3.67      3.59        6.29
```

Persistenz = „bleibt wie jetzt“. Je kleiner, desto besser.

