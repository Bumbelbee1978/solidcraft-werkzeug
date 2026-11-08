"""
SA_09 Dach: Rautengitter-Stahldach aus flach gedruckten Einzelbögen.

Geometrie (Ursprung Dachmitte am Fuß, X quer, Y längs, Z hoch):
  Leitkurve 3-Punkt-Bogen (±91,5 | 0) und (0 | 110) -> Mittelpunkt z_c = 16,944, R = 93,056.
  Jeder Bogen = Mantelschale (R ± 2, entlang Y) ∩ Scheibe 4 mm dick in einer um ±20° geneigten Ebene.
  Bogen A (Paar i): Ebene y = 50·i + z·tan 20°, Bogen B: y = 50·i − z·tan 20°.
  Überblattung: A behält an jeder Kreuzung die innere Hälfte (ρ < R), B die äußere.
  H-Profil: Taschen 2,4 breit, 1,1 tief auf beiden flachen Seiten (Flansche 0,8, Steg 1,8).
Jeder Bogen wird zuletzt flach auf das Druckbett gedreht (Ebene -> XY, Dicke 0 … 4).
"""
import math
from sa_basis import *

G = "SA_09_Dach"
ZC = (110 ** 2 - 91.5 ** 2) / 220            # 16,944
R = 110 - ZC                                  # 93,056
WINKEL = 20.0
RASTER = 50.0
KRAG = math.degrees(math.atan(75 / 110))      # 34,29°
DICKE = 4.0
TASCHE_B, TASCHE_T = 2.4, 1.1
SPIEL = 0.1                                   # Spiel der Überblattung (Scheibe ± 0,1, radial ± 0,05)
SILBER = "#A7ADB4"


def schale(name, r_i, r_a, laenge=900.0):
    """Massive Mantelschale zwischen r_i und r_a (Mittelpunkt (0 | z_c)), z ≥ 0, entlang Y extrudiert."""
    xa, xi = math.sqrt(r_a ** 2 - ZC ** 2), math.sqrt(max(r_i, ZC + 0.01) ** 2 - ZC ** 2)
    return [skizze(name, "XZ", offset=-laenge / 2),
            linie([[-xa, 0], [-xi, 0]]),
            bogen3([-xi, 0], [xi, 0], [0, -(ZC + r_i)]),
            linie([[xi, 0], [xa, 0]]),
            bogen3([xa, 0], [-xa, 0], [0, -(ZC + r_a)]),
            fertig(), extrusion(laenge, "new", name + "_E", name)]


def scheibe(name, y0, phi, w0=-DICKE / 2, w1=DICKE / 2):
    """Ebene Scheibe w0 … w1 (Abstand zur Bogenebene), Ebene durch (y0 | z 0), um phi (Grad) um X gekippt.
    phi < 0: y wächst mit z (Bogen A), phi > 0: Bogen B."""
    return [quader(name, -150, w0, -40, 300, w1 - w0, 240),
            drehen([name], [1, 0, 0], phi),
            verschieben([name], dy=y0)]


def _phi(art):
    return -WINKEL if art == "A" else WINKEL


def bogen_befehle(art, i, name, kerben=True):
    """Befehle für einen vollständigen Bogen 'art' (A/B) im Paar i, als Körper 'name' in Einbaulage."""
    y0, phi = RASTER * i, _phi(art)
    b = schale(f"{name}_Sch", R - 2, R + 2)
    b += scheibe(name, y0, phi)
    b += [schnittmenge(name, [f"{name}_Sch"])]
    # H-Taschen: Schale R ± 1,2 geschnitten mit den beiden äußeren Lagen der Scheibe
    b += schale(f"{name}_TS", R - TASCHE_B / 2, R + TASCHE_B / 2)
    b += scheibe(f"{name}_T1", y0, phi, DICKE / 2 - TASCHE_T, DICKE / 2 + 2)
    b += scheibe(f"{name}_T2", y0, phi, -DICKE / 2 - 2, -DICKE / 2 + TASCHE_T)
    b += [verbinden(f"{name}_T1", [f"{name}_T2"]), schnittmenge(f"{name}_T1", [f"{name}_TS"]),
          ausschneiden(name, [f"{name}_T1"])]
    if kerben:
        b += kerben_befehle(art, i, name)
    # Fußbohrungen Ø 1,1 senkrecht (Hälfte in A, Hälfte in B)
    for s, x in (("L", -91.5), ("R", 91.5)):
        b.append(zylinder(f"{name}_Fuss{s}", x, y0, -1, 1.1, 7.0, op="cut", ziele=[name]))
    return b


