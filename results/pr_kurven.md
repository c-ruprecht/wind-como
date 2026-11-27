# Precision-Recall

Out-of-fold-Vorhersagen 2024–heute mit echten Läufen. AP = Average Precision (Fläche unter der Kurve). Tabelle: größter Recall, bei dem die Präzision mindestens 60/70/80 % ist, und ab welcher (geeichten) Chance.
Nur März–Oktober.

## 7-Tage-Modell

![](pr_7tage.png)

```
praezision_ziel                0.6    0.7    0.8
schwelle wann  ap    anteil                     
14       Tag 1 0.728 0.35    0.827  0.553  0.350
         Tag 2 0.689 0.35    0.785  0.456  0.181
         Tag 3 0.695 0.35    0.734  0.523  0.156
         Tag 4 0.638 0.35    0.544  0.376  0.068
         Tag 5 0.602 0.35    0.489  0.245    NaN
         Tag 6 0.566 0.35    0.481    NaN    NaN
         Tag 7 0.572 0.35    0.397  0.249    NaN
```

## Heute-Modell

![](pr_heute.png)

```
praezision_ziel                 0.6    0.7    0.8
schwelle wann   ap    anteil                     
14       07 Uhr 0.754 0.35    0.861  0.616  0.346
         09 Uhr 0.776 0.35    0.848  0.705  0.511
         11 Uhr 0.796 0.35    0.865  0.675  0.549
         13 Uhr 0.861 0.35    0.937  0.789  0.646
         15 Uhr 0.929 0.35    0.962  0.945  0.797
lang     07 Uhr 0.561 0.17    0.383  0.313  0.104
         09 Uhr 0.610 0.17    0.583  0.304  0.183
         11 Uhr 0.619 0.17    0.548  0.400  0.139
         13 Uhr 0.726 0.17    0.800  0.670  0.322
         15 Uhr 0.814 0.17    0.887  0.800  0.687
```

