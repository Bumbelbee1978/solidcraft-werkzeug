"""
Bildanleitung für den Zusammenbau des beweglichen Aufzugs.
Baut für jeden Schritt eine vereinfachte 3D-Szene in SolidCraft (Grundkörper) und rendert sie;
das jeweils neue Teil ist farbig, der Rest blass. Dazu zwei 2D-Skizzen (Falten, Hebel).
Koordinaten: z = 0 ist die Bahnsteig-Oberkante, Schacht außen x 0–25, y 0–14.
"""
import json
import math
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch, Circle
from PIL import Image, ImageDraw, ImageFont

CLI = "/home/claude/bin/solidcraft-cli"
AUS = Path("/home/claude/heimanlage/abb/aufzug")
AUS.mkdir(parents=True, exist_ok=True)
SCHRIFT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def box(name, x, y, z, l, b, h):
    return {"command": "solid.box", "params": {"length": l, "width": b, "height": h, "corner": [x, y, z],
                                               "operation": "new", "body_name": name, "name": name}}


def zyl(name, x, y, z, d, h, achse="Z"):
    return {"command": "solid.cylinder", "params": {"diameter": d, "height": h, "base": [x, y, z], "axis": achse,
                                                    "operation": "new", "body_name": name, "name": name}}


# ---------- die Bauteile der Szene ----------
def schacht():
    """Glasschacht als dünnwandiger Kasten (vereinfacht)."""
    return [box("Schacht", 0, 0, 0, 25, 14, 42),
            {"command": "solid.box", "params": {"length": 23, "width": 12, "height": 44, "corner": [1, 1, -1],
                                                "operation": "cut", "targets": ["Schacht"]}}]


def boden():
    return [box("Boden", 1, 1, 0, 23, 12, 1.5)]


def roehrchen():
    return [zyl("Roehrchen", 12.5, 7, -40, 1.5, 80)]


def draehte():
    return [zyl("Draht1", 4.3, 7, 0, 0.5, 40), zyl("Draht2", 20.7, 7, 0, 0.5, 40)]


def kabinen(oben_links=True):
    zl, zr = (22.0, 1.5) if oben_links else (1.5, 22.0)
    return [box("Kabine1", 2.8, 2, zl, 9.5, 10, 14), box("Kabine2", 12.7, 2, zr, 9.5, 10, 14)]


def kopf():
    return [box("Kopfstueck", 1, 1, 38, 23, 12, 4)]


def faeden(oben_links=True):
    zl, zr = (22.0 + 14, 1.5 + 14) if oben_links else (1.5 + 14, 22.0 + 14)
    return [zyl("Faden1", 7.55, 7, zl, 0.35, 42 - zl + 0.6), zyl("Faden2", 17.45, 7, zr, 0.35, 42 - zr + 0.6),
            {"command": "solid.cylinder", "params": {"diameter": 0.35, "height": 9.9, "base": [7.55, 7, 42.3],
                                                     "axis": "X", "operation": "new", "body_name": "Faden3"}}]


def platte():
    """Bahnsteig, Kork und obere Grundplatte als Schnittstück."""
    return [box("Bahnsteig", -12, -10, -7.3, 50, 34, 7.3), box("Kork", -12, -10, -9.3, 50, 34, 2),
            box("Grundplatte", -12, -10, -28.3, 50, 34, 19)]


def servo():
    """Halter (Flansch + Platte), Servo, Hebel, Fäden zu den Hebelenden."""
    zf = -28.3
    return [box("Flansch", 0, 3, zf - 3, 50 - 25, 22, 3),
            box("Halterplatte", 0, 0, zf - 48, 25, 3, 48),
            box("Servo", 6, -12, zf - 40, 22.8, 12.2, 22.7),
            box("Hebel", -7.5, 6, zf - 30, 40, 2, 5),
            zyl("Faden4", -3.5, 7, zf - 28, 0.35, 28 - 0.5),
            zyl("Faden5", 28.5, 7, zf - 28, 0.35, 28 - 0.5)]


