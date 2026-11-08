"""
Basisbibliothek für die SolidCraft-Teile der Schwalm-Arkaden.

Enthält kleine Bausteine für SolidCraft-Skripte (Skizze, Rechteck, Vieleck, Quader, Zylinder),
die Prüf- und Exportfunktion {@code bauen} und die Oberflächenstruktur (Ziegel, Bretter, Rillen),
die als Netz-Boolesche Operation mit manifold3d auf das fertige Teil gerechnet wird.

Alle Maße in mm. Koordinaten je Teil lokal: Ursprung (0|0|0) wie in der Anleitung angegeben.
"""
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import trimesh
import manifold3d as mf

CLI = "/home/claude/bin/solidcraft-cli"
WURZEL = Path(__file__).parent / "teile"
WURZEL.mkdir(exist_ok=True)

# Sammelliste aller gebauten Teile (für Anleitung und Teileliste)
PROTOKOLL = []


# ---------------------------------------------------------------------------
# Skizzen-Bausteine
# ---------------------------------------------------------------------------
def skizze(name, ebene="XY", offset=None, flip=None):
    """Skizze anlegen. Ebene XY/XZ/YZ oder {origin, x_dir, y_dir}."""
    p = {"plane": ebene, "name": name}
    if offset is not None:
        p["offset"] = offset
    if flip is not None:
        p["flip"] = flip
    return {"command": "sketch.create", "params": p}


def linie(punkte, geschlossen=False):
    """Linienzug; bei geschlossen=True wird der erste Punkt am Ende wiederholt."""
    pk = [list(map(float, p)) for p in punkte]
    if geschlossen:
        pk = pk + [pk[0]]
    return {"command": "sketch.line", "params": {"points": pk}}


def bogen3(start, ende, durch):
    """3-Punkt-Bogen."""
    return {"command": "sketch.arc.three_point", "params": {"start": start, "end": ende, "through": durch}}


def spline(punkte):
    """Spline durch Stützpunkte (für Ellipsen- und Versatzkurven)."""
    return {"command": "sketch.spline.fit_point", "params": {"points": [list(map(float, p)) for p in punkte]}}


def kreis(mitte, d):
    """Kreis mit Durchmesser d."""
    return {"command": "sketch.circle.center", "params": {"center": list(mitte), "diameter": d}}


def rechteck(x0, y0, x1, y1):
    """Rechteck über zwei Ecken."""
    return {"command": "sketch.rectangle.two_point", "params": {"p0": [x0, y0], "p1": [x1, y1]}}


def fertig():
    return {"command": "sketch.finish", "params": {}}


def extrusion(abstand, op="new", name=None, koerper=None, richtung=None, start=None, ziele=None):
    """Extrusion der aktiven Skizze. richtung: positive|negative|symmetric."""
    p = {"distance": abstand, "operation": op}
    if name:
        p["name"] = name
    if koerper:
        p["body_name"] = koerper
    if richtung:
        p["direction"] = richtung
    if start is not None:
        p["start_offset"] = start
    if ziele:
        p["targets"] = ziele
    return {"command": "solid.extrude", "params": p}


def vieleck(name, punkte, hoehe, op="new", koerper=None, ebene="XY", offset=None, richtung=None, ziele=None):
    """Geschlossenes Vieleck skizzieren und extrudieren."""
    return [skizze(name, ebene, offset), linie(punkte, True), fertig(),
            extrusion(hoehe, op, name + "_E", koerper, richtung, ziele=ziele)]


def rechtecke(name, liste, hoehe, op="cut", offset=0.0, richtung=None, koerper=None, ziele=None):
    """Mehrere getrennte Rechtecke (x0, y0, x1, y1) in einer Skizze auf XY und extrudieren."""
    b = [skizze(name, "XY", offset)]
    b += [rechteck(*r) for r in liste]
    b += [fertig(), extrusion(hoehe, op, name + "_E", koerper, richtung, ziele=ziele)]
    return b


def profil_xz(name, punkte, laenge, op="new", koerper=None, offset=None):
    """Seitenprofil (x | z) auf der XZ-Ebene zeichnen und um 'laenge' in +Y extrudieren.
    Auf XZ zeigt die Skizzen-y nach −Z, darum wird z negiert."""
    pk = [[x, -z] for x, z in punkte]
    return [skizze(name, "XZ", offset), linie(pk, True), fertig(), extrusion(laenge, op, name + "_E", koerper)]


