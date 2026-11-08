"""
SA_02 Läden: Ladeneinsatz Kiosk/Imbiss, Ladenfront, Portal, Fenster, Fächer-Oberlicht.
Verglasung: klare PET-Folie 0,2 mm, von hinten in einen 0,25 mm tiefen Falz geklebt.
"""
import math
from shapely.geometry import box, Point, Polygon
from shapely.ops import unary_union
from sa_basis import *

G = "SA_02_Laeden"
B, T, H, W = 35.6, 48.0, 24.0, 1.2       # Ladeneinsatz: Breite, Tiefe, Höhe, Wand
HELL, HOLZ, DUNKEL = "#E8E0CC", "#7A5230", "#3C3C3C"
FALZ = 0.25


def ladeneinsatz(schild="KIOSK"):
    """Offener Kasten (unten offen), Front bei y = 0. Stehend drucken."""
    name = f"Ladeneinsatz_{schild.capitalize()}"
    tuer = (B - 3 - 9, 0.0, B - 3, 18.8)          # x0, z0, x1, z1
    fenster = (2.0, 7.0, 20.0, 19.0)
    b = [quader("Laden", 0, 0, 0, B, T, H),
         quader("Innenraum", W, W, -1, B - 2 * W, T - 2 * W, H - W + 1, op="cut", ziele=["Laden"])]
    for nm, (x0, z0, x1, z1) in (("Tueroeffnung", tuer), ("Fenster", fenster)):
        b.append(quader(nm, x0, -1, z0 - (1 if z0 == 0 else 0), x1 - x0, W + 2, z1 - z0 + (1 if z0 == 0 else 0),
                        op="cut", ziele=["Laden"]))
    # Holz: Türblatt (0,8 zurückgesetzt) und Thekenbrett (ragt 1,5 vor)
    b += [quader("Holz", tuer[0] + 0.2, 0.8, 0, 8.6, 0.8, 18.6),
          quader("Theke", fenster[0], -1.5, 6.0, 20.0, 2.7, 1.0),
          verbinden("Holz", ["Theke"]),
          ausschneiden("Laden", ["Holz"], behalten=True)]
    # Schild: erhabene Schrift über dem Fenster, 0,3 vor der Front
    b += text("Schild", schild, (fenster[0] + fenster[2]) / 2, 20.2, 2.5, 0.3, front_ebene(0.0), koerper="Schrift")
    v_laden = B * T * H - (B - 2 * W) * (T - 2 * W) * (H - W) - 9 * 18.8 * W - 18 * 12 * W - 20 * 1.0 * W
    v_holz = 8.6 * 18.6 * 0.8 + 20 * 1.0 * 2.7
    return bauen(name, b, G, {"Laden": v_laden, "Holz": v_holz}, ansicht="iso",
                 kamera={"target": [B / 2, T / 2, H / 2], "yaw": math.radians(-30), "pitch": math.radians(20),
                         "distance": 110},
                 koerperfarben={"Laden": HELL, "Holz": HOLZ, "Schrift": "#FFFFFF"})


def _platte(name, oeffnungen, vertiefungen, falz_bereiche, breite=B, hoehe=H, dicke=1.2):
    """Flach liegende Frontplatte (Ansicht oben, z = 0 … dicke). Öffnungen durch, Vertiefungen 0,4 tief,
    Folienfalz 0,25 von unten (Rückseite liegt beim Drucken unten)."""
    platte = box(0, 0, breite, hoehe)
    oeff = unary_union([box(*o) for o in oeffnungen]) if oeffnungen else None
    vert = unary_union([box(*v) for v in vertiefungen]) if vertiefungen else None
    falz = unary_union([box(*f) for f in falz_bereiche]) if falz_bereiche else None
    koerper = platte.difference(oeff) if oeff is not None else platte
    b = flaeche(name, koerper, dicke, koerper="Rahmen")
    v = koerper.area * dicke
    if vert is not None:
        vv = vert.difference(oeff) if oeff is not None else vert
        b += flaeche("Vertiefung", vv, 0.4, "cut", offset=dicke, richtung="negative", ziele=["Rahmen"])
        v -= vv.area * 0.4
    if falz is not None:
        ff = falz.difference(oeff) if oeff is not None else falz
        b += flaeche("Falz", ff, FALZ, "cut", offset=0.0, ziele=["Rahmen"])
        v -= ff.area * FALZ
    return b, v


