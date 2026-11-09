"""Seitenansicht in Laufrichtung: Keil-Konsole, schräge Platten, Klemmbock mit waagerechter Oberseite (Steigung 5-fach überhöht)."""
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
s = 0.0317 * 5                                   # überhöht
fig, ax = plt.subplots(figsize=(10, 5))
P = lambda pts, f: ax.add_patch(Polygon(pts, closed=True, fc=f, ec="black", lw=0.8))
# Muttern + Stange
ax.add_patch(Rectangle((-3, -16), 6, 46, fc="#B8B8B8", ec="black", lw=0.8))
for z in (-11, -6): ax.add_patch(Rectangle((-5.75, z), 11.5, 5, fc="#8C8C8C", ec="black", lw=0.8))
ax.add_patch(Rectangle((-5.2, -1), 10.4, 1, fc="#C8C8C8", ec="black", lw=0.8))
# Konsole: unten waagerecht, oben schräg
P([(-20, 0), (20, 0), (20, 6 + s * 20), (-20, 6 - s * 20)], "#D85A30")
# Platten A (links) und B (rechts) – gleiche Steigung, Fuge bei y = 0
P([(-45, 6 - s * 45), (0, 6), (0, 9.9), (-45, 9.9 - s * 45)], "#9EC1E6")
P([(0, 6), (45, 6 + s * 45), (45, 9.9 + s * 45), (0, 9.9)], "#7FAEDC")
# Klemmbock (liegt eigentlich radial daneben – hier hinter der Platte angedeutet)
P([(-7, 9.9 - s * 7 + 4 - 0.2), (7, 9.9 + s * 7 + 4 - 0.2), (7, 18.3), (-7, 18.3)], "#2E6FB0")
ax.add_patch(Rectangle((-5.2, 18.3), 10.4, 0.6, fc="#C8C8C8", ec="black", lw=0.8))
ax.add_patch(Rectangle((-5.75, 18.9), 11.5, 5, fc="#8C8C8C", ec="black", lw=0.8))
ax.annotate("bergauf", (40, 22), (22, 22), arrowprops=dict(arrowstyle="->", lw=1.2), fontsize=10, va="center")
ax.text(23, 1.5, "Konsole: unten waagerecht,\noben Keil (±0,6 mm innen, ±0,5 mm außen)", fontsize=9)
ax.text(-12, 21.5, "Klemmbock: unten schräg,\noben waagerecht → Mutter liegt gerade", fontsize=9, ha="right", color="#2E6FB0")
ax.text(-44, 4.5 - s * 45 + 8, "Platte A", fontsize=9); ax.text(30, 12 + s * 30, "Platte B", fontsize=9)
ax.text(-21, -9, "Mutter + Kontermutter\nwaagerecht", fontsize=9, ha="right")
ax.text(18, -2.5, "Fase unten = Seite bergauf", fontsize=8, color="#D85A30")
ax.set_xlim(-60, 60); ax.set_ylim(-18, 30); ax.set_aspect("equal"); ax.axis("off")
ax.set_title("Blick von innen auf einen Stoß (Steigung 5-fach überhöht gezeichnet)", fontsize=11)
fig.savefig("Keil_Skizze.png", dpi=120, bbox_inches="tight", facecolor="white")
