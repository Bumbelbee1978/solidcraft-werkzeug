"""
Erzeugt SolidCraft-Skripte für die Wendel- und Bahnhofsteile, prüft sie und exportiert 3MF/STEP/SC.
Alle Maße in mm. Aufruf: python3 teile.py [teilname ...]
"""
import json
import math
import subprocess
import sys
from pathlib import Path

CLI = "/home/claude/bin/solidcraft-cli"
AUS = Path(__file__).parent / "teile"
AUS.mkdir(exist_ok=True)


# ---------- kleine Helfer ----------
def rot(p, grad):
    """Punkt um den Ursprung drehen."""
    a = math.radians(grad)
    x, y = p
    return [round(x * math.cos(a) - y * math.sin(a), 4), round(x * math.sin(a) + y * math.cos(a), 4)]


def polar(r, grad, versatz=(0, 0)):
    """Polarkoordinate (Radius, Winkel) plus optionaler Verschiebung."""
    x, y = rot([r, 0], grad)
    return [round(x + versatz[0], 4), round(y + versatz[1], 4)]


def skizze(name, ebene="XY", offset=None):
    """Skizze anlegen."""
    p = {"plane": ebene, "name": name}
    if offset is not None:
        p["offset"] = offset
    return {"command": "sketch.create", "params": p}


def linie(punkte):
    return {"command": "sketch.line", "params": {"points": punkte}}


def bogen(start, ende, durch):
    return {"command": "sketch.arc.three_point", "params": {"start": start, "end": ende, "through": durch}}


def fertig():
    return {"command": "sketch.finish", "params": {}}


def extrusion(abstand, op="new", name=None, koerper=None):
    p = {"distance": abstand, "operation": op}
    if name:
        p["name"] = name
    if koerper:
        p["body_name"] = koerper
    return {"command": "solid.extrude", "params": p}


def vieleck(name, punkte, hoehe, op="new", koerper=None, ebene="XY", offset=None):
    """Geschlossenes Vieleck skizzieren und extrudieren."""
    return [skizze(name, ebene, offset), linie(punkte + [punkte[0]]), fertig(),
            extrusion(hoehe, op, name + "_Extr", koerper)]


def loch(x, y, z, d, tiefe=None, art=None, name=None, ziel=None, **extra):
    """Bohrung an einer Flächenposition."""
    p = {"position": [x, y, z], "diameter": d}
    if tiefe is not None:
        p["depth"] = tiefe
    if art:
        p["type"] = art
    if name:
        p["name"] = name
    if ziel:
        p["targets"] = [ziel]
    p.update(extra)
    return {"command": "solid.hole", "params": p}


def ringsektor(name, r1, r2, w1, w2, hoehe, op="new", koerper=None, versatz=(0, 0), offset=None):
    """Ringsektor von Winkel w1 bis w2 zwischen r1 und r2."""
    wm = (w1 + w2) / 2
    return [skizze(name, "XY", offset),
            linie([polar(r1, w1, versatz), polar(r2, w1, versatz)]),
            bogen(polar(r2, w1, versatz), polar(r2, w2, versatz), polar(r2, wm, versatz)),
            linie([polar(r2, w2, versatz), polar(r1, w2, versatz)]),
            bogen(polar(r1, w2, versatz), polar(r1, w1, versatz), polar(r1, wm, versatz)),
            fertig(), extrusion(hoehe, op, name + "_Extr", koerper)]


# ---------- Prüfen und Exportieren ----------
def bauen(name, befehle, erwartet=None, ansicht="iso"):
    """Skript schreiben, auswerten, Volumen prüfen, exportieren und Vorschaubild erzeugen."""
    skript = AUS / f"{name}.json"
    json.dump({"commands": befehle}, open(skript, "w"), indent=1, ensure_ascii=False)
    r = subprocess.run([CLI, "eval", str(skript)], capture_output=True, text=True)
    if r.returncode:
        print(f"FEHLER {name}: {r.stderr.strip()[:300]}")
        return None
    koerper = json.loads(r.stdout)["bodies"]
    ok = True
    for k in koerper:
        if k.get("error"):
            print(f"FEHLER {name}/{k['name']}: {k['error'][:200]}")
            ok = False
    if not ok:
        return None
    vol = {k["name"]: round(k["volume_mm3"], 1) for k in koerper}
    zu = all(k.get("closed") for k in koerper)
    pruef = ""
    if erwartet:
        for kname, soll in erwartet.items():
            ist = vol.get(kname)
            abw = None if ist is None else abs(ist - soll) / soll * 100
            pruef += f" {kname}: ist {ist} soll {round(soll, 1)} ({'OK' if abw is not None and abw < 0.5 else 'ABWEICHUNG'})"
    print(f"{name}: {len(koerper)} Körper, geschlossen={zu}{pruef or ' ' + str(vol)}")
    subprocess.run([CLI, "run", str(skript), "--out", str(AUS / f"{name}.3mf"), "--out", str(AUS / f"{name}.step"),
                    "--save", str(AUS / f"{name}.sc"), "--quality", "fine", "--quiet"], check=True,
                   capture_output=True)
    subprocess.run([CLI, "snapshot", str(skript), "--out", str(AUS / f"{name}.png"), "--view", ansicht,
                    "--width", "900", "--height", "600"], capture_output=True)
    return vol