def _scheiben(x0, y0, x1, y1, nx, ny, steg=0.6):
    """Fenster in nx × ny Scheiben mit Sprossen 'steg' teilen."""
    bw = (x1 - x0 - (nx - 1) * steg) / nx
    bh = (y1 - y0 - (ny - 1) * steg) / ny
    return [(x0 + i * (bw + steg), y0 + j * (bh + steg), x0 + i * (bw + steg) + bw, y0 + j * (bh + steg) + bh)
            for i in range(nx) for j in range(ny)]


def ladenfront():
    """Tür in der Mitte (vertieft, Glasfeld oben), links und rechts Schaufenster mit Kreuzsprosse."""
    fl, fr = (1.5, 4.0, 12.5, 19.0), (B - 12.5, 4.0, B - 1.5, 19.0)
    tuer = (B / 2 - 4, 0.0, B / 2 + 4, 19.0)
    tuerglas = (B / 2 - 2.5, 9.0, B / 2 + 2.5, 17.5)
    oeff = _scheiben(*fl, 2, 2) + _scheiben(*fr, 2, 2) + [tuerglas]
    falz = [(fl[0] - 0.8 if fl[0] > 0.8 else 0.6, fl[1] - 0.8, fl[2] + 0.8, fl[3] + 0.8),
            (fr[0] - 0.8, fr[1] - 0.8, min(fr[2] + 0.8, B - 0.6), fr[3] + 0.8),
            (tuerglas[0] - 0.8, tuerglas[1] - 0.8, tuerglas[2] + 0.8, tuerglas[3] + 0.8)]
    b, v = _platte("Ladenfront", oeff, [tuer], falz)
    return bauen("Ladenfront", b, G, {"Rahmen": v}, ansicht="top", koerperfarben={"Rahmen": HOLZ})


def portal():
    """Zweiflügelige Tür 20 × 20 (vertieft) mit zwei Glasfeldern."""
    tuer = (B / 2 - 10, 0.0, B / 2 + 10, 20.0)
    gl = [(B / 2 - 8.5, 7.0, B / 2 - 1.0, 18.5), (B / 2 + 1.0, 7.0, B / 2 + 8.5, 18.5)]
    falz = [(B / 2 - 9.3, 6.2, B / 2 + 9.3, 19.3)]
    b, v = _platte("Portal", gl, [tuer], falz)
    return bauen("Portal", b, G, {"Rahmen": v}, ansicht="top", koerperfarben={"Rahmen": HOLZ})


def fenster():
    """Brüstung bis Höhe 6, darüber ein Fenster 26 × 16 mit Kreuzsprosse."""
    f = (B / 2 - 13, 6.5, B / 2 + 13, 22.5)
    falz = [(f[0] - 0.8, f[1] - 0.8, f[2] + 0.8, f[3] + 0.8)]
    b, v = _platte("Fenster", _scheiben(*f, 2, 2), [], falz)
    return bauen("Fenster", b, G, {"Rahmen": v}, ansicht="top", koerperfarben={"Rahmen": HOLZ})


def oberlicht():
    """Fächer-Oberlicht: Halbkreis r 17,5, 0,8 dick; Rahmen 0,6, Nabe r 3, fünf Fächerstege 0,6.
    Die sechs Felder sind offen (Folie von hinten)."""
    r, dicke, steg = 17.5, 0.8, 0.6
    halb = Point(0, 0).buffer(r, 128).intersection(box(-r - 1, 0, r + 1, r + 1))
    innen = Point(0, 0).buffer(r - steg, 128).difference(Point(0, 0).buffer(3.0 + steg, 64)).intersection(
        box(-r, steg, r, r))
    from shapely.affinity import rotate
    stege = unary_union([rotate(box(0, -steg / 2, r + 1, steg / 2), w, origin=(0, 0)) for w in (30, 60, 90, 120, 150)])
    felder = innen.difference(stege)
    koerper = halb.difference(felder)
    b = flaeche("Oberlicht", koerper, dicke, koerper="Oberlicht")
    return bauen("Faecher_Oberlicht", b, G, {"Oberlicht": koerper.area * dicke}, ansicht="top",
                 koerperfarben={"Oberlicht": "#F2F2F2"})


def alle():
    ladeneinsatz("KIOSK")
    ladeneinsatz("IMBISS")
    ladenfront()
    portal()
    fenster()
    oberlicht()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        globals()[sys.argv[1]](*sys.argv[2:])
    else:
        alle()