def profil_yz(name, punkte, laenge, op="new", koerper=None, offset=None):
    """Seitenprofil (y | z) auf der YZ-Ebene, Extrusion um 'laenge' in +X."""
    return [skizze(name, "YZ", offset), linie(punkte, True), fertig(), extrusion(laenge, op, name + "_E", koerper)]


def quader(name, x, y, z, l, b, h, op="new", ziele=None):
    """Achsparalleler Quader ab Ecke (x|y|z)."""
    p = {"length": l, "width": b, "height": h, "corner": [x, y, z], "operation": op, "name": name}
    if op == "new":
        p["body_name"] = name
    if ziele:
        p["targets"] = ziele
    return {"command": "solid.box", "params": p}


def zylinder(name, x, y, z, d, h, achse="Z", op="new", ziele=None):
    """Zylinder mit Grundmitte (x|y|z), Achse X/Y/Z oder Vektor."""
    p = {"diameter": d, "height": h, "base": [x, y, z], "axis": achse, "operation": op, "name": name}
    if op == "new":
        p["body_name"] = name
    if ziele:
        p["targets"] = ziele
    return {"command": "solid.cylinder", "params": p}


def verbinden(ziel, werkzeuge, behalten=False):
    return {"command": "solid.combine", "params": {"target": ziel, "tools": werkzeuge, "operation": "join",
                                                   "keep_tools": behalten}}


def ausschneiden(ziel, werkzeuge, behalten=False):
    return {"command": "solid.combine", "params": {"target": ziel, "tools": werkzeuge, "operation": "cut",
                                                   "keep_tools": behalten}}


def schnittmenge(ziel, werkzeuge, behalten=False):
    return {"command": "solid.combine", "params": {"target": ziel, "tools": werkzeuge, "operation": "intersect",
                                                   "keep_tools": behalten}}


def verschieben(koerper, dx=0, dy=0, dz=0, kopie=False):
    return {"command": "solid.move", "params": {"bodies": koerper, "translate": [dx, dy, dz], "copy": kopie}}


def drehen(koerper, achse, winkel, kopie=False):
    """Körper um eine Achse durch den Ursprung drehen (Winkel in Grad)."""
    return {"command": "solid.move", "params": {"bodies": koerper, "axis": achse, "angle": f"{winkel} deg",
                                                "copy": kopie}}


def entfernen(koerper):
    return {"command": "solid.remove", "params": {"bodies": koerper}}


def umbenennen(alt, neu):
    return {"command": "body.rename", "params": {"body": alt, "name": neu}}


def loch(x, y, z, d, tiefe=None, richtung=None, ziele=None, name=None):
    """Bohrung an einer Flächenposition."""
    p = {"position": [x, y, z], "diameter": d, "type": "simple"}
    if tiefe is not None:
        p["depth"] = tiefe
    if richtung:
        p["direction"] = richtung
    if ziele:
        p["targets"] = ziele
    if name:
        p["name"] = name
    return {"command": "solid.hole", "params": p}


# ---------------------------------------------------------------------------
# Oberflächenstruktur (Netz-Boolesche Operationen)
# ---------------------------------------------------------------------------
def _manifold_aus_trimesh(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, dtype=np.float32),
                               tri_verts=np.asarray(m.faces, dtype=np.uint32)))


def _trimesh_aus_manifold(m):
    g = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(g.vert_properties)[:, :3], faces=np.asarray(g.tri_verts), process=False)


def kastenliste_zu_manifold(kaesten):
    """Liste von Quadern (x0, y0, z0, x1, y1, z1) zu einem vereinigten Manifold."""
    teile = []
    for x0, y0, z0, x1, y1, z1 in kaesten:
        teile.append(mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0]))
    return mf.Manifold.batch_boolean(teile, mf.OpType.Add)