def kerben_befehle(art, i, name, partner=None):
    """Überblattungen: A verliert die äußere Hälfte dort, wo B(i) und B(i+1) liegen; B die innere, wo A(i), A(i−1)."""
    if partner is None:
        partner = [i, i + 1] if art == "A" else [i, i - 1]
    andere = "B" if art == "A" else "A"
    b = []
    if art == "A":
        b += schale(f"{name}_KS", R - SPIEL / 2, R + 6)
    else:
        b += schale(f"{name}_KS", R - 6, R + SPIEL / 2)
    teile = []
    for k, j in enumerate(partner):
        nm = f"{name}_K{k}"
        b += scheibe(nm, RASTER * j, _phi(andere), -DICKE / 2 - SPIEL, DICKE / 2 + SPIEL)
        teile.append(nm)
    if len(teile) > 1:
        b.append(verbinden(teile[0], teile[1:]))
    b += [schnittmenge(teile[0], [f"{name}_KS"]), ausschneiden(name, [teile[0]])]
    return b


def flach_legen(name, y0, phi):
    """Bogen aus der Einbaulage auf das Druckbett drehen: Ebene -> XY, Dicke z 0 … 4."""
    return [verschieben([name], dy=-y0), drehen([name], [1, 0, 0], -phi), drehen([name], [1, 0, 0], 90),
            verschieben([name], dz=DICKE / 2)]


# ---------------------------------------------------------------------------
# Vergleichsmodell mit manifold3d (unabhängiger Rechenkern) für Volumen und Kollisionsprüfung
# ---------------------------------------------------------------------------
import manifold3d as mf


def m_schale(r_i, r_a, laenge=900.0):
    ring = mf.CrossSection.circle(r_a, 720) - mf.CrossSection.circle(max(r_i, 0.1), 720)
    ring = ring.translate([0, ZC]) ^ mf.CrossSection.square([400, 300]).translate([-200, 0])
    return mf.Manifold.extrude(ring, laenge).rotate([90, 0, 0]).translate([0, laenge / 2, 0])


def m_scheibe(y0, phi, w0=-DICKE / 2, w1=DICKE / 2):
    return mf.Manifold.cube([300, w1 - w0, 240]).translate([-150, w0, -40]).rotate([phi, 0, 0]).translate([0, y0, 0])


def m_bogen(art, i, kerben=True):
    y0, phi = RASTER * i, _phi(art)
    m = m_schale(R - 2, R + 2) ^ m_scheibe(y0, phi)
    tasche = m_schale(R - TASCHE_B / 2, R + TASCHE_B / 2) ^ (
        m_scheibe(y0, phi, DICKE / 2 - TASCHE_T, DICKE / 2 + 2) + m_scheibe(y0, phi, -DICKE / 2 - 2, -DICKE / 2 + TASCHE_T))
    m = m - tasche
    if kerben:
        m = m - m_kerbe(art, [i, i + 1] if art == "A" else [i, i - 1])
    for x in (-91.5, 91.5):
        m = m - mf.Manifold.cylinder(7.0, 0.55, 0.55, 64).translate([x, y0, -1])
    return m


def m_kerbe(art, partner):
    andere = "B" if art == "A" else "A"
    ks = m_schale(R - SPIEL / 2, R + 6) if art == "A" else m_schale(R - 6, R + SPIEL / 2)
    sch = mf.Manifold.batch_boolean([m_scheibe(RASTER * j, _phi(andere), -DICKE / 2 - SPIEL, DICKE / 2 + SPIEL)
                                     for j in partner], mf.OpType.Add)
    return ks ^ sch


# ---------------------------------------------------------------------------
# Teile
# ---------------------------------------------------------------------------
Y_STIRN = 4 * RASTER                         # 200: letzter Fußknoten


def _aussen_scheibe(name, seite):
    """Bereich jenseits der Innenseite des Stirnbogens (wird von Teilbögen/Kappen weggeschnitten)."""
    if seite == "ost":
        return scheibe(name, Y_STIRN, -KRAG, -DICKE / 2 - 0.05, 400)
    return scheibe(name, -Y_STIRN, KRAG, -400, DICKE / 2 + 0.05)