# =====================================================================
# Wendel
# =====================================================================
def konsolen():
    """Konsole innen (R 232–262) und außen (R 338–351), flach, 6 mm, auf zwei Muttern."""
    b = []
    # innen: x radial ab R 232, y tangential
    b += vieleck("Konsole_innen", [[0, -20], [30, -20], [30, 20], [0, 20]], 6, koerper="Konsole_innen")
    b += [loch(8, 0, 6, 6.5, name="Stange_innen", ziel="Konsole_innen")]
    b += [loch(26, s * 10, 0, 3.2, art="countersink", cs_diameter=6.4, cs_angle=90, name=f"Schraube_i{n}",
               ziel="Konsole_innen") for n, s in enumerate((-1, 1))]
    # außen: daneben ab x = 40
    b += vieleck("Konsole_aussen", [[40, -20], [53, -20], [53, 20], [40, 20]], 6, koerper="Konsole_aussen")
    b += [loch(45, 0, 6, 6.5, name="Stange_aussen", ziel="Konsole_aussen")]
    b += [loch(45, s * 14, 0, 3.2, art="countersink", cs_diameter=6.4, cs_angle=90, name=f"Schraube_a{n}",
               ziel="Konsole_aussen") for n, s in enumerate((-1, 1))]
    return b


def sonderkonsole():
    """Verlängerte Konsole für die versetzte Außenstange bei 60° (R 395) an der unteren Ausfahrt."""
    b = vieleck("Sonderkonsole", [[0, -20], [64, -20], [64, 20], [0, 20]], 5, koerper="Sonderkonsole")
    b += [loch(57, 0, 5, 6.5, name="Stange")]
    b += [loch(5, s * 14, 0, 3.2, art="countersink", cs_diameter=6.4, cs_angle=90, name=f"Schraube{n}")
          for n, s in enumerate((-1, 1))]
    return b


ANLAUF_HOEHEN = [2.125, 6.375, 10.625, 14.875]


def anlaufkloetze():
    """Acht Anlaufklötze für die Stöße 1–4 (innen und außen), auf die Erweiterung geschraubt."""
    b = []
    for i, h in enumerate(ANLAUF_HOEHEN, start=1):
        x0 = (i - 1) * 50
        # innen 30 × 40, Stange bei x = 8, Befestigungsschraube bei x = 21
        b += vieleck(f"Klotz{i}_innen", [[x0, -20], [x0 + 30, -20], [x0 + 30, 20], [x0, 20]], h,
                     koerper=f"Klotz{i}_innen")
        b += [loch(x0 + 8, 0, h, 6.5, name=f"K{i}i_Stange", ziel=f"Klotz{i}_innen"),
              loch(x0 + 21, 0, h, 3.5, art="countersink", cs_diameter=min(6.4, 3.5 + 2 * (h - 0.6)),
                   cs_angle=90, name=f"K{i}i_Schraube", ziel=f"Klotz{i}_innen")]
        # außen 13 × 40, Stange bei x = 5, Schrauben bei y = ±14
        y0 = 60
        b += vieleck(f"Klotz{i}_aussen", [[x0, y0 - 20], [x0 + 13, y0 - 20], [x0 + 13, y0 + 20], [x0, y0 + 20]], h,
                     koerper=f"Klotz{i}_aussen")
        b += [loch(x0 + 5, y0, h, 6.5, name=f"K{i}a_Stange", ziel=f"Klotz{i}_aussen"),
              loch(x0 + 6.5, y0 + 14, h, 3.5, art="countersink", cs_diameter=min(6.4, 3.5 + 2 * (h - 0.6)),
                   cs_angle=90, name=f"K{i}a_Schraube", ziel=f"Klotz{i}_aussen")]
    return b


