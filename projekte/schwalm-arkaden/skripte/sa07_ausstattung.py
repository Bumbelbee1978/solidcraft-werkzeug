"""
SA_07 Ausstattung: Bänke, Marktstand + Markise, Fahrradstation + Dach, Zugzielanzeiger, Wartepavillon,
Tram-Wartehaus, Fahrkartenautomat, Laterne, Brunnen, Litfaßsäule, Tram-Steig.
Kleinteile mit 0,2-Düse drucken; Glas = Folie, Masten und Bügel = Messingdraht.
"""
import math
from shapely.geometry import box, Polygon, Point
from shapely.ops import unary_union
from sa_basis import *

G = "SA_07_Ausstattung"
ANTHR, HOLZ, HELL, WEISS, ROTF, BLAU, GELB = "#4A4A4A", "#7A5230", "#C8C8C4", "#F4F4F0", "#B0302A", "#1F4E9A", "#E3B505"


def _drehteil(name, profil, koerper):
    """Rotationsteil um die Z-Achse aus einem Halbprofil (r | z), r ≥ 0."""
    pk = [[r, -z] for r, z in profil]
    return [skizze(name, "XZ"), linie(pk, True), fertig(),
            {"command": "solid.revolve", "params": {"axis": "Z", "angle": "360 deg", "operation": "new",
                                                     "body_name": koerper, "name": name + "_R"}}]


def _drehvolumen(profil):
    """Volumen eines Rotationskörpers (Pappus-Regel) aus dem Halbprofil."""
    p = Polygon(profil)
    return p.area * 2 * math.pi * p.centroid.x


# ---------------------------------------------------------------------------
def doppelbank():
    """Sitz 3,2 × 0,5 auf Höhe 2,5, Lehne 0,8 × 2,2 mittig, Länge 12, zwei Füße 0,8 × 0,8."""
    profil = [(-1.6, 2.5), (1.6, 2.5), (1.6, 3.0), (0.4, 3.0), (0.4, 5.2), (-0.4, 5.2), (-0.4, 3.0), (-1.6, 3.0)]
    b = profil_xz("Bank", profil, 12.0, koerper="Bank", offset=-6.0)
    for i, y in enumerate((-4.5, 4.5)):
        b.append(quader(f"Fuss{i}", -0.4, y - 0.4, 0, 0.8, 0.8, 2.5, op="join", ziele=["Bank"]))
    v = Polygon(profil).area * 12 + 2 * 0.8 * 0.8 * 2.5
    bauen("Doppelsitzbank", b, G, {"Bank": v}, koerperfarben={"Bank": ANTHR})


def parkbank():
    b = [quader("Bank", -1.6, -5, 2.5, 3.2, 10, 0.5)]
    for i, y in enumerate((-3.5, 3.5)):
        b.append(quader(f"Fuss{i}", -1.2, y - 0.4, 0, 2.4, 0.8, 2.5, op="join", ziele=["Bank"]))
    bauen("Parkbank", b, G, {"Bank": 3.2 * 10 * 0.5 + 2 * 2.4 * 0.8 * 2.5}, koerperfarben={"Bank": HOLZ})


def marktstand():
    """Boden 18 × 18 × 0,8, U-förmige Theke bis 7,5, Auslage mit 3 Fächern, vier Pfosten 1 × 1
    (vorn bis 13,0, hinten bis 17,0). Vorderseite y = −9."""
    theke = unary_union([box(-9, -9, 9, -4), box(-9, -4, -5, 9), box(5, -4, 9, 9)])
    b = [quader("Stand", -9, -9, 0, 18, 18, 0.8)]
    b += flaeche("Theke", theke, 6.7, "join", offset=0.8, ziele=["Stand"])
    faecher = [box(-8.2, -8.2, -3.0, -4.8), box(-2.2, -8.2, 2.2, -4.8), box(3.0, -8.2, 8.2, -4.8)]
    b += flaeche("Auslage", unary_union(faecher), 0.8, "cut", offset=7.5, richtung="negative", ziele=["Stand"])
    pf = [(-8, -8, 13.0), (8, -8, 13.0), (-8, 8, 17.0), (8, 8, 17.0)]
    for i, (x, y, h) in enumerate(pf):
        b.append(quader(f"Pfosten{i}", x - 0.5, y - 0.5, 7.5, 1.0, 1.0, h - 7.5, op="join", ziele=["Stand"]))
    v = 18 * 18 * 0.8 + theke.area * 6.7 - sum(f.area for f in faecher) * 0.8 + sum(1.0 * (h - 7.5) for *_, h in pf)
    bauen("Marktstand", b, G, {"Stand": v}, koerperfarben={"Stand": HOLZ})


