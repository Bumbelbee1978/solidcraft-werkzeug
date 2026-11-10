"""Stellt das MakerWorld-Paket für den Wendel zusammen: Druckplatten, Einzelteile (3MF + STEP), Anleitung."""
import shutil, sys, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, "/home/claude/heimanlage/druck")
import testsatz as t

TEILE = Path("/home/claude/heimanlage/solidcraft/teile")
ZIEL = Path("Wendel_SpurN_2gleisig")
if ZIEL.exists(): shutil.rmtree(ZIEL)
for o in ("01_Druckplatten", "02_Einzelteile", "03_Testdrucke", "04_Anleitung"):
    (ZIEL / o).mkdir(parents=True)


def obj(datei, name=None):
    o = t.lesen(datei); return o[name] if name else next(iter(o.values()))


def gedreht(p):
    """180° um X: Oberseite aufs Bett (für Klemmböcke)."""
    return p * np.array([1, -1, -1])


def pruefen(teile, name):
    """Rasterprüfung: liegen Teile übereinander oder außerhalb des Betts (256 × 256)?"""
    g = np.zeros((520, 520), np.uint8)
    for _, p, d in teile:
        assert p[:, :2].min() >= 0 and p[:, :2].max() <= 256, f"{name}: außerhalb des Betts"
        im = Image.new("L", (520, 520), 0); dr = ImageDraw.Draw(im)
        for tri in p[d][:, :, :2] * 2:
            dr.polygon([tuple(v) for v in tri], fill=1)
        a = np.array(im); assert not (g & a).any(), f"{name}: Teile überlappen"; g |= a


def platte(datei, teile):
    pruefen(teile, datei); t.schreiben(ZIEL / "01_Druckplatten" / datei, teile)


def stapel(p, d, n, delta, name):
    """n gleiche Bogenstücke ineinander geschachtelt (Verschiebung entlang der Symmetrieachse)."""
    g = p.max(0) - p.min(0)
    return [(f"{name}_{i+1}", t.ablegen(p, (256 - g[0]) / 2, 3 + i * delta), d) for i in range(n)]


# ---------- Druckplatten ----------
pp, pd = obj("HA_01_Wendelplatte_v3.3mf"); pp = t.drehen_z(pp, 75)
platte("01_Wendelplatten_2Stk_21x_drucken.3mf", [("Wendelplatte_1", t.ablegen(pp, 6, 8), pd), ("Wendelplatte_2", t.ablegen(pp, 6, 122.5), pd)])

k = t.lesen("HA_02_Konsolen_v3.3mf"); tl = []
for i in range(4):
    for j in range(2):
        tl.append((f"Konsole_innen_{i}{j}", t.ablegen(k["Konsole_innen"][0], 20 + i * 55, 20 + j * 110), k["Konsole_innen"][1]))
        tl.append((f"Konsole_aussen_{i}{j}", t.ablegen(k["Konsole_aussen"][0], 55 + i * 55, 20 + j * 110), k["Konsole_aussen"][1]))
platte("02_Konsolen_8Saetze_5x_drucken.3mf", tl)

kp, kd = obj("HA_02_Klemmbock_v2.3mf"); kp = gedreht(kp)
platte("03_Klemmboecke_24Stk_2x_drucken.3mf", [(f"Klemmbock_{i}{j}", t.ablegen(kp, 20 + i * 35, 20 + j * 30), kd) for i in range(6) for j in range(4)])

tl = []
ak = t.lesen("HA_05_Anlaufkloetze_v3.3mf"); alle = np.vstack([p for p, _ in ak.values()]); mn = alle.min(0)
tl += [(n, p - mn + np.array([10, 10, 0]), d) for n, (p, d) in ak.items()]
sk = obj("HA_04_Sonderkonsole_v3.3mf")
tl += [(f"Sonderkonsole_{i+1}", t.ablegen(sk[0], 10 + i * 72, 150), sk[1]) for i in range(3)]
for n, dat in enumerate(("HA_02_Konsolen_Stoss41.3mf", "HA_02_Konsolen_Stoss42.3mf")):
    kk = t.lesen(dat)
    tl.append((f"Stoss{41+n}_innen", t.ablegen(kk["Konsole_innen"][0], 10 + n * 65, 205), kk["Konsole_innen"][1]))
    tl.append((f"Stoss{41+n}_aussen", t.ablegen(kk["Konsole_aussen"][0], 45 + n * 65, 205), kk["Konsole_aussen"][1]))
platte("04_Anlaufkloetze_Sonderkonsolen_Stoss41-42_1x_drucken.3mf", tl)

ap = obj("HA_05_Ausfahrplatte_v3.3mf")
platte("05_Ausfahrplatte_1x_drucken.3mf", [("Ausfahrplatte", t.ablegen(ap[0], 18, 78), ap[1])])

for datei, w, delta, n, anzahl, name in [("HA_03_Bettung_aussen_30_v3.3mf", 30, 22, 11, 4, "TPU_Bettung_aussen30_11Stk"),
                                        ("HA_03_Bettung_innen_30_v3.3mf", 30, 22, 11, 4, "TPU_Bettung_innen30_11Stk")]:
    p, d = obj(datei); p = t.drehen_z(p, 90 - w / 2)
    nr = "06" if "aussen" in name else "07"
    platte(f"{nr}_{name}_{anzahl}x_drucken.3mf", stapel(p, d, n, delta, name))