def ausfahrplatte():
    """Ebene 4-mm-Platte für die obere Ausfahrt (südlich, Richtung Osten), mit Nut für den letzten Zapfen."""
    umriss = [[0, -350], [220, -350], [220, -250], [0, -250], [0, -291], [10, -291], [10, -309], [0, -309]]
    # Umriss mit Nut; Halbkreis-Ausklinkung bei (0, −343) als Bogen
    b = [skizze("Ausfahrplatte"),
         linie([[0, -339], [0, -309], [10, -309], [10, -291], [0, -291], [0, -250], [220, -250], [220, -350],
                [0, -350], [0, -347]]),
         bogen([0, -347], [0, -339], [4, -343]),
         fertig(), extrusion(4, "new", "Platte_Extr", "Ausfahrplatte")]
    # Nut: an der Kante 12 mm, in 10 mm Tiefe 18 mm breit -> Trapez, daher Umriss korrigieren
    b[1] = linie([[0, -339], [0, -306], [10, -309], [10, -291], [0, -294], [0, -250], [220, -250], [220, -350],
                  [0, -350], [0, -347]])
    b += vieleck("Leitkante", [[0, -350], [220, -350], [220, -346], [0, -346]], 10, "join", offset=4)
    b += vieleck("Randleiste", [[0, -254], [220, -254], [220, -250], [0, -250]], 4, "join", offset=4)
    b += [loch(171.5, -297.05, 0, 7, name="Stange_300"),
          loch(14, -343, 0, 2.4, 3, name="Vorbohrung_aussen"),
          loch(10, -258, 0, 2.4, 3, name="Vorbohrung_innen")]
    return b


def gleisbettung(name, r, w):
    """TPU-Bettungsstreifen 18 mm breit, 2 mm dick (ein Streifen je Datei)."""
    return ringsektor(name, r - 9, r + 9, 0, w, 2, koerper=name)


# =====================================================================
# Bahnhof
# =====================================================================
TURM_L, TURM_B, TURM_H, WAND = 40.0, 29.0, 42.0, 1.2
HAUT = 0.3          # Restwandstärke im Knick
FALZ = 0.3          # Tiefe des Folienfalzes


def aufzugturm_faltwand():
    """Aufzugturm als Faltabwicklung: vier Wände nebeneinander, V-Nuten zum Umknicken, Fenster mit Folienfalz.
    Flach drucken: Außenseite unten (z = 0), Innenseite oben (z = WAND)."""
    breiten = [TURM_L, TURM_B, TURM_L, TURM_B]
    gesamt = sum(breiten)
    b = vieleck("Abwicklung", [[0, 0], [gesamt, 0], [gesamt, TURM_H], [0, TURM_H]], WAND, koerper="Aufzugturm")
    rand, riegel = 1.5, (14.0, 28.0)
    x = 0.0
    for i, w in enumerate(breiten):
        # Folienfalz: eine Tasche je Wand von innen
        b += vieleck(f"Falz{i}", [[x + 1.0, 1.0], [x + w - 1.0, 1.0], [x + w - 1.0, TURM_H - 1.0], [x + 1.0, TURM_H - 1.0]],
                     FALZ, "cut", offset=WAND - FALZ)
        # Fensterfelder: lange Wand 3 Spalten, kurze Wand 2 Spalten, 3 Reihen
        spalten = 3 if w == TURM_L else 2
        pfosten = 1.0
        feld_b = (w - 2 * rand - (spalten - 1) * pfosten) / spalten
        reihen = [(rand, riegel[0] - 0.5), (riegel[0] + 0.5, riegel[1] - 0.5), (riegel[1] + 0.5, TURM_H - rand)]
        for s in range(spalten):
            fx = x + rand + s * (feld_b + pfosten)
            for r, (y1, y2) in enumerate(reihen):
                # Tür unten in der ersten kurzen Wand: Feld bleibt offen bis zum Boden
                if i == 1 and r == 0:
                    y1 = 0.0
                b += vieleck(f"Fenster{i}_{s}_{r}", [[fx, y1], [fx + feld_b, y1], [fx + feld_b, y2], [fx, y2]], 5, "cut",
                             offset=-1)
        x += w
    # V-Nuten (90°) an den drei Knicken, halbe V-Fasen an beiden Enden
    def v_nut(name, xm, links=True, rechts=True):
        tiefe = WAND - HAUT
        p = []
        p.append([xm - (tiefe if links else 0), WAND])
        p.append([xm + (tiefe if rechts else 0), WAND])
        p.append([xm, HAUT])
        # Skizze auf XZ: Skizzen-x = Welt-x, Skizzen-y = Welt −Z  -> z negativ eintragen
        punkte = [[px, -pz] for px, pz in p]
        return [skizze(name, "XZ", offset=-1), linie(punkte + [punkte[0]]), fertig(),
                extrusion(TURM_H + 2, "cut", name + "_Extr")]
    x = 0.0
    for i, w in enumerate(breiten[:-1]):
        x += w
        b += v_nut(f"Knick{i + 1}", x)
    b += v_nut("Fase_Anfang", 0.0, links=False)
    b += v_nut("Fase_Ende", gesamt, rechts=False)
    return b