def markise():
    """Markise 19 × 20 × 0,8 mit Volant 2 mm vorn; weiße Streifen 1,25 breit als Einlage (0,4)."""
    b = [quader("Markise", 0, 0, 0, 19, 20, 0.8), quader("Volant", 0, 0, 0.8, 19, 0.8, 1.2, op="join", ziele=["Markise"])]
    streifen = [(0.625 + k * 2.5, 0.8, 0.625 + k * 2.5 + 1.25, 20) for k in range(8) if 0.625 + k * 2.5 + 1.25 <= 19]
    for i, (x0, y0, x1, y1) in enumerate(streifen):
        b.append(quader(f"S{i}", x0, y0, 0.4, x1 - x0, y1 - y0, 0.4))
    b += [verbinden("S0", [f"S{i}" for i in range(1, len(streifen))]), umbenennen("S0", "Streifen"),
          ausschneiden("Markise", ["Streifen"], behalten=True)]
    v_s = sum((x1 - x0) * (y1 - y0) * 0.4 for x0, y0, x1, y1 in streifen)
    bauen("Markise", b, G, {"Markise": 19 * 20 * 0.8 + 19 * 0.8 * 1.2 - v_s, "Streifen": v_s}, ansicht="top",
          koerperfarben={"Markise": ROTF, "Streifen": WEISS})


def fahrradstation():
    """Fundament 40 × 15 × 0,8 mit 16 Löchern Ø 0,7 für Drahtbügel, zwei Pfosten 1 × 1 × 12,2 hinten,
    Ausleger 1 × 14 × 1 nach vorn (Gesamthöhe 14). Rückseite y = +7,5."""
    b = [quader("Station", -20, -7.5, 0, 40, 15, 0.8)]
    v = 40 * 15 * 0.8
    for i, x in enumerate((-19.5, 19.5)):
        b.append(quader(f"Pfosten{i}", x - 0.5, 6.0, 0.8, 1.0, 1.0, 12.2, op="join", ziele=["Station"]))
        b.append(quader(f"Ausleger{i}", x - 0.5, -6.0, 13.0, 1.0, 13.0, 1.0, op="join", ziele=["Station"]))
        v += 12.2 + 13.0
    n = 0
    for k in range(8):
        for y in (-2.5, 2.5):
            b.append(loch(-17.5 + k * 5, y, 0.8, 0.7, ziele=["Station"], name=f"B{n}"))
            n += 1
    v -= 16 * math.pi * 0.35 ** 2 * 0.8
    bauen("Fahrradstation", b, G, {"Station": v}, koerperfarben={"Station": ANTHR})


def _rahmenplatte(name, breite, hoehe, dicke, felder, koerper="Rahmen", extra=None):
    """Flache Rahmenplatte mit offenen Feldern (Folie dahinter)."""
    form = box(0, 0, breite, hoehe).difference(unary_union([box(*f) for f in felder]))
    if extra is not None:
        form = form.union(extra)
    return flaeche(name, form, dicke, koerper=koerper), form


def fahrraddach():
    b, form = _rahmenplatte("Dach", 41, 16, 1.0, [(0.8, 0.8, 40.2, 15.2)])
    bauen("Fahrradstation_Dach", b, G, {"Rahmen": form.area * 1.0}, ansicht="top", koerperfarben={"Rahmen": ANTHR})