tl = []
gp, gd = obj("HA_03_Bettung_gerade_220.3mf")
tl += [(f"Bettung_gerade_{j+1}", t.ablegen(gp, 18, 200 + j * 26), gd) for j in range(2)]
for i, (datei, delta_y) in enumerate((("HA_03_Bettung_aussen_15_v3.3mf", 5), ("HA_03_Bettung_innen_15_v3.3mf", 90))):
    p, d = obj(datei); p = t.drehen_z(p, 90 - 7.5); g = p.max(0) - p.min(0)
    for j in range(2):
        tl.append((f"{datei[3:-8]}_{j+1}", t.ablegen(p, 8 + j * (g[0] + 15), delta_y), d))
platte("08_TPU_Bettung_15Grad_und_gerade_1x_drucken.3mf", tl)

# ---------- Einzelteile ----------
E = ZIEL / "02_Einzelteile"
einzel = [("HA_01_Wendelplatte_v3", None, "HA01_Wendelplatte_42x", None),
          ("HA_02_Konsolen_v3", "Konsole_innen", "HA02_Konsole_innen_36x", None),
          ("HA_02_Konsolen_v3", "Konsole_aussen", "HA02_Konsole_aussen_33x", None),
          ("HA_02_Konsolen_Stoss41", None, "HA02_Konsolen_Stoss41_innen+aussen_1x", "alle"),
          ("HA_02_Konsolen_Stoss42", None, "HA02_Konsolen_Stoss42_innen+aussen_1x", "alle"),
          ("HA_02_Klemmbock_v2", None, "HA02_Klemmbock_42x", "drehen"),
          ("HA_04_Sonderkonsole_v3", None, "HA04_Sonderkonsole_3x", None),
          ("HA_05_Anlaufkloetze_v3", None, "HA05_Anlaufkloetze_Satz_8Teile_1x", "alle"),
          ("HA_05_Ausfahrplatte_v3", None, "HA05_Ausfahrplatte_1x", None),
          ("HA_03_Bettung_aussen_30_v3", None, "HA03_TPU_Bettung_aussen_30Grad_41x", None),
          ("HA_03_Bettung_innen_30_v3", None, "HA03_TPU_Bettung_innen_30Grad_41x", None),
          ("HA_03_Bettung_aussen_15_v3", None, "HA03_TPU_Bettung_aussen_15Grad_2x", None),
          ("HA_03_Bettung_innen_15_v3", None, "HA03_TPU_Bettung_innen_15Grad_2x", None),
          ("HA_03_Bettung_gerade_220", None, "HA03_TPU_Bettung_gerade_Ausfahrt_2x", None)]
for quelle, koerper, ziel, art in einzel:
    o = t.lesen(quelle + ".3mf")
    if art == "alle":
        teile = [(n, p - np.vstack([q for q, _ in o.values()]).min(0), d) for n, (p, d) in o.items()]
    else:
        p, d = o[koerper] if koerper else next(iter(o.values()))
        if art == "drehen": p = gedreht(p)
        teile = [(ziel, p - p.min(0), d)]
    t.schreiben(E / f"{ziel}.3mf", teile)
    shutil.copy(TEILE / f"{quelle}.step", E / f"{ziel}{'_(beide)' if koerper == 'Konsole_innen' else ''}.step" if koerper != "Konsole_aussen" else E / "_skip.step")
(E / "_skip.step").unlink(missing_ok=True)
for f in E.glob("HA02_Konsole_innen_36x_(beide).step"):
    f.rename(E / "HA02_Konsolen_innen+aussen.step")

# ---------- Testdrucke ----------
T = ZIEL / "03_Testdrucke"
shutil.copy("/home/claude/heimanlage/druck/Keil_Konsolen_Klemmbock_Test_PETG.3mf", T / "Test1_Konsolen_Keil_Klemmbock.3mf")
shutil.copy("/home/claude/heimanlage/druck/Passprobe_Varianten_PETG.3mf", T / "Test2_Passprobe_Stifte_3Varianten.3mf")
shutil.copy("/home/claude/heimanlage/druck/Taschenprobe_PETG.3mf", T / "Test3a_Taschenprobe_PETG.3mf")
shutil.copy("/home/claude/heimanlage/druck/Taschenprobe_TPU.3mf", T / "Test3b_Taschenprobe_TPU.3mf")
print(sorted(str(p.relative_to(ZIEL)) for p in ZIEL.rglob("*") if p.is_file()))

# ---------- Anleitung, Beschreibung, Titelbild (werden durch das Neuanlegen sonst gelöscht) ----------
A = ZIEL / "04_Anleitung"
for q in ("/home/claude/heimanlage/schablone/Wendel_Bohrschablone_1zu1.pdf",
          "/home/claude/heimanlage/druck/Keil_Skizze.png", "/home/claude/heimanlage/druck/Klemmbock_Schnitt.png"):
    shutil.copy(q, A)
shutil.copy("Titelbild_Wendel.png", ZIEL)
shutil.copy("Beschreibung_MakerWorld.md", ZIEL)
shutil.copy("Druckplatten_Uebersicht.png", A)