SCHACHT_L, SCHACHT_B = 25.0, 14.0


def aufzugschacht():
    """Doppelaufzugschacht 25 × 14 × 42 mit Mittelwand-Andeutung und Türen (0,5 mm vertieft)."""
    b = vieleck("Schacht", [[0, 0], [SCHACHT_L, 0], [SCHACHT_L, SCHACHT_B], [0, SCHACHT_B]], TURM_H, koerper="Schacht")
    # Trennfuge zwischen den Kabinen auf beiden Langseiten
    for y0, y1 in ((0, 0.4), (SCHACHT_B - 0.4, SCHACHT_B)):
        b += vieleck(f"Fuge_{y0}", [[12.3, y0], [12.7, y0], [12.7, y1], [12.3, y1]], TURM_H, "cut")
    # Türen: je Kabine unten und oben, beide Langseiten, 6 × 9 mm, 0,5 mm tief
    for kx in (3.25, 15.75):
        for z0 in (0.0, TURM_H - 9.5):
            for y0, y1 in ((0, 0.5), (SCHACHT_B - 0.5, SCHACHT_B)):
                b += vieleck(f"Tuer_{kx}_{z0}_{y0}", [[kx, y0], [kx + 6, y0], [kx + 6, y1], [kx, y1]], 9, "cut",
                             offset=z0 + 0.3)
    return b


STUFE_H = 2.1


def treppenlauf(name, auftritt, breite=6.0, stufen=5, dicke_ende=3.6):
    """Treppenlauf als Seitenprofil, flach liegend zu drucken (Profil auf dem Bett, Breite = Extrusion)."""
    t, h = auftritt, STUFE_H
    p = [[0, 0], [0, h]]
    for i in range(1, stufen):
        p += [[i * t, i * h], [i * t, (i + 1) * h]]
    p += [[stufen * t, stufen * h], [stufen * t, stufen * h - dicke_ende], [t, 0]]
    return vieleck(name, p, breite, koerper=name)


def treppen():
    """Zwei Treppenläufe (lang 5 mm, kurz 2,8 mm Auftritt) und ein Eckpodest 6,3 × 6,3 × 2."""
    b = treppenlauf("Lauf_lang", 5.0)
    lauf_kurz = treppenlauf("Lauf_kurz", 2.8)
    # kurzen Lauf verschieben: Punkte um x+35
    for c in lauf_kurz:
        if c["command"] == "sketch.line":
            c["params"]["points"] = [[px + 35, py] for px, py in c["params"]["points"]]
    b += lauf_kurz
    b += vieleck("Podest", [[60, 0], [66.3, 0], [66.3, 6.3], [60, 6.3]], 2, koerper="Podest")
    return b


def stufenplateau():
    """Stufenplateau am Industrie-Eingang: 58 × 40 mm, 7,3 mm hoch, drei Stufen, Mulde für den Turm."""
    h = 7.3
    s = h / 3
    profil = [[0, 0], [88, 0], [88, h], [30, h], [30, 2 * s], [20, 2 * s], [20, s], [10, s], [10, 0]]
    # Profil auf XZ (Skizzen-y = −Z) -> z negativ, Extrusion 40 mm in Y
    punkte = [[px, -pz] for px, pz in profil]
    b = [skizze("Plateau", "XZ"), linie(punkte + [punkte[0]]), fertig(), extrusion(40, "new", "Plateau_Extr", "Plateau")]
    # 0,5 mm tiefe Mulde für den Turm (40,4 × 29,4) zum Ausrichten
    b += vieleck("Turmmulde", [[42, 5.3], [82.4, 5.3], [82.4, 34.7], [42, 34.7]], 1, "cut", offset=h - 0.5)
    return b


TEILE = {
    "HA_02_Konsolen": (konsolen, None),
    "HA_02_Sonderkonsole_60": (sonderkonsole, None),
    "HA_04_Anlaufkloetze": (anlaufkloetze, None),
    "HA_05_Ausfahrplatte": (ausfahrplatte, None),
    "HA_03_Bettung_aussen_30": (lambda: gleisbettung("Bett_aussen_30", 320, 30), None),
    "HA_03_Bettung_aussen_15": (lambda: gleisbettung("Bett_aussen_15", 320, 15), None),
    "HA_03_Bettung_innen_30": (lambda: gleisbettung("Bett_innen_30", 280, 30), None),
    "HA_03_Bettung_innen_15": (lambda: gleisbettung("Bett_innen_15", 280, 15), None),
    "HA_11_Turm_Faltwand": (aufzugturm_faltwand, None),
    "HA_11_Schacht": (aufzugschacht, None),
    "HA_11_Treppe": (treppen, None),
    "HA_15_Stufenplateau": (stufenplateau, None),
}



