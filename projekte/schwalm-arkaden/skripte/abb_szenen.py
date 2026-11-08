"""Alle Montage- und Übersichtsbilder der Bildanleitung."""
import manifold3d as mf
from abbildungen import *

ROT, SAND, GRUEN, BETON, GRAU, WEISS, ANTHR, SILBER = ("#A0472E", "#D9C7A0", "#2F4F3A", "#9A9A96", "#C8C8C4",
                                                       "#F4F4F0", "#4A4A4A", "#A7ADB4")
KACHEL = {"Kachel": ROT, "Sandstein": SAND}
AUF = RX(90)      # flach gedruckte Platte (Ansicht oben) aufrichten: Ansicht zeigt nach −Y
DACH3D = ABB.parent / "teile" / "SA_09_Dach" / "Dach_Zusammenbau_Einbaulage.3mf"


def _hilfsbox(name, x0, y0, z0, x1, y1, z1):
    """Einfacher Quader als 3MF (Montagebrett, Boden)."""
    m = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    m.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    p = ABB / f"_{name}.3mf"
    sz = trimesh.Scene()
    sz.add_geometry(m, geom_name=name, node_name=name)
    sz.export(p)
    return str(p)


def arkade():
    t = []
    for k in range(3):
        t.append(("SA_01_Arkaden/Bogenkachel_42.3mf", kette(T(42 * k, 0, 0), AUF), KACHEL, True))
        t.append(("SA_01_Arkaden/Laibung_60.3mf", kette(T(42 * k + 21, 60, 22), RX(90)), ROT, True))
    t.append(("SA_02_Laeden/Ladeneinsatz_Kiosk.3mf", T(42 + 3.2, 1.0, 0),
              {"Laden": "#E8E0CC", "Holz": "#7A5230", "Schrift": "#FFFFFF"}, True))
    t.append(("SA_02_Laeden/Ladenfront.3mf", kette(T(84 + 3.2, 2.5, 0), AUF), "#7A5230", True))
    t.append(("SA_02_Laeden/Faecher_Oberlicht.3mf", kette(T(84 + 21, 1.5, 24), AUF), "#F2F2F2", True))
    return szene("M_arkade", t, kamera([63, 20, 28], -25, 12, 150))


def bahnsteig():
    t = [("SA_03_Bahnsteig/Bahnsteig_C2_Ende_200.3mf", T(0, 0, 0), {"Bahnsteig": GRAU, "Weiss": WEISS}, True),
         ("SA_03_Bahnsteig/Bahnsteig_C1_Normal_200.3mf", T(215, 0, 0), {"Bahnsteig": GRAU, "Weiss": WEISS}, True),
         ("SA_03_Bahnsteig/Bahnsteig_C3_Aufgang_200.3mf", T(430, 0, 0), {"Bahnsteig": GRAU, "Weiss": WEISS}, True)]
    return szene("M_bahnsteig", t, kamera([315, 22, 0], -28, 30, 560))


def bahnsteig_steck():
    t = [("SA_03_Bahnsteig/Bahnsteig_C2_Ende_200.3mf", T(0, 0, 0), {"Bahnsteig": GRAU, "Weiss": WEISS}, True),
         ("SA_03_Bahnsteig/Bahnsteig_C1_Normal_200.3mf", T(210, 0, 0), {"Bahnsteig": GRAU, "Weiss": WEISS}, True)]
    return szene("M_bahnsteig_steck", t, kamera([205, 22, 3], -55, 25, 60))


def treppe():
    t = [("SA_04_Aufgaenge/Treppe.3mf", T(0, 0, 0), "#9C9C98", True),
         ("SA_04_Aufgaenge/Treppenwange.3mf", kette(T(0, -8, 0), AUF), ANTHR, 0.4),
         ("SA_04_Aufgaenge/Treppenwange.3mf", kette(T(0, 18.8, 0), AUF), ANTHR, 0.4),
         ("SA_04_Aufgaenge/Treppenstuetze.3mf", kette(T(63, 4, -12), RY(-90)), GRAU, True),
         ("SA_04_Aufgaenge/Treppenstuetze.3mf", kette(T(73, 4, -12), RY(-90)), GRAU, True)]
    return szene("M_treppe", t, kamera([67, 5, 30], -29, 17, 230))