def ziegelfugen(x0, x1, y0, y1, z_oben, tiefe=0.15, schicht=0.6, fuge=0.2, stein=42 / 26, versatz_start=0.0):
    """Fugenkästen für Läuferverband auf einer waagerechten Fläche (Kachel liegt flach, Ansicht oben).
    Lagerfugen alle 'schicht', Stoßfugen alle 'stein', jede zweite Schicht um einen halben Stein versetzt."""
    k = []
    z0, z1 = z_oben - tiefe, z_oben + 1.0
    n = int((y1 - y0) / schicht) + 1
    for i in range(1, n + 1):
        yf = y0 + i * schicht
        if yf < y1 - 0.05:
            k.append((x0 - 1, yf - fuge / 2, z0, x1 + 1, yf + fuge / 2, z1))
    for i in range(n + 1):
        ya, yb = y0 + i * schicht, min(y0 + (i + 1) * schicht, y1)
        if ya >= y1:
            break
        ver = versatz_start + (stein / 2 if i % 2 else 0.0)
        x = x0 + ver
        while x < x1 + stein:
            if x0 + 0.15 < x < x1 - 0.15:
                k.append((x - fuge / 2, ya, z0, x + fuge / 2, yb, z1))
            x += stein
    return k


def lagerrillen(x0, x1, y0, y1, z_oben, abstand, breite, tiefe):
    """Waagerechte Rillen (z. B. Brettschalung) im Abstand 'abstand'."""
    k = []
    y = y0 + abstand
    while y < y1 - 0.05:
        k.append((x0 - 1, y - breite / 2, z_oben - tiefe, x1 + 1, y + breite / 2, z_oben + 1))
        y += abstand
    return k


# ---------------------------------------------------------------------------
# Bauen, prüfen, exportieren
# ---------------------------------------------------------------------------
def _cli(*args, **kw):
    return subprocess.run([CLI, *args], capture_output=True, text=True, **kw)


def bauen(name, befehle, gruppe, erwartet=None, struktur=None, ansicht="iso", info=None, kamera=None,
          koerperfarben=None):
    """Skript schreiben, auswerten, Volumen gegen die Handrechnung prüfen, als STEP/3MF/SC exportieren
    und ein Vorschaubild rendern.

    @param name      Dateiname des Teils (ohne Endung)
    @param befehle   Liste der SolidCraft-Befehle
    @param gruppe    Unterordner (z. B. "SA_03_Bahnsteig")
    @param erwartet  {Körpername: Sollvolumen mm³} aus der Handrechnung
    @param struktur  {Körpername: [Kästen]} – Fugen/Rillen, die nur ins 3MF eingerechnet werden
    @param info      Zusatzangaben für die Anleitung (Maße, Stück, Farbe, Druck …)
    """
    aus = WURZEL / gruppe
    aus.mkdir(parents=True, exist_ok=True)
    skript = aus / f"{name}.json"
    json.dump({"commands": befehle}, open(skript, "w"), indent=1, ensure_ascii=False)
    r = _cli("eval", str(skript))
    if r.returncode:
        print(f"FEHLER {name}: {r.stderr.strip()[:400]}")
        return None
    koerper = json.loads(r.stdout)["bodies"]
    fehler = [k for k in koerper if k.get("error")]
    for k in fehler:
        print(f"FEHLER {name}/{k['name']}: {k['error'][:300]}")
    if fehler:
        return None
    import re as _re0
    vol = {}
    for k in koerper:                                  # "Weiss (2)" zählt zu "Weiss"
        bn = _re0.sub(r" \(\d+\)$", "", k["name"]).split("__")[0]
        vol[bn] = round(vol.get(bn, 0) + k["volume_mm3"], 2)
    zu = all(k.get("closed") for k in koerper)
    pruef, ok = "", True
    if erwartet:
        for kname, soll in erwartet.items():
            ist = vol.get(kname)
            abw = None if ist is None else abs(ist - soll) / max(soll, 1e-9) * 100
            gut = abw is not None and abw < 0.5
            ok &= gut
            pruef += f" | {kname}: {ist} / soll {round(soll, 2)} {'OK' if gut else 'ABWEICHUNG'}"
    print(f"{name}: {len(vol)} Körper ({len(koerper)} Stücke), geschlossen={zu}{pruef or ' ' + str(vol)}")
    # Export: STEP (für Fusion), SC (SolidCraft), 3MF je Körper als STL-Zwischenschritt
    r = _cli("run", str(skript), "--out", str(aus / f"{name}.step"), "--out", str(aus / f"{name}_roh.3mf"),
             "--save", str(aus / f"{name}.sc"), "--quality", "fine", "--quiet")
    if r.returncode:
        print(f"EXPORTFEHLER {name}: {r.stderr[:300]}")
    netze = trimesh.load(aus / f"{name}_roh.3mf", force="scene")
    # Körpernamen den Netzen zuordnen (3MF-Objekte heißen wie die Körper)
    geom = {}
    import re as _re
    for g, m in netze.geometry.items():
        basisname = _re.sub(r" \(\d+\)$", "", g).split("__")[0]   # "Schrift (2)", "Weiss__Kreuze" -> Grundname
        geom[basisname] = trimesh.util.concatenate([geom[basisname], m]) if basisname in geom else m
    if struktur:
        for kname, kaesten in struktur.items():
            schluessel = next((g for g in geom if g.startswith(kname)), None)
            if schluessel is None:
                print(f"  Struktur: Körper {kname} nicht gefunden ({list(geom)})")
                continue
            basis = geom[schluessel]
            m = _manifold_aus_trimesh(basis)
            werkzeug = kaesten if isinstance(kaesten, mf.Manifold) else kastenliste_zu_manifold(kaesten)
            m = m - werkzeug
            geom[schluessel] = _trimesh_aus_manifold(m)
    szene = trimesh.Scene()
    for g, m in geom.items():
        szene.add_geometry(m, geom_name=g, node_name=g)
    szene.export(aus / f"{name}.3mf")
    (aus / f"{name}_roh.3mf").unlink(missing_ok=True)
    # Vorschaubild aus dem fertigen 3MF (mit Struktur)
    vorschau = aus / f"{name}_vorschau.json"
    json.dump({"commands": [{"command": "file.insert_mesh", "params": {"path": str(aus / f"{name}.3mf")}}]},
              open(vorschau, "w"))
    args = ["snapshot", str(vorschau), "--out", str(aus / f"{name}.png"), "--width", "1000", "--height", "700",
            "--no-grid", "--no-axes", "--quality", "fine"]
    if kamera:
        args += ["--camera", json.dumps(kamera)]
    else:
        args += ["--view", ansicht]
    for kname, farbe in (koerperfarben or {}).items():
        args += ["--body", f"{kname}:color={farbe}"]
    r = _cli(*args)
    if r.returncode:
        print(f"  Vorschau-Fehler {name}: {r.stderr[:200]}")
    vorschau.unlink(missing_ok=True)
    PROTOKOLL.append({"name": name, "gruppe": gruppe, "volumen": vol, "ok": ok and zu, "info": info or {}})
    return vol


