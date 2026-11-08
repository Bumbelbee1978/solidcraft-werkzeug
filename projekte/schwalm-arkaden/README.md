# Nächster Halt: Schwalm-Arkaden

Spur-N-Bahnhofsmodul (FREMO N-RE) – alle 81 Druckteile, konstruiert mit SolidCraft, für Bambu Lab A1 mit AMS lite.

## Inhalt

| Datei | Zweck |
|---|---|
| `Schwalm_Arkaden_SolidCraft_Teile.zip` | Alle Teile (Ordner SA_01 … SA_09): `.3mf` zum Drucken (Fugen/Rillen eingerechnet), `.step` für Fusion, `.sc`, `.json`, `.png` |
| `Schwalm_Arkaden_Einzelteile_Bildanleitung.docx` | Bildanleitung: Steckbrief je Teil, Montagebilder, Dach-Bauschritte, Druckplan |
| `skripte/` | Python-Skripte, aus denen alle Teile entstehen |

## Teile neu erzeugen

```bash
# SolidCraft einrichten (siehe README im Hauptordner), dann:
pip install --break-system-packages trimesh manifold3d shapely
cd projekte/schwalm-arkaden/skripte
python3 alle_teile.py        # erzeugt teile/SA_* und prüft jedes Volumen gegen die Handrechnung
python3 abb_szenen.py        # Montagebilder (optional)
```

| Skript | Baugruppe |
|---|---|
| `sa_basis.py` | Bausteine, Prüfung, Export, Oberflächenstruktur (manifold3d) |
| `sa01_arkaden.py` … `sa08_stadt.py` | Arkaden, Läden, Bahnsteige, Aufgänge, Stahl, Beton, Ausstattung, Stadthäuser |
| `sa09_dach.py` | Rautengitter-Dach aus Einzelbögen, Kollisionsprüfung (`python3 sa09_dach.py pruefen`) |
| `karten.py`, `abbildungen.py`, `abb_szenen.py`, `zuschnitt.py` | Steckbriefe und Bilder für die Anleitung |

Spiel der Dach-Überblattungen: `SPIEL` in `sa09_dach.py` (Standard 0,1 mm).
