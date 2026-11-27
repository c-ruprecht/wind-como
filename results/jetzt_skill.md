# Same-Day-Modell, stündlich

Prüfung 2024–2026 je Jahr out-of-fold; Vorhersage-Teil aus ecmwf_ifs00z (Vorlauf 0). Stufen: V nur Vorhersage, W + gemessener Wind, A + ARPA-Treiber.


## Kommt nach dieser Stunde noch ≥ 14 kn (≥ 2 h)? – AUC März–Oktober

```
stufe   A + ARPA-Treiber  V Vorhersage  W + Wind
stunde                                          
8.0                0.839         0.833     0.837
9.0                0.848         0.833     0.840
10.0               0.856         0.837     0.842
11.0               0.866         0.838     0.853
12.0               0.883         0.842     0.873
13.0               0.899         0.843     0.895
14.0               0.915         0.846     0.906
15.0               0.917         0.845     0.909
16.0               0.935         0.864     0.928
17.0               0.941         0.853     0.931
```

## Kommt nach dieser Stunde noch ≥ 18 kn (≥ 2 h)? – AUC März–Oktober

```
stufe   A + ARPA-Treiber  V Vorhersage  W + Wind
stunde                                          
8.0                0.771         0.729     0.743
9.0                0.779         0.729     0.743
10.0               0.783         0.729     0.752
11.0               0.786         0.730     0.761
12.0               0.801         0.733     0.781
13.0               0.816         0.730     0.803
14.0               0.852         0.734     0.838
15.0               0.862         0.738     0.858
16.0               0.921         0.779     0.910
17.0               0.907         0.799     0.895
```

## Wind auf dem See in k Stunden – mittlerer Fehler (kn), März–Oktober, 9–16 Uhr

```
stufe           A + ARPA-Treiber  V Vorhersage  W + Wind  Persistenz
stunden_voraus                                                      
1.0                         2.19          3.76      2.26        2.38
2.0                         3.19          4.06      3.34        3.92
3.0                         3.64          4.25      3.78        5.01
4.0                         3.82          4.24      3.97        5.75
5.0                         3.79          4.07      3.88        6.21
6.0                         3.59          3.73      3.65        6.33
```

Persistenz = „bleibt wie jetzt“. Je kleiner, desto besser.

