"""
SA_05 Stahl: Einheitsträger Typ V (Außenträger 3/6/8 Felder), Fahrbahnplatten, Gitterstütze, Bogenrippe Schwalm.
Träger liegen flach (Ansicht oben): x = Länge, y = Höhe (Untergurt y = 0, Obergurt bis 12), z = Dicke.
"""
import math
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
import manifold3d as mf
from sa_basis import *

G = "SA_05_Stahl"
FELD, TH, GURT = 18.0, 12.0, 1.6        # Feldlänge, Trägerhöhe, Gurthöhe
GRUEN, BETON = "#2F4F3A", "#9A9A96"


def _traeger_flaeche(n):
    """Fachwerk als Fläche: Gurte, Pfosten, V-Streben je Feld (1,2 breit)."""
    teile = [box(0, 0, n * FELD + 1, GURT), box(0, TH - GURT, n * FELD + 1, TH)]
    for k in range(n + 1):
        teile.append(box(k * FELD, 0, k * FELD + 1, TH))
    for k in range(n):
        x0 = k * FELD + 0.5
        teile.append(LineString([(x0, GURT), (x0 + FELD / 2, TH - GURT)]).buffer(0.6, cap_style=2))
        teile.append(LineString([(x0 + FELD / 2, TH - GURT), (x0 + FELD, GURT)]).buffer(0.6, cap_style=2))
    return unary_union(teile).intersection(box(0, 0, n * FELD + 1, TH))


def _knotenbleche(n):
    """Dreieckige Knotenbleche (3 mm Schenkel) an den Untergurt- und Obergurtknoten."""
    bl = []
    for k in range(n + 1):
        x = k * FELD + 0.5
        bl.append(Polygon([(x - 2.5, GURT), (x + 2.5, GURT), (x, GURT + 2.5)]))
    for k in range(n):
        x = k * FELD + 0.5 + FELD / 2
        bl.append(Polygon([(x - 2.5, TH - GURT), (x + 2.5, TH - GURT), (x, TH - GURT - 2.5)]))
    return unary_union(bl).intersection(box(0.2, 0, n * FELD + 0.8, TH))


def aussentraeger(n):
    name = f"Aussentraeger_{n}_Felder"
    flaeche_t = _traeger_flaeche(n)
    gurte = unary_union([box(0, 0, n * FELD + 1, GURT), box(0, TH - GURT, n * FELD + 1, TH)])
    bleche = _knotenbleche(n)
    b = flaeche("Traeger", flaeche_t, 2.0, koerper="Traeger")
    b += flaeche("Gurtplatten", gurte, 1.0, "join", offset=2.0, ziele=["Traeger"])
    b += flaeche("Knotenbleche", bleche, 0.3, "join", offset=2.0, ziele=["Traeger"])
    v = flaeche_t.area * 2 + gurte.area * 1.0 + bleche.difference(gurte).area * 0.3
    return bauen(name, b, G, {"Traeger": v}, ansicht="top", koerperfarben={"Traeger": GRUEN})


def fahrbahnplatte(laenge):
    """Platte 190 breit (y) × Länge (x) × 2, Querträger 1,5 × 6 alle 18 mm, zwei Längsträger 2 × 6 unter
    den Bahnsteigen. Kopfüber drucken (Platte unten)."""
    name = f"Fahrbahnplatte_{laenge:g}"
    quer = []
    k = 0
    while k * FELD <= laenge + 0.01:
        x0 = min(max(k * FELD - 0.75, 0.0), laenge - 1.5)
        quer.append(box(x0, 2, x0 + 1.5, 188))
        k += 1
    laengs = [box(0, 48, laenge, 50), box(0, 138, laenge, 140)]
    rippen = unary_union(quer + laengs)
    b = [quader("Platte", 0, 0, 0, laenge, 190, 2.0)]
    b += flaeche("Rippen", rippen, 6.0, "join", offset=2.0, ziele=["Platte"])
    v = laenge * 190 * 2 + rippen.area * 6
    return bauen(name, b, G, {"Platte": v}, koerperfarben={"Platte": BETON})


