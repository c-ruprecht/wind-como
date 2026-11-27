# Die unsicheren Tage

7-Tage-Modell, Vorlauf 1, März–Oktober 2024–heute: 678 Tage, davon 152 mit geeichter Chance 35–65 % (66 Breva, 86 kein Breva).

auc_band: wie gut die Größe innerhalb des Bandes Breva von Nicht-Breva trennt (0,5 = gar nicht). auc_alle: dieselbe Größe über alle Tage. p: Mann-Whitney (bei ~150 Tagen und vielen Größen ist p < 0,01 ein Hinweis, kein Beweis).


## A ERA5 (Wetter wie es war)

```
               groesse im_modell   n  auc_band     richtung     p  auc_alle  median_breva  median_kein
   taupunktdiff_milano      True 152     0.612  Breva höher 0.018     0.655         10.75         9.20
        tmax_chiavenna      True 152     0.607  Breva höher 0.025     0.643         27.25        23.85
bodenfeuchte_chiavenna     False 152     0.605 Breva tiefer 0.027     0.633          0.29         0.31
               doy_cos      True 152     0.605 Breva tiefer 0.027     0.650         -0.84        -0.66
          tmax_engadin      True 152     0.601  Breva höher 0.034     0.645         16.95        13.45
           tmax_milano      True 152     0.601  Breva höher 0.033     0.641         29.50        26.65
          tmax_sondrio      True 152     0.600  Breva höher 0.035     0.637         27.05        23.90
              tmax_see     False 152     0.599  Breva höher 0.036     0.634         28.05        25.65
          tmax_bergamo      True 152     0.594  Breva höher 0.047     0.629         27.80        25.05
           tmin_milano     False 152     0.593  Breva höher 0.050     0.599         19.50        17.95
          dp_po_tal_18      True 152     0.591 Breva tiefer 0.055     0.552         -3.40        -2.80
        tmin_chiavenna      True 152     0.590  Breva höher 0.058     0.589         18.30        17.20
   bodenfeuchte_milano     False 152     0.583 Breva tiefer 0.080     0.621          0.34         0.37
          dp_po_tal_06      True 152     0.583 Breva tiefer 0.081     0.557         -3.20        -2.65
               see_t30      True 152     0.581  Breva höher 0.090     0.563         23.80        21.69
```

## B Vorhersagefehler Vortag (Lauf − ERA5)

```
                     groesse im_modell   n  auc_band     richtung     p  auc_alle  median_breva  median_kein
dp_bergamo_sondrio_15_fehler           152     0.631 Breva tiefer 0.006     0.539         -0.30         0.05
  rad_spaet_chiavenna_fehler           152     0.595  Breva höher 0.046     0.653          0.32         0.23
       tmax_chiavenna_fehler           152     0.590 Breva tiefer 0.058     0.557         -0.85        -0.35
   luft_minus_see_t30_fehler           152     0.590 Breva tiefer 0.057     0.557         -0.62        -0.17
            dt_tal_po_fehler           152     0.575 Breva tiefer 0.112     0.523          0.70         1.20
        rad_chiavenna_fehler           152     0.571  Breva höher 0.132     0.622          0.70         0.45
          geo_staerke_fehler           152     0.568  Breva höher 0.151     0.570         -0.03        -0.06
         tmax_bergamo_fehler           152     0.567  Breva höher 0.158     0.510         -1.15        -1.65
              rad_see_fehler           152     0.559  Breva höher 0.216     0.602          0.34         0.24
         regen_vortag_fehler           152     0.559  Breva höher 0.208     0.514          0.00        -0.10
         tmax_sondrio_fehler           152     0.557 Breva tiefer 0.229     0.520         -0.90        -0.55
     drucktendenz_24h_fehler           152     0.557 Breva tiefer 0.227     0.529          0.00         0.10
         geo_aus_sued_fehler           152     0.556 Breva tiefer 0.236     0.574         -0.06        -0.02
        dt_engadin_po_fehler           152     0.547 Breva tiefer 0.322     0.557         -0.10         0.50
   dp_lyon_venezia_12_fehler           152     0.543  Breva höher 0.368     0.590          0.40         0.20
```