def _m_aussen(seite):
    if seite == "ost":
        return m_scheibe(Y_STIRN, -KRAG, -DICKE / 2 - 0.05, 400)
    return m_scheibe(-Y_STIRN, KRAG, -400, DICKE / 2 + 0.05)


def teilbogen_befehle(art, i, name, seite, partner):
    """Teilbogen/Kappe: Bogen ohne Füße, am Stirnbogen abgeschnitten; Kerben nur zu den 'partner'-Bögen."""
    y0, phi = RASTER * i, _phi(art)
    b = schale(f"{name}_Sch", R - 2, R + 2)
    b += scheibe(name, y0, phi)
    b += [schnittmenge(name, [f"{name}_Sch"])]
    b += schale(f"{name}_TS", R - TASCHE_B / 2, R + TASCHE_B / 2)
    b += scheibe(f"{name}_T1", y0, phi, DICKE / 2 - TASCHE_T, DICKE / 2 + 2)
    b += scheibe(f"{name}_T2", y0, phi, -DICKE / 2 - 2, -DICKE / 2 + TASCHE_T)
    b += [verbinden(f"{name}_T1", [f"{name}_T2"]), schnittmenge(f"{name}_T1", [f"{name}_TS"]),
          ausschneiden(name, [f"{name}_T1"])]
    if partner:
        b += kerben_befehle(art, i, name, partner)
    b += _aussen_scheibe(f"{name}_Aussen", seite) + [ausschneiden(name, [f"{name}_Aussen"])]
    return b


def m_teilbogen(art, i, seite, partner):
    y0, phi = RASTER * i, _phi(art)
    m = m_schale(R - 2, R + 2) ^ m_scheibe(y0, phi)
    tasche = m_schale(R - TASCHE_B / 2, R + TASCHE_B / 2) ^ (
        m_scheibe(y0, phi, DICKE / 2 - TASCHE_T, DICKE / 2 + 2) + m_scheibe(y0, phi, -DICKE / 2 - 2, -DICKE / 2 + TASCHE_T))
    m = m - tasche
    if partner:
        m = m - m_kerbe(art, partner)
    return m - _m_aussen(seite)


def stirnbogen_befehle(seite, name):
    """Stirnbogen in der um 34,29° geneigten Ebene durch den letzten Fußknoten; dort frei geschnitten."""
    y0, phi = (Y_STIRN, -KRAG) if seite == "ost" else (-Y_STIRN, KRAG)
    b = schale(f"{name}_Sch", R - 2, R + 2)
    b += scheibe(name, y0, phi)
    b += [schnittmenge(name, [f"{name}_Sch"])]
    b += schale(f"{name}_TS", R - TASCHE_B / 2, R + TASCHE_B / 2)
    b += scheibe(f"{name}_T1", y0, phi, DICKE / 2 - TASCHE_T, DICKE / 2 + 2)
    b += scheibe(f"{name}_T2", y0, phi, -DICKE / 2 - 2, -DICKE / 2 + TASCHE_T)
    b += [verbinden(f"{name}_T1", [f"{name}_T2"]), schnittmenge(f"{name}_T1", [f"{name}_TS"]),
          ausschneiden(name, [f"{name}_T1"])]
    # Fußknoten: die beiden letzten Bögen A und B (mit Spiel) herausschneiden
    i = 4 if seite == "ost" else -4
    b += schale(f"{name}_WS", R - 2 - SPIEL, R + 2 + SPIEL)
    b += scheibe(f"{name}_WA", RASTER * i, _phi("A"), -DICKE / 2 - SPIEL, DICKE / 2 + SPIEL)
    b += scheibe(f"{name}_WB", RASTER * i, _phi("B"), -DICKE / 2 - SPIEL, DICKE / 2 + SPIEL)
    b += [verbinden(f"{name}_WA", [f"{name}_WB"]), schnittmenge(f"{name}_WA", [f"{name}_WS"]),
          ausschneiden(name, [f"{name}_WA"])]
    # winzige Splitter (< 0,1 mm³) direkt am Fußpunkt entfernen
    b.append(entfernen([f"{name} ({k})" for k in range(1, 5)]))
    return b, y0, phi