def gitterstuetze():
    """Fuß 4,5 × 4,5 × 0,8, Schaft 3 × 3 × 41,4, Kopf 4,5 × 4,5 × 0,8; Gitter-Rillen nur im 3MF."""
    b = [quader("Stuetze", -2.25, -2.25, 0, 4.5, 4.5, 0.8),
         quader("Schaft", -1.5, -1.5, 0.8, 3, 3, 41.4, op="join", ziele=["Stuetze"]),
         quader("Kopf", -2.25, -2.25, 42.2, 4.5, 4.5, 0.8, op="join", ziele=["Stuetze"])]
    v = 2 * 4.5 * 4.5 * 0.8 + 9 * 41.4
    # X-Rillen 0,3 breit, 0,15 tief, Raster 3 mm, auf allen vier Seiten
    rillen = []
    for w in (45, -45):
        for s in range(-20, 40):
            r = mf.Manifold.cube([0.3, 8.0, 70.0], center=True).rotate([0, 0, 0])
            r = mf.Manifold.cube([70.0, 8.0, 0.3], center=True).rotate([0, w, 0]).translate([0, 0, 0.8 + s * 3.0])
            rillen.append(r)
    netz = mf.Manifold.batch_boolean(rillen, mf.OpType.Add)        # diagonale Scheiben in der XZ-Ebene
    # Haut 0,15 auf den beiden y-Seiten (dort erscheinen die Scheiben als X), dann um 90° für die x-Seiten
    haut_y = mf.Manifold.batch_boolean([mf.Manifold.cube([2.9, 0.4, 40.6]).translate([-1.45, s * 1.5 - 0.2 - s * 0.05 + (0 if s > 0 else 0), 1.0])
                                        for s in (-1, 1)], mf.OpType.Add)
    haut_y = haut_y - mf.Manifold.cube([3.2, 2.7, 50], center=True).translate([0, 0, 21.5])
    werkzeug = (netz ^ haut_y) + (netz ^ haut_y).rotate([0, 0, 90])
    return bauen("Gitterstuetze", b, G, {"Stuetze": v}, struktur={"Stuetze": werkzeug},
                 koerperfarben={"Stuetze": GRUEN})


def bogenrippe():
    """Halbring r 49/53 (Mittelpunkt = Ursprung), oben in die Anschlussleiste (y 49 … 50,6) übergehend,
    Zwickel-Ständer 1,0 breit bei x = ±27, ±36, ±45, Kämpferfüße 5 × 1 × 3."""
    ring = Point(0, 0).buffer(53, 256).difference(Point(0, 0).buffer(49, 256)).intersection(box(-60, 0, 60, 50.6))
    leiste = box(-58, 49, 58, 50.6)
    staender = []
    for x in (27, 36, 45):
        for s in (-1, 1):
            xc = s * x
            y0 = math.sqrt(53 ** 2 - x ** 2) - 0.5
            staender.append(box(xc - 0.5, y0, xc + 0.5, 49.5))
    form = unary_union([ring, leiste] + staender)
    b = flaeche("Bogenrippe", form, 2.0, koerper="Bogenrippe")
    fuesse = [box(48.5, -1, 53.5, 0.01), box(-53.5, -1, -48.5, 0.01)]
    for i, f in enumerate(fuesse):
        x0, y0, x1, y1 = f.bounds
        b.append(quader(f"Fuss{i}", x0, -1, 0, 5, 1.0, 3.0, op="join", ziele=["Bogenrippe"]))
    v = form.area * 2 + 2 * 5 * 1.0 * 3.0
    return bauen("Bogenrippe_Schwalm", b, G, {"Bogenrippe": v}, ansicht="top", koerperfarben={"Bogenrippe": GRUEN})


def alle():
    for n in (3, 6, 8):
        aussentraeger(n)
    for l in (54, 108, 144):
        fahrbahnplatte(l)
    gitterstuetze()
    bogenrippe()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        globals()[sys.argv[1]]()
    else:
        alle()