def rolltreppe():
    t = [("SA_04_Aufgaenge/Rolltreppe.3mf", T(0, 0, 0), {"Wanne": "#6A6A6A", "Stufenband": SILBER}, True),
         ("SA_04_Aufgaenge/Rolltreppenwange.3mf", kette(T(0, -8, 0), AUF), ANTHR, 0.4),
         ("SA_04_Aufgaenge/Rolltreppenwange.3mf", kette(T(0, 16, 0), AUF), ANTHR, 0.4)]
    return szene("M_rolltreppe", t, kamera([67, 4, 30], -29, 17, 230))


def aufzug():
    a = "SA_04_Aufgaenge/"
    e = 14.0     # Explosionsabstand
    t = [(a + "Aufzug_Boden.3mf", T(0, 0, -0.8 - e), ANTHR, True),
         (a + "Aufzug_Laengsseite.3mf", kette(T(0, 0.8 - e, 0), AUF), ANTHR, True),
         (a + "Aufzug_Laengsseite.3mf", kette(T(0, 12 + e, 0), AUF), ANTHR, True),
         (a + "Aufzug_Schmalseite_Tuer_unten.3mf", kette(T(-e, 0.8, 0), RZ(90), AUF), ANTHR, True),
         (a + "Aufzug_Schmalseite_Tuer_oben.3mf", kette(T(14.2 + e, 0.8, 0), RZ(90), AUF), ANTHR, True),
         (a + "Aufzug_Kabine.3mf", kette(T(1, 11, 2), AUF), SILBER, True),
         (a + "Aufzug_Dach.3mf", T(0, 0, 83 + e), ANTHR, True)]
    return szene("M_aufzug", t, kamera([7.5, 6, 42], -35, 15, 190), breite=1000, hoehe=1100)


def bruecke():
    s = "SA_05_Stahl/"
    t = []
    for y, dreh in ((0.0, False), (190.0, True)):
        m = kette(T(0, y, 43), AUF) if not dreh else kette(T(55, y + 3.0, 43), RZ(180), AUF)
        t.append((s + "Aussentraeger_3_Felder.3mf", m, GRUEN, True))
        for x in (0.5, 54.5):
            t.append((s + "Gitterstuetze.3mf", T(x, y - 1.5 if not dreh else y + 1.5, 0), GRUEN, True))
    t.append((s + "Fahrbahnplatte_54.3mf", kette(T(0.5, 190, 55), RX(180)), BETON, True))
    return szene("M_bruecke", t, kamera([27, 95, 30], -60, 8, 360))


def schwalm():
    t = [("SA_05_Stahl/Bogenrippe_Schwalm.3mf", kette(T(0, 0, 0), AUF), GRUEN, True),
         ("SA_05_Stahl/Bogenrippe_Schwalm.3mf", kette(T(0, 60, 0), AUF), GRUEN, False)]
    return szene("M_schwalm", t, kamera([0, 30, 25], -25, 15, 200))


def betonwand():
    t = []
    for k in range(5):
        t.append(("SA_06_Beton/Betonwand_Feld.3mf", kette(T(45 * k, 0, 0), AUF), BETON, True))
    t.append(("SA_06_Beton/Kappe_225.3mf", kette(T(0, -3.5, 61), RZ(0)), GRAU, True))
    return szene("M_betonwand", t, kamera([112, 0, 30], -25, 15, 270))


def haus():
    st = "SA_08_Stadt/"
    t = [(st + "Haus_Fassade_34.3mf", AUF, {"Putz": "#D8C3A0", "Weiss": "#F2EFE6", "Tuer": "#3A3A3A"}, True),
         (st + "Haus_Seitenwand.3mf", kette(RZ(90), AUF), "#D8C3A0", True),
         (st + "Haus_Seitenwand.3mf", kette(T(34, 0, 0), RZ(90), AUF), "#D8C3A0", True),
         (st + "Haus_Mansarddach_34.3mf", T(0, 0, 100), "#5B5E66", True)]
    return szene("M_haus", t, kamera([17, 30, 62], -32, 12, 230), breite=1000, hoehe=1100)