def m_stirnbogen(seite):
    y0, phi = (Y_STIRN, -KRAG) if seite == "ost" else (-Y_STIRN, KRAG)
    m = m_schale(R - 2, R + 2) ^ m_scheibe(y0, phi)
    tasche = m_schale(R - TASCHE_B / 2, R + TASCHE_B / 2) ^ (
        m_scheibe(y0, phi, DICKE / 2 - TASCHE_T, DICKE / 2 + 2) + m_scheibe(y0, phi, -DICKE / 2 - 2, -DICKE / 2 + TASCHE_T))
    m = m - tasche
    i = 4 if seite == "ost" else -4
    werkzeug = m_schale(R - 2 - SPIEL, R + 2 + SPIEL) ^ (
        m_scheibe(RASTER * i, _phi("A"), -DICKE / 2 - SPIEL, DICKE / 2 + SPIEL) +
        m_scheibe(RASTER * i, _phi("B"), -DICKE / 2 - SPIEL, DICKE / 2 + SPIEL))
    ys = 190.0 if seite == "ost" else -199.5
    return m - werkzeug - mf.Manifold.cube([200, 9.5, 1.3]).translate([-100, ys, -1])


def _hilfskoerper_weg(befehle, name):
    """Alle Hilfskörper (Name beginnt mit name + '_') am Ende entfernen."""
    hilfs = sorted({c["params"].get("body_name") for c in befehle
                    if c["params"].get("body_name", "").startswith(name + "_")})
    # Körper, die durch combine verbraucht wurden, existieren nicht mehr -> nur noch vorhandene entfernen
    return hilfs


TEILE = {
    # Name: (Art, Paar i, Seite/None, Partner für Kerben, Stückzahl, Beschreibung)
    "Bogen_A": ("A", 0, None, None, 9, "voller Bogen, Kerben außen"),
    "Bogen_B": ("B", 0, None, None, 9, "voller Bogen, Kerben innen"),
    "Teilbogen_B5_Ost": ("B", 5, "ost", [4], 1, "beginnt auf Höhe 47,9, Kerben innen"),
    "Kappe_B6_Ost": ("B", 6, "ost", [], 1, "beginnt auf Höhe 95,7"),
    "Teilbogen_A5_West": ("A", -5, "west", [-4], 1, "beginnt auf Höhe 47,9, Kerben außen"),
    "Kappe_A6_West": ("A", -6, "west", [], 1, "beginnt auf Höhe 95,7"),
}


def baue_bogenteil(name, flach=True):
    art, i, seite, partner, stueck, text_ = TEILE[name]
    if seite is None:
        b = bogen_befehle(art, i, name)
        m = m_bogen(art, i)
    else:
        b = teilbogen_befehle(art, i, name, seite, partner)
        m = m_teilbogen(art, i, seite, partner)
    y0, phi = RASTER * i, _phi(art)
    b += _aufraeumen(b, name)
    if flach:
        b += flach_legen(name, y0, phi)
    return bauen(name, b, G, {name: m.volume()}, ansicht="top", koerperfarben={name: SILBER},
                 info={"stueck": stueck, "text": text_})


def baue_stirnbogen(seite, flach=True):
    name = f"Stirnbogen_{seite.capitalize()}"
    b, y0, phi = stirnbogen_befehle(seite, name)
    b += _aufraeumen(b, name)
    if flach:
        b += flach_legen(name, y0, phi)
    return bauen(name, b, G, {name: m_stirnbogen(seite).volume()}, ansicht="top", koerperfarben={name: SILBER},
                 info={"stueck": 1})


def _aufraeumen(befehle, name):
    """Übrig gebliebene Hilfskörper (Schalen) entfernen: Schalen werden bei 'schnittmenge' als Werkzeug verbraucht,
    nur Werkzeuge mit keep_tools bleiben. Hier bleiben keine übrig – Platzhalter für spätere Erweiterungen."""
    return []


