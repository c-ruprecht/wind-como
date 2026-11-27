"""Explanation map "How the Breva forms" -> app/img/breva_karte.svg (English labels)


Schematisch, aber geografisch richtig platziert (Seen: Natural Earth 10 m, design/karte/seen.json).
Zahlen in den Beschriftungen aus results/breva_faktoren_14.txt (ERA5, Schönwettertage) und results/breva_merkmale.txt.
  python design/karte/breva_karte.py
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "app", "img", "breva_karte.svg")
LO0, LO1, LA0, LA1 = 8.55, 10.45, 45.28, 46.62
W = 680
K = math.cos(math.radians(46))
H = round(W * (LA1 - LA0) / ((LO1 - LO0) * K))


def xy(lo, la):
    return (lo - LO0) / (LO1 - LO0) * W, (LA1 - la) / (LA1 - LA0) * H


def path(pts, close=True):
    s = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in (xy(*p) for p in pts))
    return s + ("Z" if close else "")


def smooth(pts):
    """Catmull-Rom durch Punkte (lon, lat) als SVG-Pfad"""
    P = [xy(*p) for p in pts]
    P = [P[0]] + P + [P[-1]]
    d = f"M{P[1][0]:.1f},{P[1][1]:.1f}"
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


seen = json.load(open(os.path.join(HERE, "seen.json")))
# Rand der Alpen/Voralpen (grob, von West nach Ost) – südlich davon Po-Ebene
RAND = [(8.55, 45.72), (8.75, 45.78), (8.95, 45.80), (9.08, 45.79), (9.25, 45.78), (9.42, 45.80), (9.58, 45.74),
        (9.72, 45.70), (9.95, 45.66), (10.2, 45.60), (10.45, 45.55)]
ALPENKAMM = [(8.55, 46.50), (8.9, 46.48), (9.18, 46.47), (9.33, 46.50), (9.55, 46.42), (9.75, 46.40), (10.0, 46.40),
             (10.25, 46.45), (10.45, 46.52)]
# Talböden (Valchiavenna, Veltlin) als breite Bänder
VALCH = [(9.39, 46.16), (9.40, 46.22), (9.42, 46.28), (9.40, 46.32), (9.35, 46.40), (9.33, 46.47)]
VELT = [(9.38, 46.15), (9.48, 46.15), (9.57, 46.14), (9.70, 46.15), (9.87, 46.17), (10.02, 46.18), (10.17, 46.22), (10.30, 46.27)]
# Breva-Strömung
FLOW_PO = [(9.22, 45.50), (9.30, 45.62), (9.37, 45.74), (9.38, 45.82)]
FLOW_PO2 = [(9.16, 45.50), (9.12, 45.62), (9.09, 45.74), (9.10, 45.82)]
FLOW_COMO = [(9.10, 45.84), (9.12, 45.90), (9.17, 45.95), (9.24, 45.98)]
FLOW_SEE = [(9.38, 45.86), (9.33, 45.93), (9.27, 46.00), (9.27, 46.06), (9.31, 46.11), (9.355, 46.15)]
FLOW_CH = [(9.37, 46.17), (9.40, 46.24), (9.41, 46.30), (9.39, 46.36)]
FLOW_VE = [(9.40, 46.15), (9.52, 46.15), (9.66, 46.15), (9.82, 46.17)]
ORTE = {"Milan": (9.19, 45.46, "se"), "Bergamo": (9.67, 45.70, "se"), "Como": (9.08, 45.81, "w"),
        "Lecco": (9.39, 45.85, "e"), "Dervio": (9.30, 46.08, "w"), "Colico": (9.37, 46.135, "e"),
        "Chiavenna": (9.40, 46.32, "e"), "Morbegno": (9.57, 46.135, "s"), "Sondrio": (9.87, 46.17, "s"),
        "Zurich ↑": (9.05, 46.60, "e")}

o = []
o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="system-ui,-apple-system,Segoe UI,Roboto,sans-serif" font-size="13">')
o.append("""<defs>
<marker id="ah" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="16" markerHeight="16" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#0b6e8a"/></marker>
<marker id="ahg" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="14" markerHeight="14" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#8a8f96"/></marker>
<pattern id="berg" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(35)"><line x1="0" y1="0" x2="0" y2="8" stroke="#c9d3cc" stroke-width="2"/></pattern>
<radialGradient id="tief" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#f08a3c" stop-opacity=".55"/><stop offset="1" stop-color="#f08a3c" stop-opacity="0"/></radialGradient>
<radialGradient id="hoch" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#e9c46a" stop-opacity=".55"/><stop offset="1" stop-color="#e9c46a" stop-opacity="0"/></radialGradient>
</defs>""")
o.append(f'<rect width="{W}" height="{H}" fill="#eef2ee"/>')
# Berge (nördlich des Randes) und Ebene
po = RAND + [(LO1, LA0), (LO0, LA0)]
o.append(f'<path d="{path(po)}" fill="#f5e7c8"/>')
o.append(f'<path d="{path(RAND + [(LO1, LA1), (LO0, LA1)])}" fill="url(#berg)"/>')
o.append(f'<path d="{smooth(RAND)}" fill="none" stroke="#b9a77d" stroke-width="1.2" stroke-dasharray="4 3"/>')
o.append(f'<path d="{smooth(ALPENKAMM)}" fill="none" stroke="#7d8a82" stroke-width="2" stroke-dasharray="7 4"/>')
# warme Täler + Hitzetief
for v in (VALCH, VELT):
    o.append(f'<path d="{smooth(v)}" fill="none" stroke="#f4b183" stroke-width="22" stroke-linecap="round" stroke-opacity=".75"/>')
tx, ty = xy(9.62, 46.24)
o.append(f'<ellipse cx="{tx:.0f}" cy="{ty:.0f}" rx="170" ry="95" fill="url(#tief)"/>')
hx, hy = xy(9.45, 45.43)
o.append(f'<ellipse cx="{hx:.0f}" cy="{hy:.0f}" rx="230" ry="110" fill="url(#hoch)"/>')
o.append(f'<text x="{hx:.0f}" y="{hy + 10:.0f}" text-anchor="middle" font-size="40" font-weight="800" fill="#b8913a" fill-opacity=".85">H</text>')
o.append(f'<text x="{tx + 40:.0f}" y="{ty + 2:.0f}" text-anchor="middle" font-size="40" font-weight="800" fill="#c2551c" fill-opacity=".85">L</text>')
# Isobaren (schematisch): Druck sinkt von der Ebene in die Täler
for k, la in enumerate((45.70, 45.92, 46.10)):
    pts = [(LO0, la - 0.04), (9.0, la), (9.35, la + 0.02 + 0.03 * k), (9.8, la + 0.01), (LO1, la - 0.05)]
    o.append(f'<path d="{smooth(pts)}" fill="none" stroke="#8a6d3b" stroke-width="1" stroke-opacity=".55" stroke-dasharray="2 4"/>')
# Seen
for name, rings in seen.items():
    for r in rings:
        o.append(f'<path d="{path(r)}" fill="#9fcde3" stroke="#5d9fbf" stroke-width=".8"/>')
# Strömung
for f in (FLOW_PO, FLOW_PO2):
    o.append(f'<path d="{smooth(f)}" fill="none" stroke="#0b6e8a" stroke-width="4" stroke-opacity=".6" stroke-linecap="round" stroke-dasharray="1 8"/>')
o.append(f'<path d="{smooth(FLOW_COMO)}" fill="none" stroke="#0b6e8a" stroke-width="3" stroke-opacity=".85" stroke-linecap="round"/>')
for f, w in ((FLOW_SEE, 6), (FLOW_CH, 4), (FLOW_VE, 4)):
    o.append(f'<path d="{smooth(f)}" fill="none" stroke="#ffffff" stroke-width="{w + 4}" stroke-opacity=".8" stroke-linecap="round"/>')
o.append(f'<path d="{smooth(FLOW_SEE)}" fill="none" stroke="#0b6e8a" stroke-width="6" stroke-linecap="round" marker-end="url(#ah)"/>')
o.append(f'<path d="{smooth(FLOW_CH)}" fill="none" stroke="#0b6e8a" stroke-width="4" stroke-linecap="round" marker-end="url(#ah)"/>')
o.append(f'<path d="{smooth(FLOW_VE)}" fill="none" stroke="#0b6e8a" stroke-width="4" stroke-linecap="round" marker-end="url(#ah)"/>')
# Nordföhn-Pfeil (Störer)
o.append(f'<path d="{smooth([(9.05, 46.62), (9.10, 46.50), (9.15, 46.38)])}" fill="none" stroke="#8a8f96" stroke-width="4" stroke-linecap="round" marker-end="url(#ahg)"/>')
# Orte
for n, (lo, la, pos) in ORTE.items():
    x, y = xy(lo, la)
    if not n.startswith("Zurich"):
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="#1d2a33"/>')
    dx, dy, anc = {"e": (7, 4, "start"), "w": (-7, 4, "end"), "s": (0, 17, "middle"), "se": (6, 15, "start")}[pos]
    o.append(f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" text-anchor="{anc}" fill="#1d2a33" paint-order="stroke" stroke="#eef2ee" stroke-width="3">{n}</text>')


def label(lo, la, lines, color="#1d2a33", weight="600", anchor="start", size=13):
    x, y = xy(lo, la)
    t = f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" fill="{color}" font-size="{size}" paint-order="stroke" stroke="#eef2ee" stroke-width="3.5">'
    for i, l in enumerate(lines):
        t += f'<tspan x="{x:.1f}" dy="{0 if i == 0 else 1.25}em" font-weight="{weight if i == 0 else 400}">{l}</tspan>'
    return t + "</text>"


o.append(label(8.62, 45.40, ["PO PLAIN", "heats up more slowly –", "relatively higher pressure (H)"], "#8a6d3b"))
o.append(label(9.80, 46.36, ["HEAT LOW IN THE VALLEYS (L)", "Valchiavenna and Valtellina heat", "up more strongly than the plain"], "#b5541c"))
o.append(label(9.47, 45.97, ["BREVA", "air flows from the plain", "over the lake into the valleys", "≈ 12–20:00, peak 15–17:00"], "#0b6e8a"))
o.append(label(8.60, 45.66, ["PRESSURE GRADIENT plain → valley", "Milan–Chiavenna on Breva days", "≈ 0.7 hPa stronger, grows", "from morning to afternoon"], "#8a6d3b", size=12))
o.append(label(9.18, 46.40, ["NORTH FOEHN disrupts:", "Zurich–Milan ≥ 4 hPa"], "#6b7177", size=12))
o.append(label(9.55, 46.58, ["Main Alpine ridge"], "#5f6b64", "400", size=11))
o.append(label(9.75, 45.63, ["Edge of the Prealps"], "#8a7a55", "400", size=11))
o.append("</svg>")
open(OUT, "w").write("\n".join(o))
print("geschrieben:", os.path.relpath(OUT), f"{W}×{H}")
