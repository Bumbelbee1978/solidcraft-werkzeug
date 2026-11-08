"""
SA_08 Stadt: Gründerzeithaus 34 (und schmal 30) – Straßenfassade flach mit Putz, weißen Gliederungen und
dunkler Tür, Seitenwand, Rückwand, Mansarddach mit zwei Gauben, Deckenplatte.
Fassade liegt flach: x = Breite, y = Höhe (Gehweg y = 0, Traufe y = 100), z = Dicke (Ansicht oben).
Fenster sind offen – klare Folie wird hinten flächig aufgeklebt.
"""
from shapely.geometry import box
from shapely.ops import unary_union
from sa_basis import *

G = "SA_08_Stadt"
PUTZ, WEISS, DUNKEL, DACH = "#D8C3A0", "#F2EFE6", "#3A3A3A", "#5B5E66"
D = 1.6                       # Wanddicke
OG_UNTERKANTEN = (24.0, 46.0, 68.0)


def _ring(r, w):
    x0, y0, x1, y1 = r
    return box(x0 - w, y0 - w, x1 + w, y1 + w).difference(box(x0, y0, x1, y1))


def fassade(breite=34.0):
    name = f"Haus_Fassade_{breite:g}"
    if breite >= 34:
        og_x = (3.5, 14.0, 24.5)
        eg_fenster = [(3.0, 2.0, 11.0, 15.0), (breite - 11.0, 2.0, breite - 3.0, 15.0)]
    else:
        og_x = (5.0, 19.0)
        eg_fenster = [(2.5, 2.0, 10.5, 15.0)]
    tuer = (breite / 2 - 3.5, 0.0, breite / 2 + 3.5, 15.0) if breite >= 34 else (breite - 11.0, 0.0, breite - 4.0, 15.0)
    og = [(x, y, x + 6.0, y + 13.0) for y in OG_UNTERKANTEN for x in og_x]
    oeffnungen = og + eg_fenster + [tuer]
    # Putzkörper: Wand + erhabener Sockel (EG, 0,4), Öffnungen durch
    wand = box(0, 0, breite, 100).difference(unary_union([box(*o) for o in oeffnungen]))
    sockel = box(0, 0, breite, 18).difference(unary_union([box(*o) for o in oeffnungen]))
    b = flaeche("Putz", wand, D, koerper="Putz")
    b += flaeche("Sockel", sockel, 0.4, "join", offset=D, ziele=["Putz"])
    # Weiß: Fensterrahmen 0,5 bündig (0,4 tief), Gesimsbänder, Verdachungen, Hauptgesims erhaben 0,4
    rahmen = unary_union([_ring(o, 0.5) for o in og])
    erhaben = unary_union([box(0, y, breite, y + 1.0) for y in (21.0, 43.0, 65.0)] + [box(0, 97.5, breite, 100)] +
                          [box(x0 - 0.8, y1 + 0.6, x1 + 0.8, y1 + 2.2) for x0, y0, x1, y1 in og if y1 + 2.2 < 97.5]).difference(
        unary_union([box(*o) for o in oeffnungen]))
    rahmen = rahmen.difference(erhaben)
    b += flaeche("Taschen", unary_union([rahmen, erhaben]).intersection(wand), 0.4, "cut", offset=D - 0.4, ziele=["Putz"])
    b += flaeche("Rahmen", rahmen, 0.4, "new", koerper="Weiss", offset=D - 0.4)
    b += flaeche("Gesimse", erhaben, 0.8, "new", koerper="Weiss__Gesimse", offset=D - 0.4)
    # Fensterkreuze (0,6 breit, um 0,4 zurückgesetzt) und Kämpfer im Schaufenster
    kreuze = []
    for x0, y0, x1, y1 in og:
        xm, yk = (x0 + x1) / 2, y0 + (y1 - y0) * 0.68
        kreuze += [box(xm - 0.3, y0, xm + 0.3, y1), box(x0, yk - 0.3, x1, yk + 0.3)]
    for x0, y0, x1, y1 in eg_fenster:
        kreuze.append(box(x0, 11.7, x1, 12.3))
    kreuz = unary_union(kreuze)
    b += flaeche("Kreuze", kreuz, 0.8, "new", koerper="Weiss__Kreuze", offset=0.0)
    # Tür dunkel, 0,8 dick an der Rückseite der Öffnung
    b.append(quader("Tuer", tuer[0], tuer[1], 0, tuer[2] - tuer[0], tuer[3] - tuer[1], 0.8))
    v_putz = wand.area * D + sockel.area * 0.4 - rahmen.area * 0.4 - erhaben.difference(rahmen).intersection(wand).area * 0.4
    v_weiss = rahmen.area * 0.4 + erhaben.area * 0.8 + kreuz.area * 0.8
    return bauen(name, b, G, {"Putz": v_putz, "Weiss": v_weiss, "Tuer": (tuer[2] - tuer[0]) * 15 * 0.8}, ansicht="top",
                 koerperfarben={"Putz": PUTZ, "Weiss": WEISS, "Tuer": DUNKEL})


