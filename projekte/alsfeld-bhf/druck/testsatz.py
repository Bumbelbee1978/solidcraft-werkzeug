"""
Fügt Einzelteile (3MF aus SolidCraft) zu einer Druckplatte für den Bambu A1 (256 × 256 mm) zusammen.
Jedes Teil bleibt ein eigenes Objekt, damit es in Bambu Studio einzeln verschoben werden kann.
"""
import math
import re
import zipfile
from pathlib import Path

import numpy as np

TEILE = Path("/home/claude/heimanlage/solidcraft/teile")
BETT = 256.0


def lesen(datei):
    """Liest alle Objekte einer 3MF: Name -> (Punkte Nx3, Dreiecke Mx3)."""
    xml = zipfile.ZipFile(TEILE / datei).read("3D/3dmodel.model").decode()
    objekte = {}
    for name, inhalt in re.findall(r'<object id="\d+" type="model" name="([^"]+)">(.*?)</object>', xml, re.S):
        p = np.array([[float(a), float(b), float(c)] for a, b, c in
                      re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', inhalt)])
        d = np.array([[int(a), int(b), int(c)] for a, b, c in
                      re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', inhalt)])
        objekte[name] = (p, d)
    return objekte


def drehen_z(p, grad):
    """Dreht Punkte um die Z-Achse."""
    a = math.radians(grad)
    m = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    return p @ m.T


def ablegen(p, x0, y0):
    """Verschiebt so, dass die linke untere Ecke der Grundfläche bei (x0, y0) liegt und z bei 0 beginnt."""
    return p - p.min(axis=0) + np.array([x0, y0, 0])


def schreiben(datei, teile):
    """Schreibt eine 3MF mit je einem Objekt pro Teil."""
    res, build = [], []
    for i, (name, p, d) in enumerate(teile, start=1):
        v = "".join(f'<vertex x="{a:.5f}" y="{b:.5f}" z="{c:.5f}"/>' for a, b, c in p)
        t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in d)
        res.append(f'<object id="{i}" type="model" name="{name}"><mesh><vertices>{v}</vertices>'
                   f'<triangles>{t}</triangles></mesh></object>')
        build.append(f'<item objectid="{i}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="de-DE" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources>{"".join(res)}</resources><build>{"".join(build)}</build></model>')
    with zipfile.ZipFile(datei, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/'
                   'vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/'
                   'vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" '
                   'Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", model)


if __name__ == "__main__":
    platte_p, platte_d = lesen("HA_01_Wendelplatte.3mf")["Wendelplatte"]
    # Symmetrieachse (15°) nach +Y drehen: Außenbogen zeigt nach oben
    platte_p = drehen_z(platte_p, 75)
    konsolen = lesen("HA_02_Konsolen.3mf")
    for n, (p, _) in {"Platte": (platte_p, 0), **konsolen}.items():
        g = p.max(axis=0) - p.min(axis=0)
        print(f"{n}: {g[0]:.1f} × {g[1]:.1f} × {g[2]:.1f} mm")