FARBEN = {
    "Schacht": "#85B7EB", "Boden": "#888780", "Roehrchen": "#BA7517", "Draht1": "#EF9F27", "Draht2": "#EF9F27",
    "Kabine1": "#D85A30", "Kabine2": "#D85A30", "Kopfstueck": "#5F5E5A",
    "Faden1": "#000000", "Faden2": "#000000", "Faden3": "#000000", "Faden4": "#000000", "Faden5": "#000000",
    "Bahnsteig": "#B4B2A9", "Kork": "#C9A66B", "Grundplatte": "#E8D5B0",
    "Flansch": "#1D9E75", "Halterplatte": "#1D9E75", "Servo": "#185FA5", "Hebel": "#7F77DD",
}


def koerper_namen(befehle):
    return [c["params"].get("body_name") for c in befehle if c["params"].get("body_name")]


def rendern(name, alt, neu, kamera, blass=0.18, glas=0.25):
    """Szene aus bisherigen (blass) und neuen (kräftig) Teilen rendern."""
    befehle = alt + neu
    skript = AUS / f"{name}.json"
    json.dump({"commands": befehle}, open(skript, "w"), indent=1)
    neue = set(koerper_namen(neu))
    args = [CLI, "snapshot", str(skript), "--out", str(AUS / f"{name}_roh.png"), "--width", "1100", "--height", "900",
            "--no-grid", "--camera", json.dumps(kamera), "--quality", "fine"]
    for k in koerper_namen(befehle):
        deck = 1.0 if k in neue else blass
        if k == "Schacht":
            deck = glas if k not in neue else 0.35
        args += ["--body", f"{k}:opacity={deck},color={FARBEN.get(k, '#888780')}"]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode:
        print(name, r.stderr[:300])


def beschriften(name, nummer, titel, zeilen):
    """Schrittnummer, Titel und Stichpunkte unter das Bild setzen."""
    bild = Image.open(AUS / f"{name}_roh.png").convert("RGB")
    if bild.width != 1100:   # alle Schritte gleich breit
        bild = bild.resize((1100, int(bild.height * 1100 / bild.width)))
    w, h = bild.size
    # Platz oben für die Überschrift schaffen
    oben = Image.new("RGB", (w, h + 110), "white")
    oben.paste(bild, (0, 110))
    bild = oben
    w, h = bild.size
    neu = Image.new("RGB", (w, h + 60 + 34 * len(zeilen)), "white")
    neu.paste(bild, (0, 0))
    d = ImageDraw.Draw(neu)
    gross = ImageFont.truetype(SCHRIFT, 40)
    mittel = ImageFont.truetype(SCHRIFT, 30)
    normal = ImageFont.truetype(SCHRIFT.replace("-Bold", ""), 27)
    d.ellipse([20, 20, 90, 90], fill="#D85A30")
    d.text((55, 55), str(nummer), fill="white", font=gross, anchor="mm")
    d.text((110, 38), titel, fill="black", font=mittel)
    for i, z in enumerate(zeilen):
        d.text((30, h + 15 + i * 34), "• " + z, fill="black", font=normal)
    neu.save(AUS / f"{name}.png")


def kamera(ziel, yaw, pitch, abstand):
    return {"target": ziel, "yaw": yaw, "pitch": pitch, "distance": abstand}


K_SCHACHT = kamera([12.5, 7, 20], math.radians(-35), math.radians(22), 120)
K_GESAMT = kamera([12.5, 7, -10], math.radians(-35), math.radians(18), 190)