def seitenwand():
    b = [quader("Wand", 0, 0, 0, 63, 100, D)]
    return bauen("Haus_Seitenwand", b, G, {"Wand": 63 * 100 * D}, ansicht="top", koerperfarben={"Wand": PUTZ})


def rueckwand(innen=30.8):
    """Rückwand (passt zwischen die Seitenwände: Hausbreite − 2 × 1,6), Fenster 5 × 10 je Geschoss, Hoftür."""
    name = f"Haus_Rueckwand_{innen:g}"
    xs = (3.4, 12.9, 22.4) if innen > 30 else (5.4, 16.4)
    oeff = [(x, y, x + 5, y + 10) for y in (26.0, 48.0, 70.0) for x in xs] + [(innen / 2 - 2.5, 0, innen / 2 + 2.5, 12)]
    form = box(0, 0, innen, 100).difference(unary_union([box(*o) for o in oeff]))
    b = flaeche("Wand", form, D, koerper="Wand")
    return bauen(name, b, G, {"Wand": form.area * D}, ansicht="top", koerperfarben={"Wand": PUTZ})


def mansarddach(breite=34.0):
    """Mansarddach: unten 63 tief, oben 55 tief, 25 hoch, Wände 1,2, unten offen; Gauben vorn (y < 0).
    Profil in der YZ-Ebene (y = Tiefe, z = Höhe), extrudiert über die Hausbreite in X."""
    import manifold3d as mf
    from shapely.geometry import Polygon
    from shapely.affinity import translate
    name = f"Haus_Mansarddach_{breite:g}"
    aussen = [(0, 0), (63, 0), (59, 25), (4, 25)]
    pa = Polygon(aussen)
    innen = pa.buffer(-1.2, join_style=2)
    innen = unary_union([innen, translate(innen, 0, -2.5)]).intersection(box(-5, -1, 70, 30))
    ik = [tuple(map(float, c)) for c in list(innen.exterior.coords)[:-1]]
    b = profil_yz("Dach", aussen, breite, koerper="Dach")
    b += profil_yz("Hohlraum", ik, breite - 2.4, op="cut", offset=1.2)
    b[-1]["params"]["targets"] = ["Dach"]

    def prisma(poly, x0, laenge):
        q = mf.CrossSection([[tuple(c) for c in list(poly.exterior.coords)[:-1]]])
        if q.area() == 0:
            q = mf.CrossSection([[tuple(c) for c in list(poly.exterior.coords)[:-1]][::-1]])
        # Querschnitt (y | z) in der XY-Ebene, in z extrudiert -> so drehen, dass Extrusion entlang X läuft
        return mf.Manifold.extrude(q, laenge).rotate([0, 90, 0]).rotate([90, 0, 0]).translate([x0, 0, 0])

    m = prisma(pa, 0, breite) - prisma(innen, 1.2, breite - 2.4)
    gauben = (breite / 2 - 11, breite / 2 + 3) if breite >= 34 else (breite / 2 - 4,)
    gdach = Polygon([(-2.6, 16.0), (2.6, 16.0), (2.6, 18.0), (-2.6, 16.6)])
    for i, x in enumerate(gauben):
        b.append(quader(f"Gaube{i}", x, -2.0, 6.0, 8.0, 4.5, 10.0, op="join", ziele=["Dach"]))
        b += profil_yz(f"Gaubendach{i}", list(gdach.exterior.coords)[:-1], 8.0, op="join", offset=x)
        b[-1]["params"]["targets"] = ["Dach"]
        b.append(quader(f"Gaubenfenster{i}", x + 1.5, -2.5, 7.5, 5.0, 0.9, 7.0, op="cut", ziele=["Dach"]))
        m = m + mf.Manifold.cube([8.0, 4.5, 10.0]).translate([x, -2.0, 6.0]) + prisma(gdach, x, 8.0)
        m = m - mf.Manifold.cube([5.0, 0.9, 7.0]).translate([x + 1.5, -2.5, 7.5])
    return bauen(name, b, G, {"Dach": m.volume()}, koerperfarben={"Dach": DACH})


def deckenplatte(innen=30.8):
    """Decken-/Bodenplatte innen (Aussteifung, später Träger für die Beleuchtung)."""
    name = f"Haus_Deckenplatte_{innen:g}"
    b = [quader("Decke", 0, 0, 0, innen, 59.8, 1.2)]
    return bauen(name, b, G, {"Decke": innen * 59.8 * 1.2}, koerperfarben={"Decke": "#BBBBBB"})


def alle():
    fassade(34.0)
    fassade(30.0)
    seitenwand()
    rueckwand(30.8)
    rueckwand(26.8)
    mansarddach(34.0)
    mansarddach(30.0)
    deckenplatte(30.8)
    deckenplatte(26.8)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        globals()[sys.argv[1]]()
    else:
        alle()