# =====================================================================
# Beweglicher Aufzug (Glasschacht, Kabinen, Kopf/Boden, Servohalter, Hebel)
# =====================================================================
def faltwand(name, breiten, hoehe, wand, spalten, reihen_grenzen, rand=1.2, pfosten=0.8, haut=0.3, falz=0.25):
    """Allgemeine Faltwand: Wände nebeneinander, Folienfalz je Wand, Fensterraster, V-Nuten zum Falten."""
    gesamt = sum(breiten)
    b = vieleck(name, [[0, 0], [gesamt, 0], [gesamt, hoehe], [0, hoehe]], wand, koerper=name)
    x = 0.0
    for i, w in enumerate(breiten):
        b += vieleck(f"{name}_Falz{i}", [[x + 0.8, 0.8], [x + w - 0.8, 0.8], [x + w - 0.8, hoehe - 0.8], [x + 0.8, hoehe - 0.8]],
                     falz, "cut", offset=wand - falz)
        sp = spalten[i]
        feld_b = (w - 2 * rand - (sp - 1) * pfosten) / sp
        for s in range(sp):
            fx = x + rand + s * (feld_b + pfosten)
            for r, (y1, y2) in enumerate(reihen_grenzen):
                b += vieleck(f"{name}_F{i}_{s}_{r}", [[fx, y1], [fx + feld_b, y1], [fx + feld_b, y2], [fx, y2]], wand + 2,
                             "cut", offset=-1)
        x += w
    tiefe = wand - haut
    def v_nut(nname, xm, links=True, rechts=True):
        p = [[xm - (tiefe if links else 0), wand], [xm + (tiefe if rechts else 0), wand], [xm, haut]]
        punkte = [[px, -pz] for px, pz in p]
        return [skizze(nname, "XZ", offset=-1), linie(punkte + [punkte[0]]), fertig(),
                extrusion(hoehe + 2, "cut", nname + "_Extr")]
    x = 0.0
    for i, w in enumerate(breiten[:-1]):
        x += w
        b += v_nut(f"{name}_Knick{i + 1}", x)
    b += v_nut(f"{name}_FaseA", 0.0, links=False)
    b += v_nut(f"{name}_FaseE", gesamt, rechts=False)
    return b


# Innenmaße Schacht (Wand 1,0): 23 × 12; Röhrchen Mitte (11,5 | 6), Führungsdrähte (2,0 | 6) und (21,0 | 6)
SCH_I_L, SCH_I_B = 23.0, 12.0
ROHR = (11.5, 6.0)
DRAHT = [(3.3, 6.0), (19.7, 6.0)]   # je 1,5 mm innerhalb der Kabinen-Außenseite
SEIL = [(6.55, 6.0), (16.45, 6.0)]   # Kabinenmitten (Kabinen x 1,8–11,3 und 11,7–21,2)


def glasschacht():
    """Glasschacht 25 × 14 × 42 als Faltwand mit Fensterraster (lang 2 Spalten, kurz 1 Spalte, 3 Reihen)."""
    reihen = [(1.2, 13.6), (14.4, 27.6), (28.4, 40.8)]
    return faltwand("Glasschacht", [25.0, 14.0, 25.0, 14.0], 42.0, 1.0, [2, 1, 2, 1], reihen)


def schacht_boden_kopf():
    """Bodenplatte (1,5 mm) und Kopfstück (4 mm) – passen innen in den Schacht (23 × 12)."""
    b = vieleck("Schachtboden", [[0, 0], [SCH_I_L, 0], [SCH_I_L, SCH_I_B], [0, SCH_I_B]], 1.5, koerper="Schachtboden")
    b += [loch(ROHR[0], ROHR[1], 1.5, 1.6, name="Boden_Rohr", ziel="Schachtboden")]
    b += [loch(x, y, 1.5, 0.55, name=f"Boden_Draht{i}", ziel="Schachtboden") for i, (x, y) in enumerate(DRAHT)]
    # Kopfstück daneben (x + 30): Röhrchen 2 mm tief von unten, Seillöcher durchgehend, Rille oben
    dx = 30.0
    b += vieleck("Kopfstueck", [[dx, 0], [dx + SCH_I_L, 0], [dx + SCH_I_L, SCH_I_B], [dx, SCH_I_B]], 4, koerper="Kopfstueck")
    b += vieleck("Kopf_Rille", [[dx + SEIL[0][0], 5.6], [dx + SEIL[1][0], 5.6], [dx + SEIL[1][0], 6.4], [dx + SEIL[0][0], 6.4]],
                 0.8, "cut", offset=3.2)
    b += [loch(dx + ROHR[0], ROHR[1], 0, 1.6, 2, name="Kopf_Rohr", ziel="Kopfstueck"),
          loch(dx + ROHR[0], ROHR[1], 4, 1.0, name="Kopf_Seil_Mitte", ziel="Kopfstueck")]
    b += [loch(dx + x, y, 4, 1.0, name=f"Kopf_Seil{i}", ziel="Kopfstueck") for i, (x, y) in enumerate(SEIL)]
    b += [loch(dx + x, y, 0, 0.55, 2.5, name=f"Kopf_Draht{i}", ziel="Kopfstueck") for i, (x, y) in enumerate(DRAHT)]
    return b


