# Analyse Breva-Modell (≥ 14 kn)

Training ERA5 2014–2023, Prüfung 2024–heute mit ECMWF-Läufen [1, 3, 5] Tage vorher. Breva-Tage im Test: 129 von 995, Satellitenabende im Test: 126 (davon Breva 19).

## 1. Leckage

```
                                      test  auc_1  saison_1  auc_3  saison_3  auc_5  saison_5  satellit_1
                   Basis (Ziel A, wie App)  0.928     0.898  0.900     0.859  0.853     0.800       0.722
a) Ziel B: nur Stationen (ohne ERA5-Regen)  0.884     0.832  0.860     0.798  0.823     0.755       0.812
             a) Ziel A ohne Regen-Merkmale  0.930     0.897  0.902     0.858  0.862     0.808       0.722
                    b) Merkmale vom Vortag  0.839     0.763  0.834     0.756  0.824     0.738       0.738
                   b) nur Jahreszeit (doy)  0.764     0.645  0.764     0.645  0.764     0.645       0.725
```

c) Kreuzvalidierung ERA5 2014–2023: zufällige Aufteilung AUC 0.951, jahresweise 0.951  (großer Abstand = benachbarte Tage verraten sich)

d) Merkmale, die nur in ERA5 trennen (Saison, Testjahre; abstand > 0,1 verdächtig):
```
              merkmal  auc_era5  auc_vorhersage_1  abstand
     wolken_chiavenna     0.363             0.418    0.055
         tmax_engadin     0.637             0.608    0.029
dp_muenchen_genova_12     0.419             0.448    0.029
       tmin_chiavenna     0.549             0.521    0.028
    wolken_morgen_see     0.357             0.385    0.028
     wind_see_15_sued     0.781             0.758    0.023
         geo_aus_west     0.630             0.607    0.023
              see_t30     0.522             0.506    0.016
  dp_zurich_milano_12     0.345             0.361    0.016
   dp_lyon_venezia_12     0.299             0.314    0.015
       tmax_chiavenna     0.636             0.623    0.013
dp_bergamo_sondrio_15     0.540             0.527    0.013
```

f) Heute-Modell: Stationen um 13 Uhr gegen Ziel A (Samolaco 11–20 Uhr) und gegen den Satelliten:
```
                merkmal  auc_ziel_A  auc_satellit
samolaco_jetzt (13 Uhr)       0.807         0.794
 vercana_jetzt (13 Uhr)       0.830         0.802
  colico_jetzt (13 Uhr)       0.755         0.793
morbegno_jetzt (13 Uhr)       0.768         0.747
```
   Liegt Samolaco gegen Ziel A deutlich höher als gegen den Satelliten, ist das Überlappung, keine Vorhersage.

## 2. Verfeinerung

```
                                                                    modell  auc_1  saison_1  auc_3  saison_3  auc_5  saison_5  satellit_1
                                            XGB Basis (250 Bäume, Tiefe 3)  0.928     0.898  0.900     0.859  0.853     0.800       0.722
                                                    Logistische Regression  0.900     0.868  0.890     0.850  0.847     0.795       0.743
                                         XGB max_depth=2, n_estimators=400  0.927     0.896  0.898     0.857  0.852     0.799       0.722
                                         XGB max_depth=4, n_estimators=200  0.930     0.900  0.900     0.860  0.853     0.803       0.718
                     XGB max_depth=3, n_estimators=600, learning_rate=0.02  0.929     0.899  0.902     0.860  0.854     0.801       0.718
                                      XGB max_depth=3, min_child_weight=15  0.927     0.897  0.901     0.861  0.855     0.804       0.740
XGB max_depth=2, n_estimators=800, learning_rate=0.02, min_child_weight=10  0.928     0.897  0.904     0.861  0.858     0.805       0.733
                    XGB max_depth=5, n_estimators=150, min_child_weight=10  0.929     0.899  0.901     0.862  0.854     0.804       0.730
```

## 3. Verkleinerung

