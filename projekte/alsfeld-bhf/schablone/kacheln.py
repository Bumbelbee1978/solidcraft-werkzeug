"""Bohrschablone 1:1 für die Wendel (70 × 70 cm) als A4-Kacheln + Übersicht."""
import math, json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from daten import stangen, R_I, R_A

plt.rcParams["font.family"] = "DejaVu Sans"
MM = 1 / 25.4
B, H = 190.0, 277.0          # Kachelinhalt (A4 hochkant, 10 mm Rand)
UEB = 10.0                   # Überlappung
SP, ZE = 4, 3                # Spalten, Zeilen
ROT, BLAU, GRAU = "#C0392B", "#1F5FA8", "#9A9A9A"


def fmt(h):
    return f"{h:.1f}".replace(".", ",")


def zeichnen(ax, gross=True):
    """Schablone in Weltkoordinaten (mm, Wendelmitte = 0/0, +y = Norden)."""
    ax.add_patch(Rectangle((-350, -350), 700, 700, fc="none", ec="black", lw=1.2))
    if gross:
        for v in range(-350, 351, 50):
            ax.plot([v, v], [-350, 350], color="#E6E6E6", lw=0.4, zorder=0)
            ax.plot([-350, 350], [v, v], color="#E6E6E6", lw=0.4, zorder=0)
            ax.text(v + 1, -348, str(v), fontsize=5, color="#BBBBBB")
            ax.text(-348, v + 1, str(v), fontsize=5, color="#BBBBBB")
    for r, ls, c in ((250, "-", "#7FAEDC"), (350, "-", "#7FAEDC"), (280, "--", "#1D9E75"), (320, "--", ROT)):
        ax.add_patch(Circle((0, 0), r, fc="none", ec=c, lw=0.6, ls=ls))
    for k in range(12):
        w = math.radians(90 + 30 * k)
        ax.plot([250 * math.cos(w), 350 * math.cos(w)], [250 * math.sin(w), 350 * math.sin(w)], color="#7FAEDC", lw=0.4)
    # Mitte
    ax.plot([-15, 15], [0, 0], color="black", lw=0.6); ax.plot([0, 0], [-15, 15], color="black", lw=0.6)
    ax.text(3, 3, "Wendelmitte", fontsize=7 if gross else 5)
    # Himmelsrichtungen
    fs = 11 if gross else 7
    ax.text(0, 330, "NORDEN (Wand) – Ein-/Ausfahrt unten", ha="center", fontsize=fs, weight="bold")
    ax.text(0, -338, "SÜDEN – Ausfahrt oben", ha="center", fontsize=fs, weight="bold")
    ax.text(338, -60, "OSTEN – Grundplatte", rotation=90, va="center", fontsize=fs, weight="bold")
    ax.text(-342, 60, "WESTEN – vorn", rotation=90, va="center", fontsize=fs, weight="bold")
    # Stangen
    for s in stangen():
        x, y = s["x"], s["y"]
        ax.add_patch(Circle((x, y), 3.25, fc="none", ec="black", lw=0.8))
        ax.plot([x - 8, x + 8], [y, y], color="black", lw=0.5); ax.plot([x, x], [y - 8, y + 8], color="black", lw=0.5)
        if not gross:
            ax.text(x, y + 9, s["name"], ha="center", fontsize=5, color=BLAU)
            continue
        w = math.atan2(y, x)
        rt = 168 if s["seite"] == "I" else 296
        if s["name"] == "A11":
            rt = 296
        tx, ty = rt * math.cos(w), rt * math.sin(w)
        zeilen = [f"{s['name']}   Ø 6,5"]
        for m, art, h in s["eintraege"]:
            if h is None:
                zeilen.append(f"St.{m:>2}: {art}")
            else:
                zeilen.append(f"St.{m:>2}: {fmt(h)} mm  Ist: ____")
        if s["name"] == "A11":
            zeilen[0] += "  (Sonderkonsole)"
        ax.text(tx, ty, "\n".join(zeilen), ha="center", va="center", fontsize=6.2, family="DejaVu Sans Mono",
                color=BLAU, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=BLAU, lw=0.5), zorder=6)
        ax.plot([x, tx], [y, ty], color=BLAU, lw=0.4, zorder=5)


def kachel(c, r):
    x0, yt = -350 + c * (B - UEB), 350 - r * (H - UEB)
    fig = plt.figure(figsize=(B * MM, H * MM), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(x0, x0 + B); ax.set_ylim(yt - H, yt); ax.axis("off")
    zeichnen(ax)
    name = f"{'ABCD'[c]}{r + 1}"
    hin = []
    if c > 0:
        ax.plot([x0 + UEB] * 2, [yt - H, yt], color=GRAU, lw=0.8, ls=(0, (4, 3)))
        ax.add_patch(Rectangle((x0, yt - H), UEB, H, fc="#F2F2F2", ec="none", zorder=0))
        hin.append(f"links abschneiden, auf {'ABCD'[c-1]}{r+1} kleben")
    if r > 0:
        ax.plot([x0, x0 + B], [yt - UEB] * 2, color=GRAU, lw=0.8, ls=(0, (4, 3)))
        ax.add_patch(Rectangle((x0, yt - UEB), B, UEB, fc="#F2F2F2", ec="none", zorder=0))
        hin.append(f"oben abschneiden, auf {'ABCD'[c]}{r} kleben")
    ax.text(x0 + B - 3, yt - H + 3, f"Blatt {name}" + ("  ·  " + "  ·  ".join(hin) if hin else ""), ha="right", va="bottom",
            fontsize=6.5, color="#777777", zorder=9)
    # Prüfmaß 100 mm – nur in der untersten Reihe, dort ist unter dem Brett freie Fläche
    if r == ZE - 1:
        px, py = x0 + UEB + 15, -400
        ax.plot([px, px + 100], [py, py], color="black", lw=1.0)
        for v in (px, px + 100):
            ax.plot([v, v], [py - 3, py + 3], color="black", lw=1.0)
        ax.text(px + 50, py + 4, "Prüfmaß: muss genau 100 mm messen", ha="center", fontsize=8)
    fig.savefig(f"kachel_{name}.png", dpi=300, facecolor="white"); plt.close(fig)
    return name


def uebersicht():
    fig, ax = plt.subplots(figsize=(7, 7)); ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-360, 360); ax.set_ylim(-360, 360)
    zeichnen(ax, gross=False)
    for c in range(SP):
        for r in range(ZE):
            x0, yt = -350 + c * (B - UEB), 350 - r * (H - UEB)
            ax.add_patch(Rectangle((x0, yt - H), B, H, fc="none", ec="#E67E22", lw=0.8, ls="--"))
            ax.text(x0 + 6, yt - 14, f"{'ABCD'[c]}{r + 1}", color="#E67E22", fontsize=10, weight="bold")
    fig.savefig("uebersicht.png", dpi=200, bbox_inches="tight", facecolor="white"); plt.close(fig)


if __name__ == "__main__":
    namen = [kachel(c, r) for r in range(ZE) for c in range(SP)]
    uebersicht()
    json.dump(namen, open("kacheln.json", "w"))
    print(namen)