## B' Vorhersage Vortag

```
                       groesse im_modell   n  auc_band     richtung     p  auc_alle  median_breva  median_kein
      rad_chiavenna_vorhersage           152     0.615  Breva höher 0.016     0.723          5.54         5.09
rad_spaet_chiavenna_vorhersage           152     0.614  Breva höher 0.016     0.702          1.79         1.61
            doy_cos_vorhersage           152     0.605 Breva tiefer 0.027     0.650         -0.84        -0.66
       tmax_bergamo_vorhersage           152     0.601  Breva höher 0.033     0.631         25.80        23.60
taupunktdiff_milano_vorhersage           152     0.601  Breva höher 0.033     0.669         10.10         8.70
       dp_po_tal_18_vorhersage           152     0.599 Breva tiefer 0.037     0.559         -3.25        -2.30
            rad_see_vorhersage           152     0.598  Breva höher 0.039     0.679          5.19         4.78
     tmax_chiavenna_vorhersage           152     0.596  Breva höher 0.043     0.632         26.55        24.25
        tmax_milano_vorhersage           152     0.595  Breva höher 0.045     0.637         27.60        25.15
       dp_po_tal_15_vorhersage           152     0.593 Breva tiefer 0.050     0.528         -2.45        -1.65
       dp_po_tal_06_vorhersage           152     0.592 Breva tiefer 0.053     0.561         -2.35        -1.80
       tmax_sondrio_vorhersage           152     0.592  Breva höher 0.052     0.632         26.25        24.40
       tmax_engadin_vorhersage           152     0.589  Breva höher 0.061     0.617         13.80        11.80
  wolken_morgen_see_vorhersage           152     0.587 Breva tiefer 0.065     0.604         29.58        38.50
     tmin_chiavenna_vorhersage           152     0.579  Breva höher 0.096     0.563         17.05        15.85
```

## D ARPA gemessen

```
                    groesse im_modell   n  auc_band    richtung     p  auc_alle  median_breva  median_kein
          morbegno_rad_9_17           152     0.652 Breva höher 0.001     0.745        599.15       513.55
         chiavenna_rad_9_17           152     0.652 Breva höher 0.001     0.745        599.15       513.55
            colico_rad_9_17           152     0.652 Breva höher 0.001     0.745        599.15       513.55
           sondrio_rad_9_17           152     0.650 Breva höher 0.002     0.746        618.02       517.41
            colico_temp_max           148     0.641 Breva höher 0.003     0.680         28.33        25.75
          morbegno_temp_max           148     0.641 Breva höher 0.003     0.680         28.33        25.75
dt_sondrio_bergamo_gemessen           149     0.626 Breva höher 0.008     0.683          1.19         0.20
         berg_nord_rad_9_17           151     0.621 Breva höher 0.011     0.754        547.63       493.61
           sondrio_temp_max           152     0.621 Breva höher 0.011     0.679         29.73        26.90
            milano_rad_9_17           149     0.619 Breva höher 0.013     0.702        579.19       493.24
           bergamo_rad_9_17           152     0.615 Breva höher 0.015     0.695        644.92       541.18
             lecco_rad_9_17           151     0.613 Breva höher 0.018     0.691        647.94       540.74
              como_rad_9_17           152     0.610 Breva höher 0.020     0.694        612.69       526.84
             lecco_temp_max           151     0.609 Breva höher 0.023     0.648         28.40        26.02
              como_temp_max           152     0.609 Breva höher 0.021     0.647         28.00        25.78
```

## E Ziel-Rauschen im Band

- Nicht-Breva-Tage, die knapp verpasst haben (nur 1 h ≥ 14 kn oder Maximum 12–14 kn): 45 von 86
- Nicht-Breva-Tage mit ≥ 2 h ≥ 14 kn, die nur an Morgen- oder Nordwindregel scheiterten: 1
- Breva-Tage mit genau 2 h (knapp gezählt): 19 von 66
- Mittlere Breva-Dauer im Band: 3.8 h (alle Breva-Tage: 4.8 h)
