# Satellitenprüfung: Fehlalarme und verpasste Tage

Satellitenfaktoren aus 121 sauberen Breva-Abenden: Samolaco × 1.41, Colico × 2.66.

## Fehlalarme (Modell ja, Ziel nein): 35

```
                      faelle  modell_p  satellit_kn  foehnindex  regen
ursache                                                               
ziel_verpasst_kurz        10      0.68        16.21       -0.55   0.05
nordwind                   7      0.68         9.43        4.00   0.80
grenzfall_10_14            6      0.82        12.42       -0.10   0.85
ziel_verpasst_knapp        4      0.68        16.72       -0.15   0.20
ziel_verpasst_morgen       3      0.74        17.54        2.80   1.20
breva_frueh_vorbei         2      0.65         8.63        2.45   6.35
echt_falsch                1      0.64         5.64       -1.90   4.50
gewitter                   1      0.51        31.05        3.20   3.50
ziel_verpasst_sonst        1      0.55        17.98        3.20   9.80
```

## Verpasste Tage (Modell nein, Ziel ja): 17

```
                     faelle  modell_p  satellit_kn  foehnindex  regen
ursache                                                              
satellit_bestaetigt       9      0.14        12.98         5.1    0.9
abends_vorbei             8      0.11         8.38         3.7    6.1
```

## Ziel-Varianten gegen den Satelliten (361 Abende März–Oktober)

Satellit-Breva = Abendbild aus Süd mit ≥ 14 kn auf dem oberen See. Das Bild entsteht gegen 19:15 – ein Breva, der früher abflaut, fehlt dort; ein perfektes Ziel erreicht deshalb keine 100 %.

```
                           ziel  breva_tage  satellit_breva  uebereinstimmung  praezision  recall  kappa
                     B (bisher)         109             108             0.748       0.578   0.583  0.400
                       B_morgen         118             108             0.751       0.576   0.630  0.421
B_zwei (Mittel Samolaco+Colico)          81             108             0.781       0.679   0.509  0.438
  B_eine (Samolaco oder Colico)         145             108             0.748       0.559   0.750  0.453
```

Kontrolle: Nachbau von B stimmt an 95% der Abende mit dem gespeicherten Ziel überein.