KAB_L, KAB_B, KAB_H, KAB_W = 9.5, 10.0, 14.0, 0.8


def kabine():
    """Aufzugkabine 9,5 × 10 × 14 mm: Fenster an drei Seiten, Kerbe für das Röhrchen, Seilöse, Führungsloch,
    Ballastmulde. Stehend drucken. x = 0 ist die Außenseite (Führungsdraht), x = 9,5 die Röhrchenseite."""
    b = vieleck("Kabine", [[0, 0], [KAB_L, 0], [KAB_L, KAB_B], [0, KAB_B]], KAB_H, koerper="Kabine")
    # Innenraum von z = 1,5 bis z = 13 (Dach 1,0)
    b += vieleck("Kab_Innen", [[KAB_W, KAB_W], [KAB_L - KAB_W, KAB_W], [KAB_L - KAB_W, KAB_B - KAB_W], [KAB_W, KAB_B - KAB_W]],
                 11.5, "cut", offset=1.5)
    # Fenster vorn und hinten (y-Seiten) und außen (x = 0)
    b += vieleck("Kab_Fenster_vorn", [[1.0, -1], [KAB_L - 1.0, -1], [KAB_L - 1.0, 1], [1.0, 1]], 9.5, "cut", offset=2.5)
    b += vieleck("Kab_Fenster_hinten", [[1.0, KAB_B - 1], [KAB_L - 1.0, KAB_B - 1], [KAB_L - 1.0, KAB_B + 1], [1.0, KAB_B + 1]],
                 9.5, "cut", offset=2.5)
    b += vieleck("Kab_Fenster_aussen", [[-1, 1.5], [1, 1.5], [1, KAB_B - 1.5], [-1, KAB_B - 1.5]], 9.5, "cut", offset=2.5)
    # Kerbe für das Röhrchen (Ø 1,5) an der Innenseite, 0,85 tief, 2,0 breit, ganze Höhe – beide Kabinen umgreifen es
    b += vieleck("Kab_Kerbe", [[KAB_L - 0.85, KAB_B / 2 - 1.0], [KAB_L + 1, KAB_B / 2 - 1.0], [KAB_L + 1, KAB_B / 2 + 1.0],
                               [KAB_L - 0.85, KAB_B / 2 + 1.0]], KAB_H + 2, "cut", offset=-1)
    # Seilöse Mitte Dach, Führungsloch außen (Dach und Boden), Ballastmulde im Boden
    b += [loch(KAB_L / 2, KAB_B / 2, KAB_H, 1.0, 1.0, name="Seiloese"),
          loch(1.5, KAB_B / 2, KAB_H, 0.7, 1.0, name="Fuehrung_Dach"),
          loch(1.5, KAB_B / 2, 0, 0.7, 1.5, name="Fuehrung_Boden"),
          loch(KAB_L / 2 + 0.5, KAB_B / 2, 1.5, 3.2, 1.0, name="Ballastmulde")]
    return b