def ellipsenpunkte(a, b, mz, w0, w1, n):
    """Punkte (x|z) einer Ellipse mit Halbachsen a (x) und b (z), Mittelpunkt (0|mz), Winkel w0…w1 (rad)."""
    return [[a * math.cos(w), mz + b * math.sin(w)] for w in np.linspace(w0, w1, n)]


# ---------------------------------------------------------------------------
# Flächen aus shapely-Polygonen
# ---------------------------------------------------------------------------
def ring_linien(koordinaten):
    """Einen geschlossenen Ring (Liste von Punkten) als Linienzug zeichnen."""
    pk = [[round(x, 4), round(y, 4)] for x, y in koordinaten]
    if pk[0] != pk[-1]:
        pk.append(pk[0])
    return linie(pk)


def flaeche(name, poly, hoehe, op="new", koerper=None, ebene="XY", offset=None, richtung=None, ziele=None):
    """shapely-(Multi)Polygon als Skizze zeichnen (Außenringe und Löcher) und extrudieren."""
    teile = list(poly.geoms) if hasattr(poly, "geoms") else [poly]
    b = [skizze(name, ebene, offset)]
    for p in teile:
        b.append(ring_linien(list(p.exterior.coords)))
        for loch_ring in p.interiors:
            b.append(ring_linien(list(loch_ring.coords)))
    b += [fertig(), extrusion(hoehe, op, name + "_E", koerper, richtung, ziele=ziele)]
    return b


def text(name, inhalt, x, y, hoehe, dicke, ebene, op="new", koerper=None, ausrichtung="center", ziele=None):
    """Erhabene Schrift auf einer Ebene."""
    return [skizze(name, ebene),
            {"command": "sketch.text", "params": {"text": inhalt, "at": [x, y], "height": hoehe, "align": ausrichtung,
                                                  "font": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"}},
            fertig(), dict(extrusion(dicke, op, name + "_E", koerper, ziele=ziele),
                           params={**extrusion(dicke, op, name + "_E", koerper, ziele=ziele)["params"],
                                   "touching": "one_body"})]


# Ebene der Vorderseite (y = y0), Skizzen-x = Welt-X, Skizzen-y = Welt-Z, Normale = −Y (nach außen)
def front_ebene(y0=0.0):
    return {"origin": [0, y0, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}
