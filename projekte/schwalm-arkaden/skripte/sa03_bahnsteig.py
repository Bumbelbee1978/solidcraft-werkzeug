"""
SA_03 Bahnsteig: Normalstück C1 (200), Kurzstück C1k (103), Endstücke C2 (200, Rampe am Anfang) und
C2k (97, Rampe am Ende), Aufgangsstück C3 (200) mit Treppenauge und Aufzugsöffnung.
Länge in X, Breite 45 in Y, Höhe 6 in Z. Ursprung: Anfang (Taschenseite), Gleisseite y = 0, Boden.
Handrechnung: Vergleichsmodell mit manifold3d aus denselben Grundkörpern.
"""
import manifold3d as mf
from sa_basis import *

G = "SA_03_Bahnsteig"
BR, HO = 45.0, 6.0
GRAU, WEISS = "#C8C8C4", "#F4F4F0"
LINIEN = [(5.0, 5.8), (BR - 5.8, BR - 5.0)]               # Sicherheitslinien, bündig
LEIT = [(6.6, 8.6), (BR - 8.6, BR - 6.6)]                 # Leitstreifen, 0,1 erhaben


def _m_box(x0, y0, z0, x1, y1, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def _rampe_profil(laenge, am_ende):
    """Keil, der oben weggeschnitten wird: Rampe 1 : 5 über 30 mm."""
    if am_ende:
        return [[laenge, HO + 1], [laenge - 30, HO], [laenge + 1, -0.2], [laenge + 1, HO + 1]]
    return [[0, HO + 1], [30, HO], [-1, -0.2], [-1, HO + 1]]


def bahnsteig(name, laenge, zapfen=True, tasche=True, rampe=None, aufgang=False):
    b = [quader("Bahnsteig", 0, 0, 0, laenge, BR, HO),
         quader("Krag1", -1, -1, -1, laenge + 2, 1.5 + 1, 3 + 1, op="cut", ziele=["Bahnsteig"]),
         quader("Krag2", -1, BR - 1.5, -1, laenge + 2, 1.5 + 1, 3 + 1, op="cut", ziele=["Bahnsteig"])]
    # weiße Einlage: Linien bündig (z 5,6–6,0), Leitstreifen 0,1 erhaben (z 5,6–6,1)
    weiss = []
    for i, (y0, y1) in enumerate(LINIEN):
        b.append(quader(f"Linie{i}", 0, y0, HO - 0.4, laenge, y1 - y0, 0.4))
        weiss.append(f"Linie{i}")
    for i, (y0, y1) in enumerate(LEIT):
        b.append(quader(f"Leit{i}", 0, y0, HO - 0.4, laenge, y1 - y0, 0.5))
        weiss.append(f"Leit{i}")
    b += [verbinden(weiss[0], weiss[1:]), umbenennen(weiss[0], "Weiss"),
          ausschneiden("Bahnsteig", ["Weiss"], behalten=True)]
    if zapfen:
        b.append(quader("Zapfen", laenge - 0.5, BR / 2 - 2, 1.0, 4.5, 4.0, 4.0, op="join", ziele=["Bahnsteig"]))
    if tasche:
        b.append(quader("Tasche", -1, BR / 2 - 2.2, 0.8, 4.2 + 1, 4.4, 4.4, op="cut", ziele=["Bahnsteig"]))
    if rampe:
        pk = _rampe_profil(laenge, rampe == "ende")
        b += profil_xz("Rampe", pk, BR + 2, op="cut", offset=-1.0)
        b[-1]["params"]["targets"] = ["Bahnsteig", "Weiss"]
    loecher = []
    if aufgang:
        auge = (6.0, BR / 2 - 9, 6.0 + 65, BR / 2 + 9)
        lift = (141.0, BR / 2 - 6, 141.0 + 15, BR / 2 + 6)
        for nm, (x0, y0, x1, y1) in (("Treppenauge", auge), ("Aufzugsoeffnung", lift)):
            b.append(quader(nm, x0, y0, -1, x1 - x0, y1 - y0, HO + 2, op="cut", ziele=["Bahnsteig"]))
        # Geländerlöcher Ø 0,7 (Messingdraht 0,5) alle 8 mm entlang der langen Kanten des Treppenauges
        x = auge[0] + 4
        while x < auge[2] - 1:
            for y in (auge[1] - 0.6, auge[3] + 0.6):
                loecher.append((x, y))
            x += 8
        for i, (x, y) in enumerate(loecher):
            b.append(loch(x, y, HO, 0.7, 3.0, ziele=["Bahnsteig"], name=f"Gel{i}"))
    # Vergleichsmodell
    m = _m_box(0, 0, 0, laenge, BR, HO) - _m_box(-1, -1, -1, laenge + 1, 1.5, 3) - _m_box(-1, BR - 1.5, -1, laenge + 1, BR + 1, 3)
    w = mf.Manifold.batch_boolean([_m_box(0, y0, HO - 0.4, laenge, y1, HO) for y0, y1 in LINIEN] +
                                  [_m_box(0, y0, HO - 0.4, laenge, y1, HO + 0.1) for y0, y1 in LEIT], mf.OpType.Add)
    m = m - w
    if zapfen:
        m = m + _m_box(laenge - 0.5, BR / 2 - 2, 1, laenge + 4, BR / 2 + 2, 5)
    if tasche:
        m = m - _m_box(-1, BR / 2 - 2.2, 0.8, 4.2, BR / 2 + 2.2, 5.2)
    if rampe:
        pk = _rampe_profil(laenge, rampe == "ende")
        pz = [(x, z) for x, z in pk]
        flaeche2 = sum(pz[i][0] * pz[(i + 1) % len(pz)][1] - pz[(i + 1) % len(pz)][0] * pz[i][1] for i in range(len(pz)))
        if flaeche2 < 0:
            pz = pz[::-1]                      # gegen den Uhrzeigersinn für manifold
        keil = mf.Manifold.extrude(mf.CrossSection([pz]), BR + 2)
        keil = keil.rotate([90, 0, 0]).translate([0, BR + 1, 0])
        m, w = m - keil, w - keil
    if aufgang:
        m = m - _m_box(*auge[:2], -1, *auge[2:], HO + 1) - _m_box(*lift[:2], -1, *lift[2:], HO + 1)
        for x, y in loecher:
            m = m - mf.Manifold.cylinder(3.0, 0.35, 0.35, 64).translate([x, y, HO - 3.0])
    return bauen(name, b, G, {"Bahnsteig": m.volume(), "Weiss": w.volume()},
                 koerperfarben={"Bahnsteig": GRAU, "Weiss": WEISS})


def alle():
    bahnsteig("Bahnsteig_C1_Normal_200", 200)
    bahnsteig("Bahnsteig_C1k_Kurz_103", 103)
    bahnsteig("Bahnsteig_C2_Ende_200", 200, tasche=False, rampe="anfang")
    bahnsteig("Bahnsteig_C2k_Ende_97", 97, zapfen=False, rampe="ende")
    bahnsteig("Bahnsteig_C3_Aufgang_200", 200, aufgang=True)


if __name__ == "__main__":
    alle()