def servohalter():
    """Winkel für einen Mikroservo SG90: Flansch unter die Platte (Langloch für das Röhrchen), senkrechte Platte
    mit Servo-Ausschnitt 23,1 × 12,6 und Laschenlöchern im Abstand 27,8 mm. Liegend drucken."""
    # Flansch 50 × 22 × 3 (x, y), senkrechte Platte als zweiter Quader 50 × 3 × 45 an der Kante y = 0
    b = vieleck("Halter", [[0, 0], [50, 0], [50, 22], [0, 22]], 3, koerper="Servohalter")
    b += vieleck("Halter_Platte", [[0, 0], [50, 0], [50, 3], [0, 3]], 45, "join")
    # Servo-Ausschnitt in der senkrechten Platte (Skizze auf XZ, Extrusion in +Y)
    aus = [[13.45, -20], [36.55, -20], [36.55, -32.6], [13.45, -32.6]]
    b += [skizze("Servo_Ausschnitt", "XZ", offset=-1), linie(aus + [aus[0]]), fertig(), extrusion(5, "cut", "Servo_Extr")]
    lasche = [[11.1, -26.3], [38.9, -26.3]]
    for i, (x, z) in enumerate(lasche):
        b += [loch(x, 0, -z, 1.8, name=f"Lasche{i}", direction=[0, 1, 0])]
    # Befestigung an der Platte (2 × Ø 3,5 gesenkt von unten) und Langloch 2 × 8 für das Röhrchen
    b += [loch(x, 15, 3, 3.5, art="countersink", cs_diameter=7, cs_angle=90, name=f"Befestigung{i}")
          for i, x in enumerate((6, 44))]
    b += vieleck("Rohr_Fenster", [[17, 8], [33, 8], [33, 16], [17, 16]], 5, "cut", offset=-1)
    return b


def servohebel():
    """Doppelhebel 40 × 5 × 2 mm zum Aufkleben auf das Servohorn: Mitte Ø 2,5, Seillöcher Ø 1,0 bei ±14 und ±16 mm."""
    b = vieleck("Hebel", [[-20, -2.5], [20, -2.5], [20, 2.5], [-20, 2.5]], 2, koerper="Hebel")
    b += [loch(0, 0, 2, 2.5, name="Hebel_Mitte")]
    b += [loch(s * r, 0, 2, 1.0, name=f"Hebel_{s}_{r}") for s in (-1, 1) for r in (14, 16)]
    return b


TEILE.update({
    "HA_11_Glasschacht_Faltwand": (glasschacht, None),
    "HA_11_Schacht_Boden_Kopf": (schacht_boden_kopf, None),
    "HA_11_Kabine": (kabine, None),
    "HA_11_Servohalter": (servohalter, None),
    "HA_11_Servohebel": (servohebel, None),
})


if __name__ == "__main__":
    auswahl = sys.argv[1:] or list(TEILE)
    for name in auswahl:
        f, erw = TEILE[name]
        bauen(name, f(), erw)


# =====================================================================
# Wendel v2: ohne Schrauben im Plattenmaterial (Ratsbeschluss 09.11.)
# =====================================================================
STIFT_D, STIFT_H = 4.0, 3.0          # Stift oben auf der Innenkonsole
NUT_B, NUT_L, NUT_T = 4.2, 5.0, 3.4  # 4,4 war zu locker (Probe 09.11.)  # Sacklanghloch in der Platte (tangential × radial × tief)
STIFT_R, STIFT_A = 258.0, 10.0       # Radius und Abstand zur Fuge (innen)
STIFT_R_AUSSEN = 343.0               # Radius der Stifte außen (auf Höhe der Stange)


