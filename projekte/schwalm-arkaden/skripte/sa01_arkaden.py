"""
SA_01 Arkaden: Bogenkachel 42, Wandkacheln, Durchlasskachel 36, Bogenlaibungen.
Kacheln liegen flach (Außenansicht oben, z = 0 … 2), Ursprung linke untere Ecke der Ansicht.
Ziegelfugen und Radialfugen werden nur ins 3MF eingerechnet (STEP bleibt glatt zum Weiterbearbeiten).
"""
import math
import manifold3d as mf
from sa_basis import *

G = "SA_01_Arkaden"
STEIN = 42 / 26          # Ziegellänge, nicht runden
DICKE = 2.0              # Kacheldicke
HOEHE = 55.0             # Kachelhöhe
ROT, SAND = "#A0472E", "#D9C7A0"


def _kachel_umriss(breite, mitte_x, kaempfer, r):
    """Kachelumriss mit Rundbogenöffnung als eine Kontur (Bogen direkt im Umriss)."""
    xl, xr = mitte_x - r, mitte_x + r
    return [skizze("Umriss"),
            linie([[xl, kaempfer], [xl, 0], [0, 0], [0, HOEHE], [breite, HOEHE], [breite, 0], [xr, 0], [xr, kaempfer]]),
            bogen3([xr, kaempfer], [xl, kaempfer], [mitte_x, kaempfer + r]),
            fertig(), extrusion(DICKE, "new", "Kachel_E", "Kachel")]


def _rollschicht(mitte_x, kaempfer, r_i, r_a):
    """Erhabene Rollschicht (Bogensteine) als Halbring, 0,4 hoch."""
    return [skizze("Rollschicht", "XY", DICKE),
            linie([[mitte_x - r_a, kaempfer], [mitte_x - r_i, kaempfer]]),
            bogen3([mitte_x - r_i, kaempfer], [mitte_x + r_i, kaempfer], [mitte_x, kaempfer + r_i]),
            linie([[mitte_x + r_i, kaempfer], [mitte_x + r_a, kaempfer]]),
            bogen3([mitte_x + r_a, kaempfer], [mitte_x - r_a, kaempfer], [mitte_x, kaempfer + r_a]),
            fertig(), extrusion(0.4, "join", "Rollschicht_E", ziele=["Kachel"])]


def _zahnfries(breite):
    """Zahnfries: kleine Ziegelköpfe 0,8 × 0,6, 0,4 erhaben, auf Höhe 44,8."""
    n = int(breite / STEIN)
    rs = []
    for k in range(n):
        x = k * STEIN + (STEIN - 0.8) / 2
        rs.append((x, 44.8, x + 0.8, 45.4))
    return rechtecke("Zahnfries", rs, 0.4, "join", offset=DICKE, ziele=["Kachel"]), n


def _sandstein(breite, extra):
    """Sandstein-Einlagen (Gesims, Abdeckplatte + extra) als eigener Körper; Tasche 0,4 im Kachelkörper."""
    b = [quader("Gesims", 0, 46.0, DICKE - 0.4, breite, 1.2, 1.0),
         quader("Abdeckung", 0, 54.2, DICKE - 0.4, breite, 0.8, 1.0, op="new")]
    namen = ["Abdeckung"]
    for i, (x, y, z, l, w, h) in enumerate(extra):
        b.append(quader(f"Stein{i}", x, y, z, l, w, h))
        namen.append(f"Stein{i}")
    b.append(verbinden("Gesims", namen))
    b.append(umbenennen("Gesims", "Sandstein"))
    b.append(ausschneiden("Kachel", ["Sandstein"], behalten=True))
    return b


def _schutz_prismen(bereiche):
    """Bereiche, in die keine Ziegelfugen geschnitten werden (Rollschicht, Sandstein, Fries)."""
    return mf.Manifold.batch_boolean(bereiche, mf.OpType.Add)


def _halbring_manifold(mx, my, r_i, r_a, z0, z1, rand=0.1):
    ring = mf.CrossSection.circle(r_a + rand, 96) - mf.CrossSection.circle(max(r_i - rand, 0.01), 96)
    halb = ring ^ mf.CrossSection.square([2 * r_a + 4, r_a + 4]).translate([-(r_a + 2), 0])
    return mf.Manifold.extrude(halb, z1 - z0).translate([mx, my, z0])


def _radialfugen(mx, my, r_i, r_a, anzahl, z_oben):
    """Radialfugen 0,2 breit, 0,2 tief in der Rollschicht (ohne die beiden Enden)."""
    teile = []
    for k in range(1, anzahl):
        w = 180.0 * k / anzahl
        f = mf.Manifold.cube([r_a - r_i + 0.4, 0.2, 0.2 + 1.0]).translate([r_i - 0.2, -0.1, z_oben - 0.2])
        teile.append(f.rotate([0, 0, w]).translate([mx, my, 0]))
    return mf.Manifold.batch_boolean(teile, mf.OpType.Add)


def _ziegelstruktur(breite, mx=None, kaempfer=None, r_i=None, r_a=None, fries_n=0, schluss=None, anzahl_radial=37):
    """Gesamtes Fugenwerkzeug für den Kachelkörper."""
    fugen = kastenliste_zu_manifold(ziegelfugen(0, breite, 0, 46.0, DICKE, tiefe=0.15)
                                    + ziegelfugen(0, breite, 47.2, 54.2, DICKE, tiefe=0.15))
    schutz = [mf.Manifold.cube([breite + 2, 0.8 + 0.2, 3]).translate([-1, 44.7, DICKE - 0.01])]  # Fries
    if mx is not None:
        schutz.append(_halbring_manifold(mx, kaempfer, r_i, r_a, DICKE - 0.3, DICKE + 2))
    fugen = fugen - _schutz_prismen(schutz)
    if mx is not None:
        fugen = fugen + _radialfugen(mx, kaempfer, r_i, r_a, anzahl_radial, DICKE + 0.4)
    return fugen


