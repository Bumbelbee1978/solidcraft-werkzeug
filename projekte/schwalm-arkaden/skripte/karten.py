"""
Steckbriefe aller Teile für die Bildanleitung -> teile/karten.json.
Je Teil: Titel, Stückzahl, Farben (Körper -> Farbe), Düse/Schicht, Lage beim Druck, Hinweise.
Maße und Volumen kommen aus teile/protokoll.json, das Bild wird auf den Inhalt zugeschnitten.
"""
import json
from pathlib import Path

from zuschnitt import zuschneiden

WURZEL = Path(__file__).parent
TEILE = WURZEL / "teile"
BILDER = WURZEL / "abb" / "teile"
BILDER.mkdir(parents=True, exist_ok=True)

D2 = "0,2 · 0,08 mm"
D4 = "0,4 · 0,12 mm"
D4G = "0,4 · 0,16 mm"
FLACH = "flach, wie in der Datei (Ansichtsseite oben)"
WIE = "wie in der Datei"

# (Name, Titel, Stück, Farben, Düse, Lage, [Hinweise])
K = [
    # ---------------- SA_01 Arkaden ----------------
    ("Bogenkachel_42", "Bogenkachel 42", "26", "Kachel: Ziegelrot · Sandstein: Sandstein/Elfenbein", D2, FLACH,
     ["Ziegelfugen 0,2 × 0,15 und Radialfugen der Rollschicht sind im 3MF schon eingerechnet.",
      "6–8 Kacheln pro Platte – die Farbe wechselt nur in den obersten Schichten.",
      "Auf den Viaduktkern (Styrodur 30 mm oder Sperrholz) kleben, Fugen laufen über die Stöße weiter."]),
    ("Durchlasskachel_36", "Durchlasskachel 36 (Promenade)", "2", "Kachel: Ziegelrot · Sandstein", D2, FLACH,
     ["Bogen 30 breit, Kämpfer 15, Scheitel 30 – für den Fußgängerdurchlass an der Promenade."]),
    ("Wandkachel_3", "Wandkachel 3", "nach Bedarf", "Kachel: Ziegelrot · Sandstein", D2, FLACH,
     ["Passstück für Ecken und Fugen."]),
    ("Wandkachel_6", "Wandkachel 6", "nach Bedarf", "Kachel: Ziegelrot · Sandstein", D2, FLACH, []),
    ("Wandkachel_7", "Wandkachel 7", "nach Bedarf", "Kachel: Ziegelrot · Sandstein", D2, FLACH, []),
    ("Wandkachel_14", "Wandkachel 14", "nach Bedarf", "Kachel: Ziegelrot · Sandstein", D2, FLACH, []),
    ("Wandkachel_27", "Wandkachel 27", "nach Bedarf", "Kachel: Ziegelrot · Sandstein", D2, FLACH,
     ["Andere Längen: im Skript sa01_arkaden.py die Liste bei wandkachel() ergänzen."]),
    ("Laibung_50", "Bogenlaibung 50", "3", "Ziegelrot", D4, "stehend (Bogen oben, Länge senkrecht)",
     ["Halbschale innen r 18,0 – sitzt in der Bogenöffnung hinter den Kacheln."]),
    ("Laibung_60", "Bogenlaibung 60", "1", "Ziegelrot", D4, "stehend", []),
    ("Laibung_186", "Bogenlaibung 186", "9", "Ziegelrot", D4, "stehend (186 hoch, passt in 256)",
     ["Langer Druck: Rand (Brim) 5 mm gegen Umkippen."]),
    # ---------------- SA_02 Läden ----------------
    ("Ladeneinsatz_Kiosk", "Ladeneinsatz Kiosk", "1", "Laden: Hell · Holz: Braun · Schrift: Weiß", D4, WIE + " (unten offen)",
     ["Passt in die 36-mm-Bogenöffnung: bei Höhe 24 bleibt 0,1 Luft je Seite.",
      "Thekenbrett ragt 1,5 vor – druckt ohne Stütze.", "Fenster: Folie von innen einkleben."]),
    ("Ladeneinsatz_Imbiss", "Ladeneinsatz Imbiss", "1", "wie Kiosk", D4, WIE, []),
    ("Ladenfront", "Ladenfront (Bäcker, Supermarkt)", "5", "Rahmen: Braun oder Grün", D2, FLACH,
     ["Tür 0,4 vertieft, Schaufenster mit Sprossen offen.", "Folie von hinten in den 0,25-Falz kleben."]),
    ("Portal", "Portal (Passage, Brauhaus)", "7", "Rahmen: Braun", D2, FLACH, ["Zweiflügelige Tür mit zwei Glasfeldern."]),
    ("Fenster", "Fenster (Brauhaus Nord)", "3", "Rahmen: Braun", D2, FLACH, ["Brüstung bis 6, Fenster mit Kreuzsprosse."]),
    ("Faecher_Oberlicht", "Fächer-Oberlicht", "15", "Weiß", D2, FLACH,
     ["Sitzt über jeder Ladenfront, jedem Portal und Fenster im Bogenfeld.", "Folie hinter die sechs Felder kleben."]),
    # ---------------- SA_03 Bahnsteig ----------------
    ("Bahnsteig_C1_Normal_200", "Bahnsteig C1 Normalstück 200", "4", "Bahnsteig: Hellgrau · Weiss: Weiß", D4G, FLACH,
     ["Kragkante 1,5 × 3,0 an beiden Seiten.", "Zapfen 4 × 4 am Ende, Tasche 4,4 × 4,4 am Anfang."]),
    ("Bahnsteig_C1k_Kurz_103", "Bahnsteig C1k Kurzstück 103", "2", "wie C1", D4G, FLACH, []),
    ("Bahnsteig_C2_Ende_200", "Bahnsteig C2 Endstück 200 (Rampe vorn)", "2", "wie C1", D4G, FLACH,
     ["Rampe 1 : 5 über 30 mm, nur Zapfen am Ende."]),
    ("Bahnsteig_C2k_Ende_97", "Bahnsteig C2k Endstück 97 (Rampe hinten)", "2", "wie C1", D4G, FLACH,
     ["Rampe am Ende, nur Tasche am Anfang."]),
    ("Bahnsteig_C3_Aufgang_200", "Bahnsteig C3 Aufgangsstück 200", "2", "wie C1", D4G, FLACH,
     ["Treppenauge 65 × 18, Aufzugsöffnung 15 × 12.",
      "Löcher Ø 0,7 alle 8 mm für ein Geländer aus Messingdraht 0,5."]),
    # ---------------- SA_04 Aufgänge ----------------
    ("Treppe", "Festtreppe mit Podest", "2", "Hellgrau", D2, "auf der Seite liegend (in Bambu: F → große Seitenfläche)",
     ["2 × 25 Stufen 2,2 / 1,22 (29°), Podest 25 lang auf 30,5.", "Auf der Seite gedruckt werden alle Stufenkanten scharf."]),
    ("Treppenwange", "Treppenwange (Glasrahmen)", "4", "Anthrazit", D2, FLACH,
     ["Je Treppe zwei Stück, links und rechts ankleben.", "Folie in die drei Felder."]),
    ("Treppenstuetze", "Podeststütze", "4", "Hellgrau", D4, FLACH, ["Steckt 3 mm tief in den Taschen unter dem Podest."]),
    ("Rolltreppe", "Rolltreppe", "2", "Wanne: Anthrazit · Stufenband: Silber", D2, "auf der Seite liegend (F → Seitenfläche)",
     ["30° Neigung, Stufenrillen im 3MF eingerechnet."]),
    ("Rolltreppenwange", "Rolltreppenwange mit Handlauf", "4", "Anthrazit", D2, FLACH, ["Steht 5 mm über das Stufenband."]),
    ("Aufzug_Laengsseite", "Aufzug Längsseite 15 × 83", "4", "Anthrazit", D2, FLACH, ["Folie innen flächig aufkleben."]),
    ("Aufzug_Schmalseite_Tuer_unten", "Aufzug Schmalseite, Tür unten", "2", "Anthrazit", D2, FLACH, ["Straßenseite."]),
    ("Aufzug_Schmalseite_Tuer_oben", "Aufzug Schmalseite, Tür oben", "2", "Anthrazit", D2, FLACH, ["Bahnsteigseite (Tür auf 60,6)."]),
    ("Aufzug_Dach", "Aufzug Dach", "2", "Anthrazit", D4, WIE, ["Rille 0,8 × 0,8 unten für die LED-Litze (Technik-Plan)."]),
    ("Aufzug_Boden", "Aufzug Boden", "2", "Anthrazit", D4, WIE, []),
    ("Aufzug_Kabine", "Aufzug Kabine", "2", "Silber", D2, "offene Seite nach oben", ["13 × 10 × 14, offene Seite zur Tür."]),
    # ---------------- SA_05 Stahl ----------------
    ("Aussentraeger_3_Felder", "Einheitsträger Typ V, 3 Felder (Vorplatz)", "2", "Tannengrün", D2, FLACH,
     ["Alle Brücken haben denselben Träger: Feld 18, Höhe 12, Gurte 3 dick mit Knotenblechen."]),
    ("Aussentraeger_6_Felder", "Einheitsträger Typ V, 6 Felder (Schwalm)", "2", "Tannengrün", D2, FLACH, []),
    ("Aussentraeger_8_Felder", "Einheitsträger Typ V, 8 Felder (Straße)", "2", "Tannengrün", D2, FLACH, []),
    ("Fahrbahnplatte_54", "Fahrbahnplatte 54", "1", "Betongrau", D4G, "kopfüber: Platte unten, Rippen oben (wie in der Datei)",
     ["Querträger alle 18 mm, Längsträger unter den Bahnsteigen."]),
    ("Fahrbahnplatte_108", "Fahrbahnplatte 108", "1", "Betongrau", D4G, "wie 54", []),
    ("Fahrbahnplatte_144", "Fahrbahnplatte 144", "1", "Betongrau", D4G, "wie 54", []),
    ("Gitterstuetze", "Gitterstütze 43", "12", "Tannengrün", D2, "liegend (F → Seitenfläche)",
     ["X-Gitter-Rillen auf allen vier Seiten im 3MF.", "6 Stück pro Platte."]),
    ("Bogenrippe_Schwalm", "Bogenrippe Schwalm", "4", "Tannengrün", D2, FLACH,
     ["Rundbogen über die Schwalm statt Pfeiler: r 49 / 53, Ständer bei ±27, ±36, ±45.",
      "2 außen, 2 innen; Kämpferfüße stehen 1 mm vor."]),
    # ---------------- SA_06 Beton ----------------
    ("Betonwand_Feld", "Betonwand-Feld 45 × 61", "10", "Betongrau", D4, FLACH,
     ["Brettschalung (0,8-Bretter) im 3MF.", "Halbe Dehnfugen an beiden Rändern: zwei Felder ergeben 0,4."]),
    ("Kappe_225", "Wandkappe 225 mit Tropfnase", "2", "Hellgrau", D4, "liegend, wie in der Datei",
     ["Nut 3,1 × 0,6 unten sitzt auf der Wandkante."]),
    ("Kabeltrog_225", "Kabeltrog 225", "2", "Hellgrau", D4, WIE, ["Deckelfugen alle 6 mm."]),
    # ---------------- SA_07 Ausstattung ----------------
    ("Doppelsitzbank", "Doppelsitzbank", "4", "Anthrazit", D2, WIE, ["Lehne 0,8 – Rücken an Rücken."]),
    ("Parkbank", "Parkbank", "6", "Holzbraun", D2, WIE, []),
    ("Marktstand", "Marktstand", "4", "Holzbraun", D2, WIE, ["Auslage mit drei Fächern, Pfosten vorn 13, hinten 17."]),
    ("Markise", "Markise", "4", "Markise: Rot · Streifen: Weiß", D2, FLACH, ["Auf die Pfosten kleben, vorn tiefer."]),
    ("Fahrradstation", "Fahrradstation", "1", "Anthrazit", D2, WIE,
     ["16 Löcher Ø 0,7 für 8 Bügel aus Messingdraht 0,5 (U 5 breit, 5,5 hoch)."]),
    ("Fahrradstation_Dach", "Fahrradstation Dach", "1", "Anthrazit", D2, FLACH, ["Folie in den Rahmen."]),
    ("Zugzielanzeiger", "DB-Zugzielanzeiger", "8", "Gehäuse: Verkehrsblau · Anzeige: Weiß", D2, FLACH + " (Anzeige oben)",
     ["6 für die Bahnsteige, 2 für die Tram.", "Zwei Löcher Ø 0,7 oben zum Aufhängen am Draht."]),
    ("Pavillon_Rueckwand", "DB-Wartepavillon Rückwand", "4", "Rahmen: Anthrazit · Fahrplan: Gelb", D2, FLACH, []),
    ("Pavillon_Stirnseite", "DB-Wartepavillon Stirnseite", "8", "Anthrazit", D2, FLACH, []),
    ("Pavillon_Dach", "DB-Wartepavillon Dach", "4", "Anthrazit", D4, WIE, ["Tasche unten für eine SMD-LED."]),
    ("Tramhaus_Rueckwand", "Tram-Wartehaus Rückwand", "3", "Anthrazit", D2, FLACH, []),
    ("Tramhaus_Dach", "Tram-Wartehaus Dach", "3", "Blau", D4, WIE, []),
    ("Tramhaus_Bank", "Tram-Wartehaus Bank", "3", "Anthrazit", D2, WIE, []),
    ("Fahrkartenautomat", "Fahrkartenautomat", "5", "Automat: Rot · Display: Anthrazit", D2, "stehend", []),
    ("Laterne_Fuss_Kopf", "Kandelaber-Laterne (Fuß + Kopf)", "20", "Anthrazit", D2, WIE,
     ["Mast: Messingdraht 0,5 × 24 in beide Löcher Ø 0,6."]),
    ("Brunnen", "Brunnen", "1", "Sandstein", D2, WIE, []),
    ("Litfasssaeule", "Litfaßsäule", "1", "Dunkelgrün", D2, WIE, ["Plakate als bedruckte Papierstreifen."]),
    ("Tram_Steig", "Tram-Steig 150", "2", "Steig: Hellgrau · Leit: Weiß", D4G, FLACH, ["Rampen 10 an beiden Enden."]),
    # ---------------- SA_08 Stadt ----------------
    ("Haus_Fassade_34", "Gründerzeithaus Fassade 34", "13", "Putz · Weiss: Gesimse/Rahmen · Tuer: Dunkelgrau", D2, FLACH,
     ["Fenster offen – Folie hinten flächig aufkleben.", "Varianten (Erker, Läden, Schilder): Skript sa08_stadt.py."]),
    ("Haus_Fassade_30", "Gründerzeithaus Fassade 30 (schmal)", "1", "wie 34", D2, FLACH, []),
    ("Haus_Seitenwand", "Haus Seitenwand 63 × 100", "28", "Putz", D4, FLACH, ["Zwei je Haus; bei Reihenhäusern reicht eine gemeinsame Wand."]),
    ("Haus_Rueckwand_30.8", "Haus Rückwand (für 34)", "13", "Putz", D4, FLACH, []),
    ("Haus_Rueckwand_26.8", "Haus Rückwand (für 30)", "1", "Putz", D4, FLACH, []),
    ("Haus_Mansarddach_34", "Mansarddach 34 mit 2 Gauben", "13", "Schiefergrau", D4, "stehend (unten offen)", []),
    ("Haus_Mansarddach_30", "Mansarddach 30 mit 1 Gaube", "1", "Schiefergrau", D4, "stehend", []),
    ("Haus_Deckenplatte_30.8", "Deckenplatte (für 34)", "26", "beliebig", D4, FLACH, ["Zwei je Haus, später Träger für die Beleuchtung."]),
    ("Haus_Deckenplatte_26.8", "Deckenplatte (für 30)", "2", "beliebig", D4, FLACH, []),
    # ---------------- SA_09 Dach ----------------
    ("Bogen_A", "Bogen A (Plus-Neigung)", "9", "Silbergrau", D2, "flach, wie in der Datei",
     ["Kerben außen: 2 Kreuzungen + 2 Füße (halbe Fußbohrung)."]),
    ("Bogen_B", "Bogen B (Minus-Neigung)", "9", "Silbergrau", D2, "flach", ["Kerben innen: 2 Kreuzungen + 2 Füße."]),
    ("Teilbogen_A5_West", "Teilbogen A5 West", "1", "Silbergrau", D2, "flach", ["Beginnt auf Höhe 47,9, Enden am Stirnbogen."]),
    ("Teilbogen_B5_Ost", "Teilbogen B5 Ost", "1", "Silbergrau", D2, "flach", []),
    ("Kappe_A6_West", "Kappe A6 West", "1", "Silbergrau", D2, "flach", ["Beginnt auf Höhe 95,7, keine Kerben."]),
    ("Kappe_B6_Ost", "Kappe B6 Ost", "1", "Silbergrau", D2, "flach", []),
    ("Stirnbogen_West", "Stirnbogen West", "1", "Silbergrau", D2, "flach",
     ["Ebene 34,29° geneigt; am Fußknoten passend für die letzten Bögen A/B ausgeschnitten."]),
    ("Stirnbogen_Ost", "Stirnbogen Ost", "1", "Silbergrau", D2, "flach", []),
    ("Fussschwelle_1", "Fußschwelle Stück 1 (230)", "2", "Silbergrau", D4, FLACH,
     ["400 mm passen nicht auf das Bett – darum zwei Stücke, Stoß zwischen zwei Löchern."]),
    ("Fussschwelle_2", "Fußschwelle Stück 2 (180)", "2", "Silbergrau", D4, FLACH, []),
    ("Montagespant", "Montagespant (Lehre)", "5", "beliebig (Resteverwertung)", D4, FLACH,
     ["Nur Hilfsteil: hält die Bögen beim Zusammenbau, 0,2 Luft zur Bogeninnenseite."]),
]


def main():
    prot = {e["name"]: e for e in json.load(open(TEILE / "protokoll.json"))}
    karten = []
    for name, titel, stueck, farben, duese, lage, hinweise in K:
        e = prot[name]
        quelle = TEILE / e["gruppe"] / f"{name}.png"
        ziel = BILDER / f"{name}.png"
        zuschneiden(quelle, ziel, rand=20)
        g = 1.24 * e["volumen_gesamt"] / 1000      # PLA 1,24 g/cm³
        karten.append({"name": name, "gruppe": e["gruppe"], "titel": titel, "stueck": stueck, "farben": farben,
                       "duese": duese, "lage": lage, "hinweise": hinweise, "masse": e["masse"],
                       "gramm": round(g, 1), "bild": str(ziel), "ok": e["ok"]})
    fehlend = set(prot) - {k[0] for k in K}
    if fehlend:
        print("Ohne Steckbrief:", fehlend)
    json.dump(karten, open(TEILE / "karten.json", "w"), indent=1, ensure_ascii=False)
    print(len(karten), "Steckbriefe")


if __name__ == "__main__":
    main()
