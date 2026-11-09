# Alsfeld BHF (Arbeitstitel, unter Vorbehalt)

Spur-N-Heimanlage auf 2 × 1 m (Peco Code 55, Unifrog): Schattenbahnhof unten, zweigleisige PETG-Wendel auf der
Erweiterung an der Westseite, oben 4-gleisiger Bahnhof mit gläserner Empfangsbrücke, Glasdach im Elbbrücken-Stil,
Doppelaufzug mit Rechtecktreppe, Rangiergruppe mit Containerverladung, kleiner Hafen, Ort auf der Anhöhe mit Tram-Rundkurs.

## Inhalt

| Datei | Zweck |
|---|---|
| `Alsfeld_BHF_Teile.zip` | Bisher konstruierte Teile (17): `.3mf`, `.step`, `.sc`, `.json`, `.png` |
| `skripte/teile.py` | Erzeugt alle Teile (Wendel-Konsolen, Anlaufklötze, Ausfahrplatte, TPU-Bettung, Aufzug, Treppe, Stufenplateau) |
| `skripte/aufzug_bildanleitung.py` | Bild-Bauanleitung für den beweglichen Aufzug |

## Teile

| Gruppe | Teile |
|---|---|
| HA_02 Wendel-Konsolen | Konsole innen/außen, Sonderkonsole 60° |
| HA_03 Gleisbettung (TPU 95A) | Bettung innen/außen, 15° und 30° |
| HA_04 Anlaufklötze | Stöße 1–4, innen und außen |
| HA_05 Ausfahrplatte | obere Ausfahrt Richtung Osten |
| HA_11 Aufzug und Treppe | Turm-Faltwand, Schacht, Glasschacht, Boden/Kopf, Kabine, Servohalter, Servohebel, Treppenläufe |
| HA_15 Stufenplateau | Industrie-Eingang |

## Neu erzeugen

```bash
cd projekte/alsfeld-bhf/skripte
python3 teile.py            # alle Teile, oder: python3 teile.py HA_11_Kabine
```

Druckwerte: Schwalbenschwanz-Spiel 0,15 mm je Seite, Faltwände mit 0,2-Düse und 0,1-mm-Schicht, Klarteile aus PET-Folie 0,2 mm.

## Wendel v2 (09.11.2026, Ratsbeschluss: keine Schrauben im Plattenmaterial)

- Schwalbenschwänze verkleben (dünner Sekundenkleber, ggf. mit Primer)
- Außen: Gewindestange durch die halben Löcher an der Fuge, dazu zwei Stifte Ø 4 × 3 mm (R 343, 10 mm neben der Fuge)
- Innen: Konsole mit zwei Stiften Ø 4 × 3 mm (R 258, 10 mm neben der Fuge), Platte mit Sacklanghloch 4,4 × 5 × 3,4 mm von unten
- Höhe nur über Mutter und Kontermutter einstellen
- TPU-Bettung mit Anschlagnasen (6 × 1 mm) bis an Randleiste bzw. Leitkante, Nasen 5° vom Streifenende

`skripte/HA_01_Wendelplatte.json` ist das Grundskript der Platte, `wendelplatte_v2()` baut daraus die neue Version.
`druck/` enthält die zusammengestellten Druckplatten (Testsatz, Passprobe, TPU-Testsatz) und `testsatz.py` zum Anordnen.