def schritte():
    s = []
    s.append(("a2", schacht() + boden(), [], K_SCHACHT))
    rendern("schritt2", schacht(), boden(), K_SCHACHT)
    beschriften("schritt2", 2, "Boden einkleben", ["Schacht ist gefaltet, Folie sitzt innen", "Bodenplatte unten bündig einkleben"])
    alt = schacht() + boden()
    rendern("schritt3", alt, roehrchen() + draehte(), kamera([12.5, 7, 5], math.radians(-35), math.radians(20), 130))
    beschriften("schritt3", 3, "Röhrchen und Führungsdrähte",
                ["Ø 1,6 mm durch Bahnsteig, Kork und Platte bohren", "Röhrchen Ø 1,5 durchstecken, unten ca. 10 mm Überstand",
                 "zwei Drähte Ø 0,5 in die Bodenplatte stecken"])
    alt += roehrchen() + draehte()
    rendern("schritt4", alt, kabinen(), K_SCHACHT)
    beschriften("schritt4", 4, "Kabinen einsetzen",
                ["Ballast in den Kabinenboden kleben (0,5–1 g)", "Faden durch die Dachöse, innen verknoten",
                 "Kerben umgreifen das Röhrchen, Loch außen auf den Draht"])
    alt += kabinen()
    rendern("schritt5", alt, kopf() + faeden(), K_SCHACHT)
    beschriften("schritt5", 5, "Kopfstück und Fäden",
                ["Fäden durch die äußeren Löcher nach oben", "oben in der Rille zur Mitte, durchs Mittelloch ins Röhrchen",
                 "Kopfstück aufstecken und einkleben"])
    alt += kopf() + faeden()
    rendern("schritt6", alt + platte(), servo(), kamera([12.5, 0, -25], math.radians(145), math.radians(12), 150), blass=0.22)
    beschriften("schritt6", 6, "Servo unter die Platte",
                ["Halter unter die obere Platte schrauben, Röhrchen durchs Fenster", "Servo einsetzen, Hebel waagrecht aufkleben",
                 "Kabinen auf halbe Höhe, Fäden straff an die Hebelenden"])


# ---------- 2D-Skizzen ----------
def skizze_falten():
    """Schritt 1: Folie einlegen und Schacht falten (Draufsicht von oben auf die Kante)."""
    fig, axs = plt.subplots(3, 1, figsize=(10, 9), gridspec_kw={"height_ratios": [1, 1.4, 1.4]})
    # a) flach mit V-Nuten
    ax = axs[0]
    ax.set_title("a) flach gedruckt – Innenseite oben", fontsize=14)
    x = 0
    for w in (25, 14, 25, 14):
        ax.add_patch(Rectangle((x, 0), w, 1.0, fc="#85B7EB", ec="#185FA5", lw=0.8))
        x += w
    for xm in (25, 39, 64):
        ax.add_patch(Polygon([[xm - 0.7, 1.0], [xm + 0.7, 1.0], [xm, 0.3]], fc="white", ec="#185FA5", lw=0.8))
    ax.add_patch(Rectangle((0.8, 0.75), 23.4, 0.25, fc="#FAC775", ec="none"))
    ax.annotate("Folie in die Tasche", xy=(12, 1.0), xytext=(4, 3.2), fontsize=12, arrowprops=dict(arrowstyle="->"))
    ax.annotate("V-Nut: knicken", xy=(39, 0.6), xytext=(44, 3.2), fontsize=12, arrowprops=dict(arrowstyle="->"))
    ax.set_xlim(-2, 80); ax.set_ylim(-1, 4.5); ax.set_aspect("equal"); ax.axis("off")
    # b) halb gefaltet
    ax = axs[1]
    ax.set_title("b) an den V-Nuten hochklappen", fontsize=14)
    ax.add_patch(Rectangle((0, 0), 25, 1, fc="#85B7EB", ec="#185FA5"))
    ax.add_patch(Rectangle((-1, 0), 1, 12, fc="#85B7EB", ec="#185FA5", angle=0))
    ax.add_patch(Rectangle((25, 0), 1, 12, fc="#85B7EB", ec="#185FA5"))
    ax.add_patch(FancyArrowPatch((-6, 4), (-2, 12), arrowstyle="->", mutation_scale=12, connectionstyle="arc3,rad=-0.3"))
    ax.add_patch(FancyArrowPatch((31, 4), (27, 12), arrowstyle="->", mutation_scale=12, connectionstyle="arc3,rad=0.3"))
    ax.set_xlim(-8, 33); ax.set_ylim(-2, 16); ax.set_aspect("equal"); ax.axis("off")
    # c) geschlossen
    ax = axs[2]
    ax.set_title("c) geschlossen, letzte Ecke kleben", fontsize=14)
    ax.add_patch(Rectangle((0, 0), 25, 14, fc="none", ec="#185FA5", lw=3))
    ax.add_patch(Circle((0, 14), 1.6, fc="none", ec="#D85A30", lw=1.5))
    ax.text(3, 16.5, "Klebenaht", fontsize=12, color="#D85A30")
    ax.set_xlim(-4, 29); ax.set_ylim(-3, 19); ax.set_aspect("equal"); ax.axis("off")
    fig.tight_layout()
    fig.savefig(AUS / "schritt1_roh.png", dpi=110, facecolor="white")
    plt.close(fig)
    beschriften("schritt1", 1, "Folie einlegen und Schacht falten",
                ["Folie zuschneiden und in die Taschen kleben (Klarsichtkleber)",
                 "Knicke vorsichtig um 90° biegen – bei PLA vorher anföhnen", "letzte Ecke mit den halben Fasen verkleben"])