Rangfolge (mittlerer |SHAP|): dp_zurich_milano_12 0.91, wind_see_15_sued 0.72, regen_see 0.40, regen_chiavenna 0.36, doy_sin 0.30, rad_spaet_chiavenna 0.29, wind_milano_12 0.29, dt_tal_po 0.28, doy_cos 0.27, rad_chiavenna 0.24, dp_bergamo_sondrio_15 0.23, geo_aus_sued 0.18, taupunktdiff_milano 0.17, dp_muenchen_genova_12 0.17, wolken_see 0.12
```
 merkmale  auc_1  saison_1  auc_3  saison_3  auc_5  saison_5  satellit_1
       37  0.927     0.896  0.897     0.855  0.849     0.797       0.727
       25  0.924     0.893  0.896     0.854  0.847     0.792       0.720
       20  0.925     0.895  0.898     0.856  0.844     0.790       0.716
       15  0.923     0.894  0.894     0.854  0.842     0.792       0.710
       12  0.916     0.886  0.892     0.854  0.842     0.794       0.728
       10  0.909     0.876  0.884     0.842  0.840     0.787       0.712
        8  0.908     0.873  0.885     0.842  0.840     0.784       0.733
        6  0.898     0.867  0.875     0.834  0.826     0.774       0.727
        5  0.873     0.858  0.848     0.831  0.780     0.759       0.691
        4  0.859     0.832  0.831     0.801  0.757     0.723       0.698
        3  0.858     0.829  0.825     0.794  0.765     0.727       0.695
```

Kleinstes Modell mit Saison-AUC (1 Tag) höchstens 0,005 unter dem besten: **15 Merkmale** – dp_zurich_milano_12, wind_see_15_sued, regen_see, regen_chiavenna, doy_sin, rad_spaet_chiavenna, wind_milano_12, dt_tal_po, doy_cos, rad_chiavenna, dp_bergamo_sondrio_15, geo_aus_sued, taupunktdiff_milano, dp_muenchen_genova_12, wolken_see

## 4. Lokales Wissen im Modell

```
                                             variante  auc_1  saison_1  auc_3  saison_3  auc_5  saison_5  satellit_1
                                                Basis  0.928     0.898  0.900     0.859  0.853     0.800       0.722
                 monotone Wirkungsrichtungen (Physik)  0.929     0.898  0.906     0.866  0.862     0.809       0.743
Jahreszeit als Vorwissen (Monats-Klima als Startwert)  0.924     0.891  0.902     0.858  0.854     0.797       0.736
               Saison stärker gewichtet (Winter ×0,3)  0.927     0.899  0.900     0.862  0.851     0.806       0.701
            + entsaisonalisierte Temperaturen/Gefälle  0.929     0.900  0.901     0.860  0.854     0.802       0.715
 + physikalische Kombinationen (Thermik, Föhn, Hitze)  0.924     0.894  0.890     0.849  0.836     0.785       0.726
                          alles + monoton + Vorwissen  0.922     0.889  0.897     0.855  0.844     0.787       0.753
                                 klein (15) + monoton  0.925     0.895  0.901     0.862  0.855     0.804       0.723
```

## 5. Kombinationen (Ziel A = wie bisher, Ziel B = nur Stationen)

```
ziel                          variante  auc_1  saison_1  auc_3  saison_3  auc_5  saison_5  satellit_1
   A                       37 Merkmale  0.928     0.898  0.900     0.859  0.853     0.800       0.722
   A                      37 + monoton  0.929     0.898  0.906     0.866  0.862     0.809       0.743
   A                      15 + monoton  0.925     0.895  0.901     0.862  0.855     0.804       0.723
   A 37 + monoton, min_child_weight=15  0.927     0.895  0.908     0.865  0.866     0.811       0.752
   B                       37 Merkmale  0.884     0.832  0.860     0.798  0.823     0.755       0.812
   B                      37 + monoton  0.884     0.832  0.860     0.797  0.827     0.755       0.791
   B                      15 + monoton  0.865     0.824  0.846     0.797  0.812     0.755       0.813
   B 37 + monoton, min_child_weight=15  0.882     0.829  0.860     0.799  0.831     0.762       0.809
```
Satellit-AUC Ziel A: 0.722  (90 % Bereich [0.588 0.834])
Satellit-AUC Ziel B + monoton: 0.791  (90 % Bereich [0.689 0.886])

auc_L: ganzes Jahr, L Tage vorher; saison_L: nur März–Oktober; satellit_1: gegen Breva im Satellitenbild (1 Tag vorher).

Laufzeit 15 s