# ---------------------------------------------------------------------------
# Dach
# ---------------------------------------------------------------------------
def _dach_teile(namen):
    return (str(DACH3D), namen)


ALLE_A = [f"A{i}" for i in range(-4, 5)]
ALLE_B = [f"B{i}" for i in range(-4, 5)]
ENDEN = ["B5", "B6", "A-5", "A-6", "SO", "SW"]


def _grundaufbau(neu):
    brett = _hilfsbox("Brett", -150, -320, -4, 150, 320, -1)
    t = [(brett, T(), "#C9A46A", True)]
    for x in (-91.5, 91.5):
        t.append(("SA_09_Dach/Fussschwelle_1.3mf", kette(T(x, 0, -1), RZ(90)), SILBER, neu))
        t.append(("SA_09_Dach/Fussschwelle_2.3mf", kette(T(x, 0, -1), RZ(90)), SILBER, neu))
    for y in (-175, -87.5, 0, 87.5, 175):
        t.append(("SA_09_Dach/Montagespant.3mf", kette(T(0, y + 2, 0), AUF), "#E0A040", neu))
    return t


K_DACH = kamera([0, 0, 50], -38, 24, 760)


def dach_schritte():
    bilder = []
    t = _grundaufbau(True)
    bilder.append(szene("D1_brett", t, K_DACH, blass=0.35))
    t = _grundaufbau(False) + [(_dach_teile(ALLE_A), T(), SILBER, True)]
    bilder.append(szene("D2_boegen_A", t, K_DACH, blass=0.35))
    t = _grundaufbau(False) + [(_dach_teile(ALLE_A), T(), SILBER, False), (_dach_teile(ALLE_B), T(), "#6F7F95", True)]
    bilder.append(szene("D3_boegen_B", t, K_DACH, blass=0.35))
    t = _grundaufbau(False) + [(_dach_teile(ALLE_A + ALLE_B), T(), SILBER, False),
                               (_dach_teile(ENDEN), T(), "#C0504D", True)]
    bilder.append(szene("D4_enden", t, K_DACH, blass=0.35))
    fuss = []
    for x in (-91.5, 91.5):
        fuss.append(("SA_09_Dach/Fussschwelle_1.3mf", kette(T(x, 0, -1), RZ(90)), SILBER, True))
        fuss.append(("SA_09_Dach/Fussschwelle_2.3mf", kette(T(x, 0, -1), RZ(90)), SILBER, True))
    t = fuss + [(_dach_teile(ALLE_A + ALLE_B + ENDEN), T(), SILBER, True)]
    bilder.append(szene("D5_fertig", t, kamera([0, 0, 45], -30, 18, 680)))
    # Nahaufnahme einer Kreuzung (A0 / B1 bei x = +77,3, z = 68,7)
    t = [(_dach_teile(["A0", "A1"]), T(), SILBER, True), (_dach_teile(["B1", "B0"]), T(), "#6F7F95", True)]
    bilder.append(szene("D6_kreuzung", t, kamera([77.3, 25, 68.7], 75, 5, 40)))
    # Fußknoten
    t = [(_dach_teile(["A0"]), T(), SILBER, True), (_dach_teile(["B0"]), T(), "#6F7F95", True),
         ("SA_09_Dach/Fussschwelle_1.3mf", kette(T(91.5, 0, -1), RZ(90)), "#E0A040", True)]
    bilder.append(szene("D7_fuss", t, kamera([91.5, 0, 5], 70, 15, 38)))
    return bilder


def dach_uebersicht():
    return szene("D0_dach", [(_dach_teile(ALLE_A + ALLE_B + ENDEN), T(), SILBER, True)], kamera([0, 0, 50], -32, 20, 650))


if __name__ == "__main__":
    import sys
    namen = sys.argv[1:] or ["arkade", "bahnsteig", "bahnsteig_steck", "treppe", "rolltreppe", "aufzug", "bruecke",
                             "schwalm", "betonwand", "haus", "dach_uebersicht", "dach_schritte"]
    for n in namen:
        print(globals()[n]())
