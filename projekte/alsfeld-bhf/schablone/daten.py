"""Stangenpositionen und Mutternhöhen für die Wendel-Bohrschablone (Höhen ab Oberkante Erweiterungsbrett)."""
import math

R_I, R_A, R_SONDER = 240, 343, 395
KONSOLE, SONDER, SCHEIBE = 6.0, 5.0, 1.6     # Konsolendicke an der Stange, Sonderkonsole, Unterlegscheibe DIN 125


def z_stoss(m):
    """Unterkante der Platte am Stoß m (0 = Einfahrt unten, 42 = Ausfahrt oben)."""
    return 0.0 if m == 0 else 2.125 + (m - 1) * 4.25


def welt(m):
    """Winkel der Stoßlinie in der Draufsicht (0° = Osten, gegen den Uhrzeigersinn)."""
    return (90 + 30 * m) % 360


def stangen():
    """Liste aller 24 Stangen mit Position und den Stößen, die sie tragen."""
    liste = []
    for pos in range(12):
        w = welt(pos)
        stoesse = list(range(pos, 43, 12))
        for seite, r in (("I", R_I), ("A", R_A)):
            sonder = seite == "A" and pos == 11
            rr = R_SONDER if sonder else r
            eintraege = []
            for m in stoesse:
                if m == 0:
                    art, h = "Platte liegt auf dem Brett", None
                elif m <= 4:
                    art, h = f"Anlaufklotz {z_stoss(m):.3f} mm hoch".replace(".", ","), None
                else:
                    dicke = SONDER if sonder else KONSOLE
                    art = "Sonderkonsole" if sonder else "Konsole"
                    h = z_stoss(m) - dicke - SCHEIBE
                eintraege.append((m, art, h))
            liste.append(dict(name=f"{seite}{pos:02d}", seite=seite, pos=pos, winkel=w, r=rr,
                              x=rr * math.cos(math.radians(w)), y=rr * math.sin(math.radians(w)),
                              eintraege=eintraege))
    return liste


if __name__ == "__main__":
    for s in stangen():
        print(s["name"], round(s["x"], 1), round(s["y"], 1),
              [(m, a, None if h is None else round(h, 2)) for m, a, h in s["eintraege"]])
