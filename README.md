# SolidCraft-Werkzeug

Fertig gebautes **SolidCraft-CLI** (Linux x86-64) plus Andys Hilfsskripte für 3D-Druckteile (Spur N, Bambu A1).

- Quelle: https://github.com/tangency-labs/solidcraft (Commit 98fdb6e), Lizenz MIT/Apache-2.0 – siehe `lizenz/`
- Programm: als Release-Anhang `solidcraft-cli-linux-x86_64.tar.gz` (zu groß fürs Repo)

## Einrichten in einer neuen Sitzung

```bash
mkdir -p ~/bin && cd ~/bin
curl -L -o sc.tar.gz https://github.com/Bumbelbee1978/solidcraft-werkzeug/releases/latest/download/solidcraft-cli-linux-x86_64.tar.gz
tar xzf sc.tar.gz && rm sc.tar.gz && ./solidcraft-cli --help | head -3
```

## Inhalt

| Datei | Zweck |
|---|---|
| `lib/teile.py` | Hilfsfunktionen (Skizze, Bogen, Ringsektor, Faltwand mit V-Nut, Löcher) und alle Teile der Heimanlage |
| `lib/aufzug_bildanleitung.py` | Beispiel für eine Bild-Bauanleitung: Szenen rendern, beschriften |
