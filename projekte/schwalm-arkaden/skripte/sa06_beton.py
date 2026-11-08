"""
SA_06 Beton (Modul C): Betonwand-Feld mit Brettschalung, Kappe mit Tropfnase, Kabeltrog.
Wandfeld liegt flach: x = Breite 45, y = Höhe 61 (Fundament unten), z = Dicke 3 (Ansicht oben).
"""
from sa_basis import *

G = "SA_06_Beton"
BETON, HELL = "#9C9C98", "#C8C8C4"


def betonfeld():
    b = [quader("Wand", 0, 0, 0, 45, 61, 3.0),
         quader("Fundament", 0, 0, 0, 45, 4.0, 4.5, op="join", ziele=["Wand"]),
         # halbe Dehnfugen an beiden Rändern (zwei Felder ergeben 0,4)
         quader("Fuge_links", -1, 4.0, 3.0 - 0.3, 1.2, 58, 2, op="cut", ziele=["Wand"]),
         quader("Fuge_rechts", 44.8, 4.0, 3.0 - 0.3, 1.2, 58, 2, op="cut", ziele=["Wand"])]
    v = 45 * 61 * 3 + 45 * 4 * 1.5 - 2 * 0.2 * 57 * 0.3
    # Brettschalung: Rillen 0,3 breit alle 0,8 (≙ 13-cm-Bretter), 0,15 tief, nur auf der Ansichtsfläche
    bretter = lagerrillen(0.2, 44.8, 4.0, 61.0, 3.0, 0.8, 0.3, 0.15)
    bretter = [(max(x0, 0.2), y0, z0, min(x1, 44.8), y1, z1) for x0, y0, z0, x1, y1, z1 in bretter]
    return bauen("Betonwand_Feld", b, G, {"Wand": v}, struktur={"Wand": bretter}, ansicht="iso",
                 koerperfarben={"Wand": BETON})


def kappe():
    """Profil (y | z): 4 breit, 2 hoch, Tropfnase 0,3 × 0,6 vorn unten; Nut 3,1 × 0,6 für die Wandkante."""
    pk = [(0, 0), (0.45, 0), (0.45, 0.6), (3.55, 0.6), (3.55, 0), (3.7, 0), (3.7, 0.0), (4.0, 0.0)]
    profil = [(0, 0), (0.45, 0), (0.45, 0.6), (3.55, 0.6), (3.55, 0), (4.0, 0), (4.0, 1.4), (3.7, 1.4), (3.7, 2.0),
              (0, 2.0)]
    b = profil_yz("Kappe", profil, 225.0, koerper="Kappe")
    flaeche_p = 4 * 2 - 0.3 * 0.6 - 3.1 * 0.6
    return bauen("Kappe_225", b, G, {"Kappe": flaeche_p * 225}, koerperfarben={"Kappe": HELL})


def kabeltrog():
    b = [quader("Trog", 0, 0, 0, 225, 3.5, 1.5)]
    deckel = []
    x = 6.0
    while x < 225:
        deckel.append((x - 0.15, -1, 1.5 - 0.1, x + 0.15, 4.5, 2.5))
        x += 6.0
    return bauen("Kabeltrog_225", b, G, {"Trog": 225 * 3.5 * 1.5}, struktur={"Trog": deckel},
                 koerperfarben={"Trog": HELL})


def alle():
    betonfeld()
    kappe()
    kabeltrog()


if __name__ == "__main__":
    alle()