def zza():
    """Zugzielanzeiger 10 breit, 2,2 hoch, 3,2 tief; Anzeige (weiß) als 0,4-Einlage oben, Aufhängelöcher."""
    b = [quader("Gehaeuse", -5, -1.1, 0, 10, 2.2, 3.2),
         quader("Anzeige", -1.3 - 3.1, -0.8, 2.8, 6.2, 1.6, 0.4)]
    b += [skizze("Uhr", "XY", 2.8), kreis([3.2, 0], 1.5), fertig(), extrusion(0.4, "new", "Uhr_E", "Uhr"),
          verbinden("Anzeige", ["Uhr"]), ausschneiden("Gehaeuse", ["Anzeige"], behalten=True)]
    for i, x in enumerate((-3.5, 3.5)):
        b.append(loch(x, 1.1, 1.6, 0.7, 1.5, ziele=["Gehaeuse"], name=f"Haken{i}"))
    v_a = 6.2 * 1.6 * 0.4 + math.pi * 0.75 ** 2 * 0.4
    v_g = 10 * 2.2 * 3.2 - v_a - 2 * math.pi * 0.35 ** 2 * 1.5
    bauen("Zugzielanzeiger", b, G, {"Gehaeuse": v_g, "Anzeige": v_a}, ansicht="top",
          koerperfarben={"Gehaeuse": BLAU, "Anzeige": WEISS})


def pavillon():
    """DB-Wartepavillon 38 × 10 × 16,5: Rückwand, 2 Stirnseiten (flache Rahmen), Dach mit LED-Tasche."""
    # Rückwand: Pfosten 0,8 mit Mitten 0,4 / 12,8 / 25,2 / 37,6, Sockel und Leiste 0,8
    felder = [(0.8, 0.8, 12.4, 14.7), (13.2, 0.8, 24.8, 14.7), (25.6, 0.8, 37.2, 14.7)]
    fahrplan = box(37.2 - 6.5, 3.5, 37.2, 13.5)
    b, form = _rahmenplatte("Rueckwand", 38, 15.5, 0.8, felder)
    b += [quader("Fahrplan", 37.2 - 6.5, 3.5, 0, 6.5, 10, 0.8)]
    bauen("Pavillon_Rueckwand", b, G, {"Rahmen": form.area * 0.8, "Fahrplan": 6.5 * 10 * 0.8}, ansicht="top",
          koerperfarben={"Rahmen": ANTHR, "Fahrplan": GELB})
    b, form = _rahmenplatte("Stirnseite", 10, 15.5, 0.8, [(0.8, 0.8, 9.2, 14.7)])
    bauen("Pavillon_Stirnseite", b, G, {"Rahmen": form.area * 0.8}, ansicht="top", koerperfarben={"Rahmen": ANTHR})
    b = [quader("Dach", 0, 0, 0, 40, 10, 1.0), quader("LED", 5, 3.5, -1, 30, 3, 1.5, op="cut", ziele=["Dach"])]
    bauen("Pavillon_Dach", b, G, {"Dach": 400 - 30 * 3 * 0.5}, koerperfarben={"Dach": ANTHR})


def tram_wartehaus():
    """Rückwand 28 × 16 mit zwei Fenstern 12,5 × 13, Dach 29 × 6,5 × 1, Bank 20 × 2,2 mit zwei Konsolen."""
    b, form = _rahmenplatte("Rueckwand", 28, 16, 0.8, [(1.0, 1.5, 13.5, 14.5), (14.5, 1.5, 27.0, 14.5)])
    bauen("Tramhaus_Rueckwand", b, G, {"Rahmen": form.area * 0.8}, ansicht="top", koerperfarben={"Rahmen": ANTHR})
    bauen("Tramhaus_Dach", [quader("Dach", 0, 0, 0, 29, 6.5, 1.0)], G, {"Dach": 29 * 6.5}, koerperfarben={"Dach": BLAU})
    b = [quader("Bank", 0, 0, 1.2, 20, 2.2, 0.8)]
    for i, x in enumerate((2.0, 17.2)):
        b.append(quader(f"Konsole{i}", x, 0, 0, 0.8, 2.2, 1.2, op="join", ziele=["Bank"]))
    bauen("Tramhaus_Bank", b, G, {"Bank": 20 * 2.2 * 0.8 + 2 * 0.8 * 2.2 * 1.2}, koerperfarben={"Bank": ANTHR})


