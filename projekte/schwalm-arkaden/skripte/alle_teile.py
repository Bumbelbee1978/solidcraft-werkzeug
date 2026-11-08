"""Alle Teile der Schwalm-Arkaden neu erzeugen und ein Protokoll (teile/protokoll.json) schreiben."""
import json
import trimesh
import sa_basis
import sa01_arkaden, sa02_laeden, sa03_bahnsteig, sa04_aufgaenge, sa05_stahl, sa06_beton, sa07_ausstattung, sa08_stadt, sa09_dach

for modul in (sa01_arkaden, sa02_laeden, sa03_bahnsteig, sa04_aufgaenge, sa05_stahl, sa06_beton, sa07_ausstattung,
              sa08_stadt, sa09_dach):
    modul.alle()
sa09_dach.zusammenbau_pruefen(str(sa_basis.WURZEL / sa09_dach.G / "Dach_Zusammenbau_Einbaulage.3mf"))

# Maße aus den fertigen 3MF-Dateien (Druck- bzw. Konstruktionslage)
for e in sa_basis.PROTOKOLL:
    s = trimesh.load(sa_basis.WURZEL / e["gruppe"] / f"{e['name']}.3mf", force="scene")
    lo, hi = s.bounds
    e["masse"] = [round(float(v), 1) for v in (hi - lo)]
    e["volumen_gesamt"] = round(sum(e["volumen"].values()), 1)
json.dump(sa_basis.PROTOKOLL, open(sa_basis.WURZEL / "protokoll.json", "w"), indent=1, ensure_ascii=False)
fehler = [e["name"] for e in sa_basis.PROTOKOLL if not e["ok"]]
print(f"{len(sa_basis.PROTOKOLL)} Teile, nicht OK: {fehler}")