def fussschwellen():
    """Fußschwelle in zwei Stücken (400 mm passt nicht auf das 256er-Bett): Teilung bei x = 25 zwischen zwei
    Löchern. Löcher Ø 1,1 im 50-mm-Raster, Stück 1 von −205 bis 25, Stück 2 von 25 bis 205."""
    for nr, (x0, x1) in enumerate(((-205.0, 25.0), (25.0, 205.0)), start=1):
        name = f"Fussschwelle_{nr}"
        b = [quader(name, x0, -2, 0, x1 - x0, 4, 1.0)]
        loecher = [x for x in range(-200, 201, 50) if x0 < x < x1]
        for k, x in enumerate(loecher):
            b.append(zylinder(f"L{k}", x, 0, -1, 1.1, 3, op="cut", ziele=[name]))
        v = (x1 - x0) * 4 - len(loecher) * math.pi * 0.55 ** 2
        bauen(name, b, G, {name: v}, ansicht="top", koerperfarben={name: SILBER},
              info={"stueck": 2, "loecher": len(loecher)})


def montagespant():
    """Montagespant: Bogenband zwischen R − 12 und R − 2,2 (0,2 Luft zur Bogeninnenseite), unten ein
    Fußsteg 160 × 4, der 1 mm unter die Fußebene reicht (steht auf dem Brett, die Fußschwellen sind 1 mm dick).
    In der XY-Ebene gezeichnet (flach), 4 dick."""
    ra, ri = R - 2.2, R - 12
    xa, xi = math.sqrt(ra ** 2 - ZC ** 2), math.sqrt(ri ** 2 - ZC ** 2)
    b = [skizze("Spant"), linie([[-xa, 0], [-xi, 0]]), bogen3([-xi, 0], [xi, 0], [0, ZC + ri]),
         linie([[xi, 0], [xa, 0]]), bogen3([xa, 0], [-xa, 0], [0, ZC + ra]), fertig(),
         extrusion(4.0, "new", "Spant_E", "Montagespant"),
         quader("Steg", -80, -1, 0, 160, 4, 4, op="join", ziele=["Montagespant"])]
    ring = (mf.CrossSection.circle(ra, 2000) - mf.CrossSection.circle(ri, 2000)).translate([0, ZC]) ^ \
        mf.CrossSection.square([400, 300]).translate([-200, 0])
    v = ring.area() * 4 + 160 * 4 * 4 - (ring ^ mf.CrossSection.square([160, 4]).translate([-80, -1])).area() * 4
    bauen("Montagespant", b, G, {"Montagespant": v}, ansicht="top", koerperfarben={"Montagespant": "#E0A040"},
          info={"stueck": 5})


def alle():
    for name in TEILE:
        baue_bogenteil(name)
    baue_stirnbogen("ost")
    baue_stirnbogen("west")
    fussschwellen()
    montagespant()


def zusammenbau_pruefen(ausgabe=None):
    """Alle Dachteile in Einbaulage mit manifold erzeugen, paarweise Überschneidungen messen und als 3MF speichern."""
    import trimesh
    import numpy as np
    teile = {}
    for i in range(-4, 5):
        teile[f"A{i}"] = m_bogen("A", i)
        teile[f"B{i}"] = m_bogen("B", i)
    teile["B5"] = m_teilbogen("B", 5, "ost", [4])
    teile["B6"] = m_teilbogen("B", 6, "ost", [])
    teile["A-5"] = m_teilbogen("A", -5, "west", [-4])
    teile["A-6"] = m_teilbogen("A", -6, "west", [])
    teile["SO"] = m_stirnbogen("ost")
    teile["SW"] = m_stirnbogen("west")
    namen = list(teile)
    schlimmste = 0.0
    for a in range(len(namen)):
        for c in range(a + 1, len(namen)):
            ba, bc = teile[namen[a]].bounding_box(), teile[namen[c]].bounding_box()
            if ba[3] < bc[0] or bc[3] < ba[0] or ba[4] < bc[1] or bc[4] < ba[1]:
                continue
            v = (teile[namen[a]] ^ teile[namen[c]]).volume()
            if v > 1e-3:
                print(f"  Überschneidung {namen[a]} / {namen[c]}: {v:.3f} mm³")
            schlimmste = max(schlimmste, v)
    print(f"Zusammenbau: {len(namen)} Teile, größte Überschneidung {schlimmste:.4f} mm³")
    if ausgabe:
        szene = trimesh.Scene()
        for n, m in teile.items():
            g = m.to_mesh()
            szene.add_geometry(trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts),
                                               process=False), geom_name=n, node_name=n)
        szene.export(ausgabe)
    return teile


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "pruefen":
        zusammenbau_pruefen(str(WURZEL / G / "Dach_Zusammenbau_Einbaulage.3mf"))
    else:
        alle()