def langloch_cut(name, mitte, winkel, koerper):
    """Radiales Sacklanghloch von unten (z = 0) in die Platte schneiden."""
    a = math.radians(winkel)
    u = (math.cos(a), math.sin(a))      # radial
    t = (-math.sin(a), math.cos(a))     # tangential
    pkt = [[round(mitte[0] + su * NUT_L / 2 * u[0] + st * NUT_B / 2 * t[0], 4),
            round(mitte[1] + su * NUT_L / 2 * u[1] + st * NUT_B / 2 * t[1], 4)]
           for su, st in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    return vieleck(name, pkt, NUT_T, op="cut", koerper=koerper)


def stift(name, x, y, z, koerper):
    """Zylindrischer Stift als 24-Eck (robuster als Kreis-Join)."""
    pkt = [[round(x + STIFT_D / 2 * math.cos(2 * math.pi * i / 24), 4),
            round(y + STIFT_D / 2 * math.sin(2 * math.pi * i / 24), 4)] for i in range(24)]
    return vieleck(name, pkt, STIFT_H, op="join", koerper=koerper, offset=z)


def wendelplatte_v2():
    """Wendelplatte wie HA_01, Schrauben-Vorbohrungen ersetzt: innen je Ende ein Sacklanghloch, außen nichts."""
    alt = json.load(open(Path(__file__).parent / "HA_01_Wendelplatte.json"))["commands"]
    b = [c for c in alt if not (c["command"] == "solid.hole" and c["params"]["name"].startswith("Vorbohrung"))]
    # Ende bei 0°: Mitte 10 mm von der Kante, Ende bei 30°: 10 mm vor der Kante
    for n, kante in enumerate((0.0, 30.0), start=1):
        vz = 1 if kante == 0 else -1
        for r, seite in ((STIFT_R, "i"), (STIFT_R_AUSSEN, "a")):
            mitte = rot([r, vz * STIFT_A], kante)
            b += langloch_cut(f"Stiftloch_{seite}{n}", mitte, kante, "Wendelplatte")
    return b


def konsolen_v2():
    """Konsolen ohne Schrauben: innen und außen je zwei Stifte (je Plattenende einer) plus Stangenbohrung."""
    b = []
    b += vieleck("Konsole_innen", [[0, -20], [30, -20], [30, 20], [0, 20]], 6, koerper="Konsole_innen")
    b += [loch(8, 0, 6, 6.5, name="Stange_innen", ziel="Konsole_innen")]
    for n, s in enumerate((-1, 1)):
        b += stift(f"Stift_{n}", STIFT_R - 232, s * STIFT_A, 6, "Konsole_innen")
    b += vieleck("Konsole_aussen", [[40, -20], [53, -20], [53, 20], [40, 20]], 6, koerper="Konsole_aussen")
    b += [loch(45, 0, 6, 6.5, name="Stange_aussen", ziel="Konsole_aussen")]
    for n, s in enumerate((-1, 1)):
        b += stift(f"Stift_a{n}", 40 + STIFT_R_AUSSEN - 338, s * STIFT_A, 6, "Konsole_aussen")
    return b


def passprobe():
    """Plattenstück R 250–275 über 8° mit Randleiste und Stiftloch – zweimal drucken, mit der Innenkonsole testen."""
    b = ringsektor("Probe", 250, 275, 0, 8, 4, koerper="Passprobe")
    b += ringsektor("Probe_Rand", 250, 254, 0, 8, 4, op="join", koerper="Passprobe", offset=4)
    b += langloch_cut("Probe_Loch", [STIFT_R, STIFT_A], 0, "Passprobe")
    # Gegenstück (das andere Plattenende): gespiegelt, Loch 10 mm vor der Kante bei 8°
    b += ringsektor("ProbeG", 250, 275, 10, 18, 4, koerper="Passprobe_G")
    b += ringsektor("ProbeG_Rand", 250, 254, 10, 18, 4, op="join", koerper="Passprobe_G", offset=4)
    b += langloch_cut("ProbeG_Loch", rot([STIFT_R, -STIFT_A], 18), 18, "Passprobe_G")
    # Außenstücke R 330–350 (ohne Leitkante, nur für die Passung), ebenfalls als Paar
    b += ringsektor("Probe_a", 330, 350, 0, 6, 4, koerper="Passprobe_aussen")
    b += langloch_cut("Probe_Loch_a", [STIFT_R_AUSSEN, STIFT_A], 0, "Passprobe_aussen")
    b += ringsektor("ProbeG_a", 330, 350, 10, 16, 4, koerper="Passprobe_aussen_G")
    b += langloch_cut("ProbeG_Loch_a", rot([STIFT_R_AUSSEN, -STIFT_A], 16), 16, "Passprobe_aussen_G")
    return b


def gleisbettung_v2(name, r, w, seite):
    """TPU-Streifen 18 × 2 mm mit zwei Anschlagnasen (6 mm breit, 1 mm dick) bis an Randleiste bzw. Leitkante.
    Die Nasen liegen 5° vom Streifenende, also nie an einem Plattenstoß (dort steht außen die Stange)."""
    b = ringsektor(name, r - 9, r + 9, 0, w, 2, koerper=name)
    r1, r2 = (254.3, r - 9 + 0.5) if seite == "innen" else (r + 9 - 0.5, 346.7)
    for n, wm in enumerate((5.0, w - 5.0)):
        dw = math.degrees(3.0 / ((r1 + r2) / 2))   # halbe Nasenbreite 3 mm als Winkel
        b += ringsektor(f"{name}_Nase{n}", r1, r2, wm - dw, wm + dw, 1, op="join", koerper=name)
    return b


TEILE_V2 = {
    "HA_01_Wendelplatte_v2": (wendelplatte_v2, None),
    "HA_02_Konsolen_v2": (konsolen_v2, None),
    "HA_02_Passprobe": (passprobe, None),
    "HA_03_Bettung_aussen_30_v2": (lambda: gleisbettung_v2("Bett_aussen_30", 320, 30, "aussen"), None),
    "HA_03_Bettung_aussen_15_v2": (lambda: gleisbettung_v2("Bett_aussen_15", 320, 15, "aussen"), None),
    "HA_03_Bettung_innen_30_v2": (lambda: gleisbettung_v2("Bett_innen_30", 280, 30, "innen"), None),
    "HA_03_Bettung_innen_15_v2": (lambda: gleisbettung_v2("Bett_innen_15", 280, 15, "innen"), None),
}
