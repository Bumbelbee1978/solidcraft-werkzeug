"""
SA_04 Aufgänge: Festtreppe mit Podest (+ Wangen, Stützen), Rolltreppe (+ Wangen), Glas-Aufzug aus Platten.
Treppe/Rolltreppe: Länge X, Breite Y, Höhe Z (Straße z = 0, Bahnsteig z = 61). Druck auf der Seite liegend.
Wangen und Stützen sind eigene, flach gedruckte Teile – so braucht nichts eine Stütze.
"""
import math
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
import manifold3d as mf
from sa_basis import *

G = "SA_04_Aufgaenge"
AUF, STG, N = 2.2, 1.22, 25            # Auftritt, Steigung, Stufen je Lauf (29,0°)
LAUF = AUF * N                          # 55
POD_X0, POD_X1, POD_Z = LAUF, LAUF + 25, STG * N   # Podest 55 … 80 auf 30,5
GRAU, ANTHR, SILBER = "#BDBDB8", "#4A4A4A", "#C9CCD1"


def _treppen_profil():
    """Seitenprofil (x | z) der ganzen Treppe als Punktliste."""
    oben = [(0.0, 0.0)]
    for lauf, (x0, z0) in enumerate(((0.0, 0.0), (POD_X1, POD_Z))):
        for i in range(N):
            oben += [(x0 + i * AUF, z0 + (i + 1) * STG), (x0 + (i + 1) * AUF, z0 + (i + 1) * STG)]
        if lauf == 0:
            oben.append((POD_X1, POD_Z))
    k = POD_Z / LAUF                                         # Neigung der Laufplatten-Unterseite
    unten = [(135.0, 2 * POD_Z - 3.43), (POD_X1 + 6.19, POD_Z), (POD_X1, POD_Z - 6.19 * k),
             (POD_X1, POD_Z - 5.0), (POD_X0, POD_Z - 5.0), (POD_X0, POD_Z - 3.43), (6.19, 0.0)]
    return oben + unten


def treppe():
    pk = _treppen_profil()
    poly = Polygon(pk)
    b = profil_xz("Treppe", pk, 10.0, koerper="Treppe")
    # Zwei quadratische Taschen 2,2 × 2,2 × 3 unter dem Podest für die Stützen
    for i, x in enumerate((POD_X0 + 7, POD_X0 + 17)):
        b.append(quader(f"Stuetzentasche{i}", x - 1.1, 5 - 1.1, POD_Z - 5.0 - 1, 2.2, 2.2, 3 + 1, op="cut",
                        ziele=["Treppe"]))
    v = poly.area * 10 - 2 * 2.2 * 2.2 * 3
    bauen("Treppe", b, G, {"Treppe": v}, koerperfarben={"Treppe": GRAU}, ansicht="front")
    return poly


def treppenwange():
    """Glaswange 0,8 dick: oben 6 mm über der Stufenvorderkante, unten bündig mit der Laufplatte.
    Rahmen 0,8 breit, Innenfeld offen (Folie). Flach drucken, 2 Stück je Treppe."""
    k = POD_Z / LAUF
    oben = [(0, 1.22 + 6), (LAUF, 1.22 + LAUF * k + 6), (POD_X1, POD_Z + 6), (135, 61 + 6)]
    unten = [(135, 2 * POD_Z - 3.43), (POD_X1 + 6.19, POD_Z), (POD_X1, POD_Z - 6.19 * k), (POD_X1, POD_Z - 5),
             (POD_X0, POD_Z - 5), (POD_X0, POD_Z - 3.43), (6.19, 0), (0, 0)]
    aussen = Polygon(oben + unten)
    # Glasfelder: nur der Teil über den Stufen (6 mm hohes Band), Rahmen 0,8
    feld1 = Polygon([(1.2, 1.22 + 1.2 * k + 0.8), (LAUF - 0.8, 1.22 + (LAUF - 0.8) * k + 0.8),
                     (LAUF - 0.8, 1.22 + (LAUF - 0.8) * k + 5.2), (1.2, 1.22 + 1.2 * k + 5.2)])
    feld2 = Polygon([(POD_X1 + 0.8, POD_Z + 1.22 + 0.8 * k + 0.8), (134.2, POD_Z + 1.22 + 54.2 * k + 0.8),
                     (134.2, POD_Z + 1.22 + 54.2 * k + 5.2), (POD_X1 + 0.8, POD_Z + 1.22 + 0.8 * k + 5.2)])
    feld3 = box(POD_X0 + 0.8, POD_Z + 0.8, POD_X1 - 0.8, POD_Z + 5.2)
    form = aussen.difference(unary_union([feld1, feld2, feld3]))
    b = flaeche("Wange", form, 0.8, koerper="Wange")
    bauen("Treppenwange", b, G, {"Wange": form.area * 0.8}, ansicht="top", koerperfarben={"Wange": ANTHR})


def treppenstuetze():
    """Podeststütze 2 × 2 × 28,5 (25,5 sichtbar + 3 in der Tasche). Liegend drucken, 2 Stück je Treppe."""
    b = [quader("Stuetze", 0, 0, 0, 28.5, 2.0, 2.0)]
    bauen("Treppenstuetze", b, G, {"Stuetze": 28.5 * 4}, koerperfarben={"Stuetze": GRAU})


# ---------------------------------------------------------------------------
def _rolltreppe_linie():
    return LineString([(0, 0.5), (15, 0.5), (120, 61), (135, 61)])