# ---------------------------------------------------------------------------
def bogenkachel(name="Bogenkachel_42", breite=42.0, kaempfer=22.0, r=18.0, radial=37):
    mx = breite / 2
    r_a = r + 3.0
    b = _kachel_umriss(breite, mx, kaempfer, r)
    b += _rollschicht(mx, kaempfer, r, r_a)
    fries, n = _zahnfries(breite)
    b += fries
    # Schlussstein über dem Scheitel, Kämpfersteine an den Bogenanfängen
    scheitel = kaempfer + r
    extra = [(mx - 1.2, scheitel - 0.4, DICKE, 2.4, 3.8, 0.8),
             (mx - r - 2.6, kaempfer - 0.6, DICKE - 0.4, 2.6, 1.2, 0.8),
             (mx + r, kaempfer - 0.6, DICKE - 0.4, 2.6, 1.2, 0.8)]
    b += _sandstein(breite, extra)
    # Handrechnung (Platte, Ring, Fries, Sandstein) – Überschneidungen über shapely
    from shapely.geometry import Polygon, Point, box
    from shapely.ops import unary_union
    oeff = unary_union([box(mx - r, 0, mx + r, kaempfer), Point(mx, kaempfer).buffer(r, 512)])
    platte = box(0, 0, breite, HOEHE).difference(oeff)
    ring = Point(mx, kaempfer).buffer(r_a, 512).difference(Point(mx, kaempfer).buffer(r, 512)).intersection(
        box(0, kaempfer, breite, HOEHE))
    fries_a = [box(k * STEIN + (STEIN - 0.8) / 2, 44.8, k * STEIN + (STEIN - 0.8) / 2 + 0.8, 45.4) for k in range(n)]
    sand = [box(0, 46.0, breite, 47.2), box(0, 54.2, breite, 55.0)]
    s_schluss = box(mx - 1.2, scheitel - 0.4, mx + 1.2, scheitel + 3.4)
    s_kaempfer = [box(mx - r - 2.6, kaempfer - 0.6, mx - r, kaempfer + 0.6), box(mx + r, kaempfer - 0.6, mx + r + 2.6, kaempfer + 0.6)]
    v_kachel = platte.area * DICKE + ring.area * 0.4 + sum(f.area for f in fries_a) * 0.4
    # abgezogen: Taschen 0,4 (Gesims/Abdeckung/Kämpfer in der Platte), Kämpfer- und Schlussstein im Ring
    v_kachel -= sum(platte.intersection(s).area for s in sand + s_kaempfer) * 0.4
    v_kachel -= sum(ring.intersection(s).area for s in s_kaempfer + [s_schluss]) * 0.4
    v_sand = sum(s.area for s in sand) * 1.0 + sum(s.area for s in s_kaempfer) * 0.8 + s_schluss.area * 0.8
    struktur = {"Kachel": _ziegelstruktur(breite, mx, kaempfer, r, r_a, n, anzahl_radial=radial)}
    return bauen(name, b, G, {"Kachel": v_kachel, "Sandstein": v_sand}, struktur=struktur, ansicht="top",
                 koerperfarben={"Kachel": ROT, "Sandstein": SAND})


def wandkachel(laenge):
    name = f"Wandkachel_{laenge:g}"
    b = [quader("Kachel", 0, 0, 0, laenge, HOEHE, DICKE)]
    fries, n = _zahnfries(laenge)
    b += fries
    b += _sandstein(laenge, [])
    v_kachel = laenge * HOEHE * DICKE + n * 0.8 * 0.6 * 0.4 - (laenge * 1.2 + laenge * 0.8) * 0.4
    v_sand = laenge * 2.0 * 1.0
    struktur = {"Kachel": _ziegelstruktur(laenge)}
    return bauen(name, b, G, {"Kachel": v_kachel, "Sandstein": v_sand}, struktur=struktur, ansicht="top",
                 koerperfarben={"Kachel": ROT, "Sandstein": SAND})


def laibung(laenge):
    """Halbschale innen r 18,0, außen r 18,8, stehend zu drucken (Länge senkrecht)."""
    name = f"Laibung_{laenge:g}"
    b = [skizze("Laibung"), linie([[-18.8, 0], [-18.0, 0]]), bogen3([-18.0, 0], [18.0, 0], [0, 18.0]),
         linie([[18.0, 0], [18.8, 0]]), bogen3([18.8, 0], [-18.8, 0], [0, 18.8]), fertig(),
         extrusion(laenge, "new", "Laibung_E", "Laibung")]
    v = math.pi * (18.8 ** 2 - 18.0 ** 2) / 2 * laenge
    return bauen(name, b, G, {"Laibung": v}, koerperfarben={"Laibung": ROT})


def alle():
    bogenkachel()
    bogenkachel("Durchlasskachel_36", breite=36.0, kaempfer=15.0, r=15.0, radial=31)
    for l in (3, 6, 7, 14, 27):
        wandkachel(l)
    for l in (50, 60, 186):
        laibung(l)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        globals()[sys.argv[1]](*[float(a) for a in sys.argv[2:]])
    else:
        alle()
