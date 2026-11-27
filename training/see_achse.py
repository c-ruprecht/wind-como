"""Achsen des Comer Sees: jeder Wasserpixel bekommt einen Arm (oben / lecco / como) und die Strecke entlang des Arms.

Der See hat drei Arme mit eigener Richtung. Breitenstreifen taugen deshalb nur für einen Arm; für den ganzen See
wird jeder Pixel auf die nächste Mittellinie projiziert (höchstens MAX_KM daneben, sonst gehört er nicht dazu –
z. B. Lago di Garlate, Annone, Pusiano).

  zonen(H, W, bbox, water) -> arm (int, -1 = keiner), km (ab Nordende des Arms), Liste der Armnamen
  Zonen je Arm: erstes, zweites, letztes Drittel (nord / mitte / sued).
"""
import numpy as np

# Mittellinien von Nord nach Süd (Breite, Länge) – grob, für Abschnitte und Profile genügt das
ARME = {
    "oben": [(46.168, 9.395), (46.140, 9.370), (46.110, 9.330), (46.077, 9.300), (46.040, 9.275), (46.000, 9.262), (45.985, 9.262)],
    "lecco": [(45.985, 9.268), (45.957, 9.300), (45.935, 9.310), (45.918, 9.318), (45.898, 9.336), (45.875, 9.355), (45.852, 9.380)],
    "como": [(45.985, 9.255), (45.965, 9.215), (45.950, 9.180), (45.935, 9.140), (45.900, 9.125), (45.860, 9.115),
             (45.835, 9.095), (45.812, 9.080)],
}
NAMEN = {"oben": "Upper lake (Sorico–Bellagio)", "lecco": "Lecco branch (Bellagio–Lecco)", "como": "Como branch (Bellagio–Como)"}
ORTE = {"oben": (("Sorico", 46.165, 9.39), ("Colico", 46.137, 9.372), ("Domaso", 46.150, 9.335), ("Dervio", 46.077, 9.300),
                 ("Menaggio", 46.020, 9.238), ("Varenna", 46.010, 9.284)),
        "lecco": (("Lierna", 45.957, 9.305), ("Mandello", 45.918, 9.318), ("Abbadia", 45.898, 9.336), ("Parè/Valmadrera", 45.852, 9.362)),
        "como": (("Lezzeno", 45.945, 9.185), ("Argegno", 45.943, 9.127), ("Torno", 45.856, 9.118), ("Como", 45.812, 9.080))}
MAX_KM = 2.5
KX, KY = 77.3, 111.2                       # km je Grad Länge (46° N) / Breite


def _proj(px, py, line):
    """Abstand zur Polylinie und Strecke entlang ab Startpunkt (km), für Arrays px, py (km)."""
    best_d = np.full(px.shape, np.inf); best_s = np.zeros(px.shape); acc = 0.0
    for (y0, x0), (y1, x1) in zip(line[:-1], line[1:]):
        ax, ay, bx, by = x0 * KX, y0 * KY, x1 * KX, y1 * KY
        dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy; L = np.sqrt(L2)
        t = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0, 1)
        d = np.hypot(px - (ax + t * dx), py - (ay + t * dy))
        m = d < best_d
        best_d[m] = d[m]; best_s[m] = acc + t[m] * L
        acc += L
    return best_d, best_s, acc


def zonen(H, W, bbox, water):
    lon = bbox[0] + (np.arange(W) + 0.5) / W * (bbox[2] - bbox[0])
    lat = bbox[3] - (np.arange(H) + 0.5) / H * (bbox[3] - bbox[1])
    px, py = np.meshgrid(lon * KX, lat * KY)
    names = list(ARME)
    D = []; Sx = []; lens = {}
    for n in names:
        d, s_, L = _proj(px, py, ARME[n]); D.append(d); Sx.append(s_); lens[n] = L
    D = np.stack(D); Sx = np.stack(Sx)
    arm = np.argmin(D, axis=0)
    dmin = np.take_along_axis(D, arm[None], 0)[0]
    km = np.take_along_axis(Sx, arm[None], 0)[0]
    arm = np.where(water & (dmin <= MAX_KM), arm, -1)
    return arm, km, names, lens


def ort_km(name_arm, lat, lon):
    """Strecke eines Ortes entlang seines Arms (km ab Nordende)"""
    d, s_, _ = _proj(np.array([lon * KX]), np.array([lat * KY]), ARME[name_arm])
    return float(s_[0])