def rolltreppe():
    """Wanne 6,4 breit (y 0,8 … 7,2) mit Stufenband (Einlage 5 breit, Silber) und Querrillen im 3MF."""
    oben = _rolltreppe_linie()
    unten = oben.offset_curve(-3.0, join_style=2)            # 3 mm parallel darunter
    pk = list(oben.coords) + [(135, 61 - 3.0)] + list(unten.coords)[::-1][1:]
    poly = Polygon(pk).buffer(0).intersection(box(0, 0, 135, 70))
    pk = [tuple(map(float, c)) for c in list(poly.exterior.coords)[:-1]]
    b = profil_xz("Wanne", pk, 6.4, koerper="Wanne", offset=0.8)
    # Stufenband: 0,4 starke Einlage auf der Oberseite, y 1,5 … 6,5
    band = Polygon(list(oben.coords) + [(135, 60.6)] + list(oben.offset_curve(-0.4, join_style=2).coords)[::-1][1:])
    bk = [tuple(map(float, c)) for c in list(band.exterior.coords)[:-1]]
    b += profil_xz("Stufenband", bk, 5.0, koerper="Stufenband", offset=1.5)
    b += [ausschneiden("Wanne", ["Stufenband"], behalten=True)]
    # Querrillen nur im schrägen Teil: 0,3 breit alle 0,8, 0,15 tief (Vorbild: Stufenkanten)
    ang = math.atan2(60.5, 105)
    rillen = []
    s = 1.0
    laenge = math.hypot(105, 60.5)
    while s < laenge - 1.0:
        x, z = 15 + s * math.cos(ang), 0.5 + s * math.sin(ang)
        r = mf.Manifold.cube([0.3, 5.2, 1.0]).translate([-0.15, -0.1, -0.15]).rotate([0, -math.degrees(ang), 0])
        rillen.append(r.translate([x, 1.5 - 0.0, z]))
        s += 0.8
    rillen_m = mf.Manifold.batch_boolean(rillen, mf.OpType.Add)
    v_wanne = poly.area * 6.4 - band.area * 5.0
    bauen("Rolltreppe", b, G, {"Wanne": v_wanne, "Stufenband": band.area * 5.0}, struktur={"Stufenband": rillen_m},
          koerperfarben={"Wanne": ANTHR, "Stufenband": SILBER}, ansicht="front")
    return poly


def rolltreppenwange():
    """Seitenwange 0,8 dick: deckt die Wanne ab und steht 5 mm über das Stufenband (Handlauf)."""
    oben = LineString([(0, 5.5), (15, 5.5), (120, 66), (135, 66)])
    unten = _rolltreppe_linie().offset_curve(-3.0, join_style=2)
    pk = list(oben.coords) + list(unten.coords)[::-1]
    poly = Polygon(pk).buffer(0).intersection(box(0, 0, 135, 70))
    b = flaeche("Wange", poly, 0.8, koerper="Wange")
    bauen("Rolltreppenwange", b, G, {"Wange": poly.area * 0.8}, ansicht="top", koerperfarben={"Wange": ANTHR})


# ---------------------------------------------------------------------------
RIEGEL = [(0.0, 0.8), (29.6, 30.4), (60.6, 61.4), (82.2, 83.0)]


def _aufzugplatte(name, breite, tuer=None):
    """Rahmenplatte 0,8 dick, Höhe 83: Stiele 0,8 links/rechts, Riegel 0,8; Felder offen (Folie innen).
    tuer = Unterkante des Türrahmens (6 × 13, mittig) oder None."""
    felder = [box(0.8, RIEGEL[i][1], breite - 0.8, RIEGEL[i + 1][0]) for i in range(3)]
    form = box(0, 0, breite, 83).difference(unary_union(felder))
    if tuer is not None:
        rahmen = box(breite / 2 - 3, tuer, breite / 2 + 3, tuer + 13)
        oeffnung = box(breite / 2 - 2.2, tuer + 0.8 if tuer > 0 else 0.0, breite / 2 + 2.2, tuer + 12.2)
        form = form.union(rahmen).difference(oeffnung)
    b = flaeche(name, form, 0.8, koerper="Platte")
    bauen(name, b, G, {"Platte": form.area * 0.8}, ansicht="top", koerperfarben={"Platte": ANTHR})


def aufzug():
    _aufzugplatte("Aufzug_Laengsseite", 15.0)
    _aufzugplatte("Aufzug_Schmalseite_Tuer_unten", 10.4, tuer=0.0)
    _aufzugplatte("Aufzug_Schmalseite_Tuer_oben", 10.4, tuer=60.6)
    # Dach 1,6 dick mit Rille 0,8 × 0,8 an der Unterseite für die LED-Litze
    b = [quader("Dach", 0, 0, 0, 15, 12, 1.6), quader("LED_Rille", 7.1, -1, -1, 0.8, 14, 1.8, op="cut", ziele=["Dach"])]
    bauen("Aufzug_Dach", b, G, {"Dach": 15 * 12 * 1.6 - 0.8 * 12 * 0.8}, koerperfarben={"Dach": ANTHR})
    bauen("Aufzug_Boden", [quader("Boden", 0, 0, 0, 15, 12, 0.8)], G, {"Boden": 15 * 12 * 0.8},
          koerperfarben={"Boden": ANTHR})
    # Kabine 13 × 10 × 14, offene Seite zeigt nach oben (so druckt sie ohne Stützen)
    b = [quader("Kabine", 0, 0, 0, 13, 14, 10), quader("Innen", 0.8, 0.8, 0.8, 11.4, 12.4, 10, op="cut", ziele=["Kabine"])]
    bauen("Aufzug_Kabine", b, G, {"Kabine": 13 * 14 * 10 - 11.4 * 12.4 * 9.2}, koerperfarben={"Kabine": SILBER})


def alle():
    treppe()
    treppenwange()
    treppenstuetze()
    rolltreppe()
    rolltreppenwange()
    aufzug()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        globals()[sys.argv[1]]()
    else:
        alle()
