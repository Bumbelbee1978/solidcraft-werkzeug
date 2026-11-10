"""Titelbild für MakerWorld: kompletter Wendel (42 Platten, Stangen, Brett) als 3D-Ansicht."""
import math, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
sys.path.insert(0, "/home/claude/heimanlage/druck"); sys.path.insert(0, "/home/claude/heimanlage/schablone")
import testsatz as t
from daten import stangen


def z_unter(tp):
    """Unterkante der Platte bei Winkel tp (Grad ab Einfahrt unten)."""
    if tp <= 30: return 2.125 * tp / 30
    if tp >= 1230: return 172.125 + 2.125 * (tp - 1230) / 30
    return 2.125 + (tp - 30) / 30 * 4.25


p0, d = t.lesen("HA_01_Wendelplatte_v2.3mf")["Wendelplatte"]
a0 = np.degrees(np.arctan2(p0[:, 1], p0[:, 0]))
licht = np.array([0.4, -0.5, 0.8]); licht /= np.linalg.norm(licht)
polys, farben = [], []
for m in range(42):
    w = math.radians(90 + 30 * m)
    c, s = math.cos(w), math.sin(w)
    p = p0 @ np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
    p[:, 2] += np.array([z_unter(30 * m + a) for a in a0]) * 1.0
    tri = p[d]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n /= np.linalg.norm(n, axis=1)[:, None] + 1e-9
    hell = 0.55 + 0.45 * np.abs(n @ licht)
    polys.append(tri); farben.append(np.c_[0.62 * hell, 0.78 * hell, 0.92 * hell, np.full(len(hell), 0.95)])
# Brett und Stangen in dieselbe Sammlung, damit die Tiefensortierung stimmt
brett = np.array([[(-350, -350, -0.5), (350, -350, -0.5), (350, 350, -0.5)], [(-350, -350, -0.5), (350, 350, -0.5), (-350, 350, -0.5)]])
polys.append(brett); farben.append(np.array([[0.85, 0.78, 0.66, 1]] * 2))
for s_ in stangen():
    oben = max([h for _, _, h in s_["eintraege"] if h is not None] + [20]) + 22
    x, y = s_["x"], s_["y"]
    for k in range(6):
        w1, w2 = 2 * math.pi * k / 6, 2 * math.pi * (k + 1) / 6
        a1 = (x + 3 * math.cos(w1), y + 3 * math.sin(w1)); a2 = (x + 3 * math.cos(w2), y + 3 * math.sin(w2))
        q = np.array([[(*a1, 0), (*a2, 0), (*a2, oben)], [(*a1, 0), (*a2, oben), (*a1, oben)]])
        polys.append(q); farben.append(np.array([[0.35, 0.35, 0.38, 1]] * 2))
polys = np.concatenate(polys); farben = np.concatenate(farben)
fig = plt.figure(figsize=(10, 8), dpi=140); ax = fig.add_subplot(111, projection="3d")
ax.add_collection3d(Poly3DCollection(polys, facecolors=farben, edgecolors="none"))
ax.set_xlim(-360, 360); ax.set_ylim(-360, 360); ax.set_zlim(0, 220)
ax.set_box_aspect((720, 720, 220*1.6)); ax.view_init(elev=24, azim=-58); ax.axis("off")
fig.text(0.5, 0.92, "Zweigleisiger Spur-N-Wendel · R 280 / R 320 · 3½ Windungen · 174 mm Höhe",
         ha="center", fontsize=13, weight="bold")
fig.text(0.5, 0.06, "Höhe zur Verdeutlichung 1,6-fach überhöht dargestellt", ha="center", fontsize=9, color="#666666")
fig.savefig("Titelbild_Wendel.png", bbox_inches="tight", facecolor="white")