def skizze_hebel():
    """Schritt 7: Endlagen ±45° und Hub."""
    fig, ax = plt.subplots(figsize=(8, 8))
    r = 16
    for winkel, farbe, text in ((0, "#888780", "Mitte (Fäden anknoten)"), (45, "#D85A30", "+45°"), (-45, "#185FA5", "−45°")):
        a = math.radians(winkel)
        x1, y1 = r * math.cos(a), r * math.sin(a)
        ax.plot([-x1, x1], [-y1, y1], color=farbe, lw=5 if winkel == 0 else 3, solid_capstyle="round",
                alpha=1 if winkel else 0.6)
        if winkel:
            ax.text(x1 + 1.5, y1, text, color=farbe, fontsize=16, va="center")
    ax.add_patch(Circle((0, 0), 2, fc="#185FA5"))
    ax.text(0, -9, "Servowelle", ha="center", fontsize=15)
    # Fäden nach oben (Mittelstellung)
    for x in (-r, r):
        ax.plot([x, 0], [0, 40], color="black", lw=1)
    ax.add_patch(Rectangle((-0.75, 38), 1.5, 8, fc="#BA7517"))
    ax.text(2, 43, "Röhrchen", fontsize=15)
    ax.annotate("", xy=(r * math.cos(math.radians(45)), r * math.sin(math.radians(45))),
                xytext=(r * math.cos(math.radians(45)), -r * math.sin(math.radians(45))),
                arrowprops=dict(arrowstyle="<->", color="#D85A30"))
    ax.text(13.5, -3, "≈ 22 mm Hub", color="#D85A30", fontsize=15, va="center")
    ax.text(-30, -24, "Servodecoder: Endlagen ±45°, langsam, in der Endlage abschalten\n"
                      "innen ±14 mm ≈ 20 mm Hub · außen ±16 mm ≈ 22,5 mm Hub", fontsize=13)
    ax.set_xlim(-32, 32); ax.set_ylim(-28, 48); ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(AUS / "schritt7_roh.png", dpi=110, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    beschriften("schritt7", 7, "Endlagen einstellen und testen",
                ["Servo in Mittelstellung, beide Kabinen auf halber Höhe", "Endlagen ±45° – eine Kabine oben, die andere unten",
                 "Kabinen müssen leicht laufen, sonst Lochkanten anfasen"])


if __name__ == "__main__":
    skizze_falten()
    schritte()
    skizze_hebel()
    print("Bildanleitung fertig")
