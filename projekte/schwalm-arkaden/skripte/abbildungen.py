"""
Abbildungen für die Bildanleitung: Teile aus den fertigen 3MF-Dateien in Einbaulage zusammenstellen und mit
SolidCraft rendern. Neue Teile kräftig, bereits verbaute Teile blass.
"""
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

CLI = "/home/claude/bin/solidcraft-cli"
TEILE = Path(__file__).parent / "teile"
ABB = Path(__file__).parent / "abb"
ABB.mkdir(exist_ok=True)
SCHRIFT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


# ---------- Transformationen ----------
def T(dx=0, dy=0, dz=0):
    return trimesh.transformations.translation_matrix([dx, dy, dz])


def RX(w):
    return trimesh.transformations.rotation_matrix(math.radians(w), [1, 0, 0])


def RY(w):
    return trimesh.transformations.rotation_matrix(math.radians(w), [0, 1, 0])


def RZ(w):
    return trimesh.transformations.rotation_matrix(math.radians(w), [0, 0, 1])


def kette(*m):
    """Matrizen von rechts nach links anwenden: kette(A, B) = A · B (erst B, dann A)."""
    e = np.eye(4)
    for x in m:
        e = e @ x
    return e


def lade(datei):
    """3MF eines Teils laden -> {Körpername: Trimesh}. datei = Pfad oder (Pfad, [Körpernamen])."""
    auswahl = None
    if isinstance(datei, tuple):
        datei, auswahl = datei
    p = Path(datei) if str(datei).startswith("/") else TEILE / datei
    s = trimesh.load(p, force="scene", process=False)
    return {n: g.copy() for n, g in s.geometry.items() if auswahl is None or n in auswahl}


def szene(name, teile, kamera, breite=1400, hoehe=900, blass=0.22, raster=False):
    """teile: Liste von (datei, matrix, farbe oder {körper: farbe}, neu: bool).
    Rendert die Szene und gibt den Bildpfad zurück."""
    sz = trimesh.Scene()
    darstellung = []
    for k, (datei, m, farbe, neu) in enumerate(teile):
        for kn, g in lade(datei).items():
            g = g.copy()
            g.apply_transform(m)
            nm = f"T{k}_{kn}"
            sz.add_geometry(g, geom_name=nm, node_name=nm)
            f = farbe.get(kn, "#888888") if isinstance(farbe, dict) else farbe
            darstellung.append((nm, f, (neu if not isinstance(neu, bool) else (1.0 if neu else blass))))
    pfad3mf = ABB / f"{name}.3mf"
    sz.export(pfad3mf)
    skript = ABB / f"{name}.json"
    json.dump({"commands": [{"command": "file.insert_mesh", "params": {"path": str(pfad3mf)}}]}, open(skript, "w"))
    args = [CLI, "snapshot", str(skript), "--out", str(ABB / f"{name}.png"), "--width", str(breite), "--height",
            str(hoehe), "--no-axes", "--quality", "fine"]
    args += ["--view", kamera] if isinstance(kamera, str) else ["--camera", json.dumps(kamera)]
    if not raster:
        args.append("--no-grid")
    for nm, f, op in darstellung:
        args += ["--body", f"{nm}:opacity={op},color={f}"]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode:
        print(name, r.stderr[:400])
    pfad3mf.unlink(missing_ok=True)
    skript.unlink(missing_ok=True)
    return ABB / f"{name}.png"


def kamera(ziel, yaw, pitch, abstand):
    return {"target": list(ziel), "yaw": math.radians(yaw), "pitch": math.radians(pitch), "distance": abstand}


def schritt_kopf(bild, nummer, titel):
    """Orange Schrittnummer und Titel oben ins Bild setzen."""
    im = Image.open(bild).convert("RGB")
    w, h = im.size
    neu = Image.new("RGB", (w, h + 90), "white")
    neu.paste(im, (0, 90))
    d = ImageDraw.Draw(neu)
    d.ellipse([18, 14, 80, 76], fill="#D85A30")
    d.text((49, 45), str(nummer), fill="white", font=ImageFont.truetype(SCHRIFT, 36), anchor="mm")
    d.text((100, 45), titel, fill="black", font=ImageFont.truetype(SCHRIFT, 32), anchor="lm")
    neu.save(bild)
    return bild


def beschriften(bild, marken):
    """marken: Liste (x, y, text) in Bildpixeln – kleine Beschriftungsfähnchen."""
    im = Image.open(bild).convert("RGB")
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(SCHRIFT, 24)
    for x, y, t in marken:
        bb = d.textbbox((x, y), t, font=f)
        d.rectangle([bb[0] - 8, bb[1] - 5, bb[2] + 8, bb[3] + 5], fill="#1D4E89")
        d.text((x, y), t, fill="white", font=f)
    im.save(bild)
    return bild