def automat():
    """Fahrkartenautomat 4 × 2,5 × 11 mit Fase oben vorn, Display als Einlage, Ausgabeschlitz. Vorderseite y = 0."""
    profil = [(0, 0), (2.5, 0), (2.5, 11), (0.8, 11), (0, 9.5)]
    b = profil_yz("Automat", profil, 4.0, koerper="Automat")
    b += [quader("Display", 0.75, 0, 7.2, 2.5, 0.4, 1.2), ausschneiden("Automat", ["Display"], behalten=True),
          quader("Schlitz", 1.25, -1, 4.4, 1.5, 1.2, 0.4, op="cut", ziele=["Automat"])]
    v = Polygon(profil).area * 4 - 2.5 * 0.4 * 1.2 - 1.5 * 0.2 * 0.4
    bauen("Fahrkartenautomat", b, G, {"Automat": v, "Display": 2.5 * 0.4 * 1.2},
          koerperfarben={"Automat": ROTF, "Display": ANTHR})


def laterne():
    """Kandelaber-Laterne: Fuß und Kopf gedruckt, Mast Messingdraht 0,5 × 24."""
    fuss = [(0, 0), (0.75, 0), (0.75, 1.5), (0, 1.5)]
    kopf = [(0, 0), (0.6, 0), (1.0, 2.0), (1.2, 2.0), (1.2, 2.3), (0.4, 2.8), (0, 2.8)]
    b = _drehteil("Fuss", fuss, "Fuss") + [loch(0, 0, 1.5, 0.6, 1.2, ziele=["Fuss"], name="Mastloch_Fuss")]
    kopf_v = [(r, z) for r, z in kopf]
    b += _drehteil("Kopf", kopf_v, "Kopf")
    b += [verschieben(["Kopf"], dx=4.0), loch(4.0, 0, 0, 0.6, 1.0, ziele=["Kopf"], name="Mastloch_Kopf")]
    v_f = _drehvolumen(fuss) - math.pi * 0.3 ** 2 * 1.2
    v_k = _drehvolumen(kopf) - math.pi * 0.3 ** 2 * 1.0
    bauen("Laterne_Fuss_Kopf", b, G, {"Fuss": v_f, "Kopf": v_k}, koerperfarben={"Fuss": ANTHR, "Kopf": ANTHR})


def brunnen():
    profil = [(0, 0), (6, 0), (6, 3), (5.2, 3), (5.2, 0.8), (1, 0.8), (1, 11), (0, 11)]
    b = _drehteil("Brunnen", profil, "Brunnen")
    bauen("Brunnen", b, G, {"Brunnen": _drehvolumen(profil)}, koerperfarben={"Brunnen": "#D9C7A0"})


def litfasssaeule():
    profil = [(0, 0), (3.3, 0), (3.3, 0.8), (3.0, 0.8), (3.0, 18), (3.5, 18), (3.5, 19.5), (3.0, 20), (0, 20)]
    b = _drehteil("Saeule", profil, "Saeule")
    bauen("Litfasssaeule", b, G, {"Saeule": _drehvolumen(profil)}, koerperfarben={"Saeule": "#2E5E3E"})


def tram_steig():
    """Tram-Steig 130 × 19,5 × 2,2 mit Rampen 10 an beiden Enden (gesamt 150), Leitstreifen weiß."""
    profil = [(0, 0), (150, 0), (140, 2.2), (10, 2.2)]
    b = profil_xz("Steig", [(0, 0), (150, 0), (140, 2.2), (10, 2.2)], 19.5, koerper="Steig")
    b += [quader("Leit", 10, 1.5, 1.8, 130, 1.2, 0.5), ausschneiden("Steig", ["Leit"], behalten=True)]
    v = Polygon(profil).area * 19.5 - 130 * 1.2 * 0.4
    bauen("Tram_Steig", b, G, {"Steig": v, "Leit": 130 * 1.2 * 0.5}, koerperfarben={"Steig": HELL, "Leit": WEISS})


def alle():
    doppelbank(); parkbank(); marktstand(); markise(); fahrradstation(); fahrraddach(); zza(); pavillon()
    tram_wartehaus(); automat(); laterne(); brunnen(); litfasssaeule(); tram_steig()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        globals()[sys.argv[1]]()
    else:
        alle()
