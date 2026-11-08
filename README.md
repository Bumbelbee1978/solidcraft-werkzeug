# SolidCraft-Werkzeug

Fertig gebautes **SolidCraft-CLI** (Linux x86-64) plus Andys Hilfsskripte für 3D-Druckteile (Spur N, Bambu A1).

- Quelle: https://github.com/tangency-labs/solidcraft (Commit 98fdb6e), Lizenz MIT/Apache-2.0 – siehe `lizenz/`
- Programm: `bin/solidcraft-cli-linux-x86_64.tar.gz` (gestrippt, gepackt ca. 49 MB)

## Einrichten in einer neuen Sitzung

```bash
mkdir -p ~/bin && cd ~/bin
git clone --depth 1 https://github.com/Bumbelbee1978/solidcraft-werkzeug /tmp/scw
cp /tmp/scw/bin/solidcraft-cli-linux-x86_64.tar.gz sc.tar.gz
tar xzf sc.tar.gz && rm sc.tar.gz && ./solidcraft-cli --help | head -3
```

## Inhalt

| Datei | Zweck |
|---|---|
| `lib/teile.py` | Hilfsfunktionen (Skizze, Bogen, Ringsektor, Faltwand mit V-Nut, Löcher) und alle Teile der Heimanlage |
| `lib/aufzug_bildanleitung.py` | Beispiel für eine Bild-Bauanleitung: Szenen rendern, beschriften |
| `projekte/alsfeld-bhf/` | Heimanlage „Alsfeld BHF“ (Arbeitstitel): Wendel- und Bahnhofsteile, Skripte |
| `projekte/schwalm-arkaden/` | Bahnhofsmodul „Nächster Halt: Schwalm-Arkaden“: 81 Teile (ZIP), Skripte, Bildanleitung |
