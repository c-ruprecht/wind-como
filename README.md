# Breva-Vorhersage-Archiv

Automatisch geschrieben von `tools/archiv.js` (GitHub Action „Vorhersagen archivieren“, Branch `main`).
Jeder Lauf rechnet genau, was die App in dem Moment anzeigt.

**vorhersagen.csv** – eine Zeile je Lauf × Zieltag × Schwelle
- `lauf_id`: Zeitpunkt des Archiv-Laufs (UTC)
- `art`: `7tage` (7-Tage-Modell) oder `heute` (Heute-Modell mit Messungen)
- `modell_id`: Modellart-Ziel-Schwelle-Prüfsumme (Modelldatei + Eichung); ändert sich bei jedem Neutraining
- `wettermodell`, `ecmwf_init`: Eingangsmodell und Startzeit des verwendeten Laufs (Open-Meteo)
- `app_commit`: Git-Commit des App-Codes
- `zieldatum`, `vorlauf` (Tage), `schwelle` (kn), `stunde` (Entscheidungsstunde des Heute-Modells, leer = nur Vorhersage)
- `p`: geeichte Chance (wie in der App), `p_roh`: Modellausgabe vor der Eichung
- `call_ab`: Schwelle für einen Breva-Call (≥ 80 % Präzision in der Prüfung; leer = nie erreicht), `call`: 1 = Call

**merkmale/JJJJ-MM.jsonl** – je Lauf die Eingangsgrößen (zum Nachrechnen und für Modellvergleiche)
