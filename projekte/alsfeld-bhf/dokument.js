/**
 * Baut das Word-Dokument „Heimanlage Spur N – Bahnhof & Gleiswendel“.
 * Aufbau wie bei den Schwalm-Arkaden: Bausteine Schritt, Dialog, Kasten, Kontrolle, Achtung, Tipp, Tabelle, Bild.
 */
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType,
  HeadingLevel, WidthType, ShadingType, BorderStyle, Header, Footer, PageNumber, PageBreak,
  LevelFormat, VerticalAlign,
} = require("docx");

// ---------- Grundwerte ----------
const SCHRIFT = "Arial";
const BREITE = 9638; // Satzspiegel A4 bei 2 cm Rand (DXA)
const FARBE = { titel: "1F3A5A", text: "2C2C2A", grau: "5F5E5A", linie: "B4B2A9" };
const KASTEN = {
  tipp: { titel: "Tipp", rand: "1D9E75", grund: "E1F5EE" },
  achtung: { titel: "Achtung", rand: "D85A30", grund: "FAECE7" },
  kontrolle: { titel: "Kontrolle", rand: "378ADD", grund: "E6F1FB" },
  info: { titel: "Hinweis", rand: "888780", grund: "F1EFE8" },
};
const RAND_DUENN = { style: BorderStyle.SINGLE, size: 4, color: FARBE.linie };
const RAENDER = { top: RAND_DUENN, bottom: RAND_DUENN, left: RAND_DUENN, right: RAND_DUENN };

/** Liest Breite/Höhe einer PNG-Datei aus dem Dateikopf. */
function pngMasse(datei) {
  const b = fs.readFileSync(datei);
  return { b: b.readUInt32BE(16), h: b.readUInt32BE(20), daten: b };
}

/** Fließtext; unterstützt **fett** im Text. */
function absatz(text, opt = {}) {
  const teile = text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean).map((t) =>
    t.startsWith("**") ? new TextRun({ text: t.slice(2, -2), bold: true }) : new TextRun(t));
  return new Paragraph({ children: teile, spacing: { after: 120, line: 290 }, ...opt });
}

/** Aufzählungspunkt. */
function punkt(text) {
  return absatz(text, { numbering: { reference: "punkte", level: 0 }, spacing: { after: 60, line: 280 } });
}

/** Zähler für die automatische Kapitelnummerierung und Sprungmarken für Verweise. */
let kapNr = 0, absNr = 0;
const ANKER = {};
/** Sammelt alle Überschriften für das Inhaltsverzeichnis. */
let VERZ = [];
/** Kapitelüberschrift – Nummer wird automatisch vergeben, id dient als Sprungmarke für ref(). */
let aktKap = "";
function h1(t, id, umbruch = true, anhang = null) {
  absNr = 0;
  const titel = t.replace(/^\d+\s+/, "");
  let text;
  if (anhang) { aktKap = anhang; text = `Anhang ${anhang} – ${titel}`; if (id) ANKER[id] = `Anhang ${anhang}`; }
  else { kapNr += 1; aktKap = String(kapNr); text = `${kapNr} ${titel}`; if (id) ANKER[id] = String(kapNr); }
  VERZ.push({ ebene: 1, text });
  return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)], pageBreakBefore: umbruch });
}
/** Abschnittsüberschrift – Nummer automatisch, setzt die Schrittzählung zurück. */
function h2(t, id) {
  absNr += 1; schrittNr = 0;
  const titel = t.replace(/^\d+\.\d+\s+/, "");
  if (id) ANKER[id] = `${aktKap}.${absNr}`;
  VERZ.push({ ebene: 2, text: `${aktKap}.${absNr} ${titel}` });
  return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(`${aktKap}.${absNr} ${titel}`)] });
}
/** Verweis auf eine Sprungmarke (Nummer aus dem ersten Durchlauf). */
const ref = (id) => ANKER[id] || "?";
const h3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] });

/** Arbeitsschritt mit fortlaufender Nummer je Abschnitt. */
let schrittNr = 0;
function neueSchritte() { schrittNr = 0; }
function schritt(titel, ...zeilen) {
  schrittNr += 1;
  const kopf = new Paragraph({
    keepNext: true, spacing: { before: 160, after: 60 },
    children: [new TextRun({ text: `Schritt ${schrittNr}  `, bold: true, color: FARBE.titel }), new TextRun({ text: titel, bold: true })],
  });
  return [kopf, ...zeilen.map((z) => absatz(z, { indent: { left: 360 }, spacing: { after: 80, line: 280 } }))];
}

/** Zelle mit Text und optionaler Hintergrundfarbe. */
function zelle(text, breite, opt = {}) {
  return new TableCell({
    width: { size: breite, type: WidthType.DXA }, borders: RAENDER, verticalAlign: VerticalAlign.CENTER,
    shading: opt.grund ? { fill: opt.grund, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: [new TextRun({ text, bold: !!opt.fett, size: 19 })] })],
  });
}

/** Tabelle mit Kopfzeile. */
function tabelle(kopf, zeilen, breiten) {
  const summe = breiten.reduce((a, b) => a + b, 0);
  return [new Table({
    width: { size: summe, type: WidthType.DXA }, columnWidths: breiten,
    rows: [
      new TableRow({ tableHeader: true, children: kopf.map((k, i) => zelle(k, breiten[i], { fett: true, grund: "E6E3DC" })) }),
      ...zeilen.map((z) => new TableRow({ children: z.map((w, i) => zelle(String(w), breiten[i])) })),
    ],
  }), new Paragraph({ spacing: { after: 120 }, children: [] })];
}

/** Fusion-Dialog: Feld → Eintrag. */
function dialog(titel, felder) {
  const b = [3600, BREITE - 3600];
  return [
    new Paragraph({ keepNext: true, spacing: { before: 80, after: 40 }, indent: { left: 360 },
      children: [new TextRun({ text: `Dialog „${titel}“`, bold: true, size: 19, color: FARBE.grau })] }),
    new Table({
      width: { size: BREITE - 360, type: WidthType.DXA }, columnWidths: [3600 - 360, BREITE - 3600], indent: { size: 360, type: WidthType.DXA },
      rows: felder.map(([f, w]) => new TableRow({ children: [zelle(f, 3600 - 360, { grund: "F1EFE8" }), zelle(w, BREITE - 3600)] })),
    }),
    new Paragraph({ spacing: { after: 100 }, children: [] }),
  ];
}

/** Farbiger Hinweiskasten (Tipp, Achtung, Kontrolle, Hinweis). */
function kasten(typ, ...zeilen) {
  const k = KASTEN[typ];
  const linie = { style: BorderStyle.SINGLE, size: 24, color: k.rand };
  const ohne = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  return [new Table({
    width: { size: BREITE, type: WidthType.DXA }, columnWidths: [BREITE],
    rows: [new TableRow({ cantSplit: true, children: [new TableCell({
      width: { size: BREITE, type: WidthType.DXA },
      borders: { left: linie, top: ohne, bottom: ohne, right: ohne },
      shading: { fill: k.grund, type: ShadingType.CLEAR, color: "auto" },
      margins: { top: 100, bottom: 100, left: 180, right: 140 },
      children: [
        new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: k.titel, bold: true, color: k.rand })] }),
        ...zeilen.map((z) => absatz(z, { spacing: { after: 60, line: 270 } })),
      ],
    })] })],
  }), new Paragraph({ spacing: { after: 120 }, children: [] })];
}
const tipp = (...z) => kasten("tipp", ...z);
const achtung = (...z) => kasten("achtung", ...z);
const kontrolle = (...z) => kasten("kontrolle", ...z);
const hinweis = (...z) => kasten("info", ...z);

/** Abbildung mit Unterschrift; Breite in cm. */
let bildNr = 0;
function bild(datei, breiteCm, unterschrift) {
  bildNr += 1;
  const m = pngMasse(`abb/${datei}`);
  const bPx = Math.round(breiteCm * 37.8);
  const hPx = Math.round(bPx * m.h / m.b);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 },
      children: [new ImageRun({ type: "png", data: m.daten, transformation: { width: bPx, height: hPx } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: [new TextRun({ text: `Abb. ${bildNr}: ${unterschrift}`, italics: true, size: 18, color: FARBE.grau })] }),
  ];
}

// ---------- Deckblatt ----------
const deckblatt = [
  new Paragraph({ spacing: { before: 600, after: 120 }, alignment: AlignmentType.LEFT,
    children: [new TextRun({ text: "Heimanlage Spur N", font: SCHRIFT, size: 64, bold: true, color: FARBE.titel })] }),
  new Paragraph({ spacing: { after: 360 },
    children: [new TextRun({ text: "Bahnhof, Gleiswendel & KV-Terminal · Planung und Bauanleitung", size: 30, color: FARBE.grau })] }),
  ...bild("deckblatt.png", 16.5, "Die Anlage am Abend – 3D-Planungsmodell, Blick von der Bedienseite (Westen)"),
  ...tabelle(["Kenndaten", ""], [
    ["Grundplatte", "2,00 × 1,00 m, dazu Leiste 0,20 × 1,00 m im Süden"],
    ["Erweiterung (Wendel)", "0,70 × 0,70 m an der Westseite, Nordende"],
    ["Ebenen", "Schattenbahnhof unten, Bahnhof und Ort oben, ca. 17,4 cm Höhenunterschied"],
    ["Spur / Gleis", "N (1:160), Peco Code 55 Flexgleis, Unifrog-Weichen, digital"],
    ["Drucker", "Bambu Lab A1 mit AMS lite – Wendel in PETG"],
    ["Stand", "Planungsstand 08.11.2026 (geprüft vom Rat) – Stücklisten folgen später"],
  ], [3000, BREITE - 3000]),
];

// ---------- Kapitel 1: Überblick ----------
function baueKap1() {
  neueSchritte();
const kap1 = [
  h1("Überblick", "ueberblick"),
  absatz("Die Anlage ist ein zweigleisiger Rundkurs über zwei Ebenen. Unten liegt ein Schattenbahnhof, oben ein viergleisiger Durchgangsbahnhof mit gläserner Brücke, ein Ort auf einer Anhöhe mit Straßenbahn, eine Rangiergruppe mit Industrie und ein kleiner Hafen. Verbunden sind die Ebenen über einen zweigleisigen Gleiswendel auf der Erweiterung."),
  h2("1.1 Himmelsrichtungen und Zugang"),
  ...tabelle(["Seite", "Lage", "Zugang"], [
    ["Westen", "Vorderseite, Bedienplatz", "voll – hier stehst du"],
    ["Süden", "Leiste 0,20 m, Zug-Safe-Anschluss unten", "gut"],
    ["Norden", "Wand", "keiner"],
    ["Osten", "Wand", "keiner"],
    ["Erweiterung", "Wendel, darüber der Ort; Drucker steht westlich daneben", "von Süden und von vorn"],
  ], [1800, 4600, BREITE - 6400]),
  h2("1.2 Betriebskonzept"),
  punkt("**Hundeknochen ohne Kehrschleife:** Zweigleisige Strecke durch den Wendel, oben und unten je eine Tropfenschleife."),
  punkt("**Richtungsbetrieb:** Jedes Hauptgleis hat eine Fahrtrichtung. Am Wendel oben verteilt ein Abzweig mit **einer Kreuzung** die Züge auf beide Richtungen."),
  punkt("**Wendel:** Bergauf auf dem äußeren Gleis (flacher), bergab auf dem inneren."),
  punkt("**Digital:** Z21 mit Booster, RailCom-Belegtmelder; Strecke, Wendel und Schattenbahnhof automatisch per PC, Rangieren von Hand mit der Köf (Kapitel " + ref("elektrik") + ")."),
  ...achtung("Zwischen den beiden Gleisen der Wendelstrecke **keinen Gleiswechsel** einbauen – sonst entsteht doch eine Kehrschleife."),
  h2("Fahrzeuge und Zuglängen", "zuglaengen"),
  absatz("Die nutzbaren Längen begrenzen die Züge. Vor dem Gleisbau eine **maximale Zuglänge** festlegen und alle Pläne daran messen."),
  ...tabelle(["Stelle", "Nutzlänge", "Folge"], [
    ["Bahnsteiggleise oben", "ca. 700 mm", "Halt nur für Züge bis ca. 70 cm (S-Bahn, Doppelstock-Regio)"],
    ["Abstellgleis unten", "ca. 2,6–2,9 m", "zwei Züge je Gleis, also je ca. 1,3 m"],
    ["Ladegleis KV-Terminal", "ca. 580 mm", "zwei bis drei Wagen, Rest per Rangieren"],
    ["Längster Zug (ICE, 8 Wagen)", "ca. 1,3 m – am Modell messen", "fährt oben durch, unten ein Zug je Abstellgleis"],
  ], [3200, 2600, BREITE - 5800]),
  ...achtung("Den **schwersten und längsten Zug bergauf im Wendel** testen, bevor die obere Ebene gebaut wird."),
];
  return kap1;
}

// ---------- Kapitel 2: Maße ----------
function baueKap2() {
  neueSchritte();
const kap2 = [
  h1("2 Maße und Kenndaten"),
  absatz("Alle Werte sind Planungswerte. Vor dem endgültigen Druck jeweils ein Probeteil drucken und mit dem längsten Fahrzeug (ICE, Doppelstockwagen) testen."),
  h2("2.1 Platten und Höhen"),
  ...tabelle(["Größe", "Wert"], [
    ["Grundplatte", "2000 × 1000 mm"],
    ["Leiste Süd", "200 × 1000 mm (wird für Südbögen gebraucht)"],
    ["Erweiterung", "700 × 700 mm"],
    ["Höhe obere Ebene über unterer (SO–SO)", "ca. 174 mm (3,5 × 51 mm, abzüglich je halbe Steigung an Anfang und Ende)"],
    ["Dicke obere Platte", "ca. 19 mm (Planungswert, siehe " + ref("unterbau") + ")"],
    ["Freiraum unter oberer Platte", "ca. 155 mm (Oberkante untere bis Unterkante obere Platte, mind. 150 mm)"],
    ["Anhöhe Ort über oberer Ebene", "55 mm"],
    ["Fahrdraht über SO (angedeutet)", "ca. 38 mm"],
  ], [5200, BREITE - 5200]),
  h2("2.2 Gleiswendel"),
  ...tabelle(["Größe", "Wert"], [
    ["Außendurchmesser Trassenbrett", "700 mm (R 250 bis R 350)"],
    ["Gleismitte außen / innen", "R 320 (bergauf) / R 280 (bergab), Abstand 40 mm"],
    ["Höhe je Umdrehung", "51 mm"],
    ["Umdrehungen", "3,5"],
    ["Steigung außen / innen", "2,5 % / 2,9 %"],
    ["Lichte Höhe über SO", "regulär ca. 42,5 mm (51 − 4 mm Platte − 2 mm Bettung − ca. 2,5 mm Gleis); an Stoß 0 und 42 ca. 40 mm; an den Ausfahrten außen ca. 37 mm, innen ca. 35 mm – Stromabnehmer max. ca. 33 mm über SO"],
    ["Höhenbezug", "Erweiterungsplatte 4 mm tiefer als die Grundplatte, Konsolenhöhen ab Oberkante Erweiterung"],
    ["Gleisbettung", "TPU 95A, 18 mm breit, Dicke wie Kork der Anlage (ca. 2 mm), Stöße 15° versetzt"],
    ["Entkopplung", "Filzscheibe Ø 12 mm nur unter jeder Konsole"],
    ["Anlauf", "Stöße 1–4 auf gedruckten Anlaufklötzen (2,125 / 6,375 / 10,625 / 14,875 mm), ab Stoß 5 auf Konsolen"],
    ["Konsolen", "flach, 6 mm, Bohrung Ø 6,5, sitzen auf zwei Muttern (Mutter + Kontermutter) unten; Stoß 11/23/35 mit Sonderkonsole (Stange bei 60° auf R 395)"],
    ["Platte", "30°, flach, 4 mm PETG, biegt sich auf die Auflager; 42 Stück"],
    ["Leitkante / Randleiste", "außen R 347–350, 10 mm hoch / innen R 250–254, 4 mm hoch (beide oben)"],
    ["Verbindung", "Schwalbenschwanz in der Ebene, 0,15 mm Spiel je Seite (im PLA-Test ermittelt)"],
    ["Übergang", "erster und letzter Stoß nur 2,125 mm (halbe Steigung) – über die Konsolenhöhe"],
    ["Ausfahrt unten", "Nordseite, Richtung Osten (an der Nordwand)"],
    ["Ausfahrt oben", "Südseite, Richtung Osten"],
    ["Drehsinn", "bergauf gegen den Uhrzeigersinn (von oben gesehen)"],
    ["Auflager", "Gewindestangen M6 bei R 240 und R 343, alle 30°; je Stoß zwei flache Konsolen (innen und außen), Höhe je Stoß +4,25 mm, Gleisbereich bleibt frei"],
  ], [4400, BREITE - 4400]),
  h2("2.3 Radien obere Ebene"),
  ...tabelle(["Abschnitt", "Radius außen / innen"], [
    ["Einfahrt Bahnhof aus dem Abzweig", "680 / 640 mm"],
    ["Bahnsteiggleise im Einfahrbogen", "740 / 580 mm"],
    ["Bahnsteigkante (gleichmäßiger Bogen)", "ca. 4400 mm"],
    ["Bogen am Bahnhofsende (Ostwand)", "545 / 505 mm"],
    ["Südbogen", "435 / 395 mm"],
    ["S-Kurve vorn (mit Zwischengerade)", "545 / 505 mm"],
    ["Bogen zurück zum Abzweig", "410 und 450 mm"],
    ["Straßenbahn (Anhöhe)", "mindestens 120 mm – Mindestradius des Modells prüfen"],
  ], [5200, BREITE - 5200]),
  h2("2.4 Radien und Längen untere Ebene"),
  ...tabelle(["Abschnitt", "Wert"], [
    ["Bogen an der Ostwand", "R 420 mm"],
    ["Großer Bogen und S-Kurve zur Vorderseite", "R 455 mm"],
    ["Südbogen Hauptgleis", "R 440 mm"],
    ["Abstellgleise im Südbogen", "4 Gleise, R ca. 410 / 377 / 345 / 314 mm (Abstand ca. 32 mm) neben dem durchgehenden Hauptgleis R 440"],
    ["Nutzlänge je Abstellgleis", "ca. 2,6–2,9 m (zwei Züge je Gleis möglich)"],
    ["Aufgleisgleis (Zug-Safe, Ende Südkante)", "ca. 1,0 m"],
  ], [5200, BREITE - 5200]),
  h2("2.5 Bahnhof"),
  ...tabelle(["Größe", "Wert"], [
    ["Gleise", "2 Hauptgleise (Mitte, ICE/Güter), 2 Bahnsteiggleise (außen)"],
    ["Bahnsteiglänge", "ca. 700 mm"],
    ["Inselbahnsteig Breite", "33 mm an den Enden, 47 mm in der Mitte, ca. 45 mm unter der Brücke"],
    ["Bahnsteighöhe", "4,8 mm über SO (76 cm beim Vorbild)"],
    ["Abstand Bahnsteigkante – Gleismitte", "11,5 mm, im Einfahrbogen (R ≈ 680 mm) 13,5 mm"],
    ["Glasbrücke", "332 × 91 mm, Unterkante 47 / Boden 55 / Dach 81 mm über SO"],
    ["Glasdächer", "zwei, je 150 mm lang, an der Brücke 236 mm breit, spitz zulaufend"],
    ["Glasdach Höhe / Wölbung", "Scheitel ca. 68 mm über SO, Stich ca. 10 mm"],
    ["Aufzugtürme", "40 × 29 mm, Doppelaufzug 25 × 14 mm, Treppe im Rechteck; alle drei 42 mm hoch"],
    ["Eingang Industrieseite", "Stufenplateau 7,3 mm (3 Stufen), Vordach ca. 30 mm über dem Plateau"],
    ["Haltestellendach (Ort)", "164 × 34 mm, 30 mm über Ortsniveau"],
    ["Hafengleise", "ca. 800 und 500 mm, gerade"],
  ], [4400, BREITE - 4400]),
  h2("2.6 KV-Terminal und Gewerbe"),
  ...tabelle(["Größe", "Wert"], [
    ["Ladegleis (Industrie 1)", "ca. 580 mm gerade, Stumpfgleis mit Kopframpe"],
    ["Portalkran", "Spur 100 mm, lichte Höhe 75 mm, gesamt ca. 88 mm, Träger 120 mm"],
    ["Kranbahn", "2 × 200 mm, Messing-Vierkant 1 × 1 mm"],
    ["Kopframpe", "28 mm breit, Plateau 30 mm, Auffahrt 50 mm"],
    ["Bahnübergang", "Südseite über beide Hauptgleise, Straße 36 mm breit"],
    ["Gewerbegebiet", "restlicher Innenraum, zwei Anschlussgleise"],
  ], [4400, BREITE - 4400]),
];
  return kap2;
}

// ---------- Kapitel 3: Gleispläne ----------
function baueKap3() {
  neueSchritte();
const kap3 = [
  h1("3 Gleispläne"),
  absatz("Die Pläne sind schematisch; Weichenstraßen sind verkürzt gezeichnet. Norden ist rechts, die Vorderseite (Westen) oben."),
  h2("3.1 Obere Ebene"),
  ...bild("plan_oben.png", 16.5, "Obere Ebene – Bahnhof, Ort auf der Anhöhe (grün), Rangiergruppe, KV-Terminal, Gewerbegebiet mit Bahnübergang, Hafen, Straßenbahn (gestrichelt)"),
  punkt("Der Abzweig mit Kreuzung liegt im Tunnel unter dem Ort; die Hauptgleise kommen vorn an der Erweiterung aus dem Tunnelportal."),
  punkt("Die Ortsplatte über Wendel und Abzweig wird **abnehmbar** gebaut – ohne Werkzeug."),
  punkt("Die **Kreuzung** im Abzweig ist die empfindlichste Stelle: vor dem Einbau einzeln mit allen Loks testen, auch langsam."),
  punkt("Die Straßenbahn fährt im Ort mit Bögen von **mindestens 120 mm** Radius."),
  h2("3.2 Untere Ebene"),
  ...bild("plan_unten.png", 16.5, "Untere Ebene – Schattenbahnhof als Tropfenschleife, Aufgleisgleis mit Zug-Safe an der Südkante"),
  h2("3.3 Wendel"),
  ...bild("wendel_uebersicht.png", 12, "Wendel – Lage der Ausfahrten und der Gewindestangen"),
];
  return kap3;
}

// ---------- Kapitel 4: Drucken ----------
function baueKap4() {
  neueSchritte();
const kap4 = [
  h1("Druckeinstellungen für den A1", "druck", true, "B"),
  h2("4.1 PETG für den Wendel"),
  absatz("PETG ist zäher und wärmefester als PLA und kriecht unter Dauerlast kaum – wichtig für ein Trassenbrett, auf dem jahrelang Züge fahren."),
  ...tabelle(["Einstellung", "Wert"], [
    ["Filament-Profil", "Bambu „PETG HF“ bzw. „Generic PETG“ übernehmen"],
    ["Düse / Schichthöhe", "0,4 mm / 0,2 mm"],
    ["Wände / Decklagen / Bodenlagen", "3 / 5 / 4"],
    ["Füllung", "25 % Gyroid"],
    ["Druckplatte", "BIQU CryoGrip Pro Glacier – in Bambu Studio als „Smooth PEI Plate / High Temp Plate“ wählen"],
    ["Betttemperatur", "ca. 65–70 °C (Hersteller: PETG 60–75 °C)"],
    ["Trennmittel", "dünn Klebestift auftragen – PETG haftet auf feinen Oberflächen sehr stark"],
    ["Modus", "Leise (50 %) – für die Serie der 42 Platten ggf. Normalmodus"],
    ["Ausrichtung", "Platte flach, Unterseite aufs Bett – „Auf Fläche legen“ (F), kein Stützmaterial"],
  ], [4400, BREITE - 4400]),
  ...tipp("PETG zieht Feuchtigkeit. Spule vor dem Druck trocknen (Herstellerangabe, meist 65 °C für einige Stunden) – sonst entstehen Fäden und raue Oberflächen."),
  ...hinweis("Die Gleisbettung im Wendel wird aus **TPU 95A** gedruckt – Einstellungen dazu in Abschnitt " + ref("bettung") + "."),
  h2("TPU 95A für die Gleisbettung"),
  ...tabelle(["Einstellung TPU 95A", "Wert"], [
    ["Spule", "externe Spulenhalterung (der AMS lite kann kein TPU)"],
    ["Filament-Profil", "Bambu „Generic TPU“ bzw. „TPU 95A HF“"],
    ["Düse / Schichthöhe", "0,4 mm / 0,2 mm"],
    ["Wände / Decklagen / Bodenlagen", "2 / 3 / 3"],
    ["Füllung", "15 % Gyroid – die Luftkammern dämpfen zusätzlich"],
    ["Max. Volumenfluss", "ca. 3,5 mm³/s (langsam, sonst Unterextrusion)"],
    ["Druckplatte", "CryoGrip Pro Glacier, Plattentyp „Smooth PEI Plate / High Temp Plate“, Klebestift als Trennmittel"],
  ], [4400, BREITE - 4400]),
  ...tipp("TPU vorher trocknen (meist 4–6 h bei ca. 55 °C). Mehrere Streifen auf einmal aufs Bett legen – der Druck läuft dann über Nacht von allein."),
  h2("Bahnhofs- und Terminalteile"),
  ...tabelle(["Teil", "Material", "Düse"], [
    ["Bahnsteige, Brückenboden, Dächer der Brücke", "PLA (Farbeinlage wie Schwalm-Arkaden)", "0,4"],
    ["Fensterrahmen Brücke", "PLA dunkelgrau", "0,2"],
    ["Glasdach-Gitter, Haltestellendach", "PETG dunkelgrau (biegsam für die Wölbung)", "0,4"],
    ["Aufzugturm-Rahmen", "PLA oder PETG (dunkelgrau/schwarz), verglast mit PET-Folie", "0,2"],
    ["Aufzugkern, Treppe", "PLA grau", "0,2"],
    ["Kran, Kranbahn, Kopframpe, Bahnübergang", "PLA (Kran gelb/orange, Rest grau)", "0,4 / 0,2"],
    ["Anlaufklötze, Ausfahrplatte", "PETG", "0,4"],
    ["Aufzugturm-Faltwand", "PETG schwarz (biegt besser) oder PLA mit Föhn", "0,2 bei 0,1 mm Schicht"],
  ], [4200, 4000, BREITE - 8200]),
  ...hinweis("Verglasung der Brücke und der Dächer mit klarer PET-Folie (ca. 0,2 mm) von innen hinterkleben."),
];
  return kap4;
}

// ---------- Kapitel 5: Wendel ----------
function baueKap5() {
  neueSchritte();
neueSchritte();
const kap5 = [
  h1("5 Bauanleitung Gleiswendel"),
  h2("5.1 Das Prinzip"),
  absatz("Der Wendel besteht aus **flachen 30°-Platten**, 4 mm dick, aus PETG. Jede Platte wird **eben gedruckt** und liegt beim Einbau auf zwei Auflagerpaaren, die von Stoß zu Stoß um 4,25 mm höher stehen. Die Platte biegt sich dabei leicht in die Steigung – genau wie die Sperrholz-Wendel (z. B. NOCH LAGGIES), nur gedruckt."),
  absatz("Die Steigung entsteht also **nur über die Höhe der Auflager** an den Gewindestangen, nicht im Bauteil. Dadurch sind alle Platten gleich, und das Trassenbrett ist überall nur 4 mm dick."),
  punkt("**Leitkante** (Sicherung gegen Absturz) außen auf der Oberseite: R 347–350, 10 mm hoch."),
  punkt("**Randleiste** innen auf der Oberseite: R 250–254, 4 mm hoch – sie versteift die Platte. Die Unterseite bleibt komplett eben, also kein Stützmaterial."),
  punkt("Die Platten sind in der Ebene mit einem **Schwalbenschwanz** verbunden: Nut am 0°-Ende, Zapfen am 30°-Ende."),
  punkt("**Flache Konsolen** an jedem Stoß, innen und außen, auf **Gewindestangen M6**. Die Höhe stellst du mit den Muttern ein."),
  punkt("**Gleisbettung aus TPU 95A** unter jedem Gleis und **Filzscheiben** an den Konsolen für leisen Lauf."),
  ...achtung("Unter den Gleisen (R 268 bis R 332) darf nichts unter der Platte hängen – dort fährt die darunterliegende Windung. Die Konsolen sitzen deshalb nur am Innen- und Außenrand."),
  ...bild("wendel_segment.png", 14.5, "Wendelplatte – Draufsicht mit Schwalbenschwanz und Ausklinkungen; Abwicklung mit flachen Konsolen"),
  h2("5.2 Datei HA_01_Wendelplatte"),
  ...schritt("Neue Konstruktion anlegen", "**Datei → Neue Konstruktion**. Speichern als **HA_01_Wendelplatte**. Im Browser unter **Dokumenteinstellungen → Einheiten** auf **mm** prüfen."),
  ...schritt("Parameter anlegen", "**ÄNDERN → Parameter ändern** (Change Parameters). Mit **+** bei den Benutzerparametern nacheinander anlegen:"),
  ...dialog("Parameter ändern – Benutzerparameter", [
    ["R_innen", "250 mm"], ["R_aussen", "350 mm"], ["Winkel", "30 deg"],
    ["Dicke", "4 mm"], ["Leit_h", "10 mm"], ["Leit_b", "3 mm"],
    ["Rand_h", "4 mm"], ["Rand_b", "4 mm"],
  ]),
  ...schritt("Ringsektor skizzieren", "**ERSTELLEN → Skizze erstellen**, Ebene **XY**.", "Zwei **Kreise – Mittelpunkt/Durchmesser** um den Ursprung: Durchmesser „2 * R_innen“ und „2 * R_aussen“.", "Zwei **Linien** vom Ursprung: eine auf der **X-Achse** (0°), eine unter **Winkel** gegen den Uhrzeigersinn. Mit **Skizzenbemaßung** (D) den Winkel zwischen beiden auf **Winkel** setzen."),
  ...kontrolle("Im Ringsektor zwischen den Kreisen und den beiden Linien erscheint eine geschlossene, hellblau hinterlegte Fläche."),
  ...schritt("Schwalbenschwanz-Nut am 0°-Ende", "In derselben Skizze am 0°-Rand die Nut zeichnen: an der Kante **12 mm** breit, in **10 mm** Tiefe **18 mm** breit, Mitte auf **R 300**. Mit **Linie** als Trapez zeichnen, das in den Sektor hineinragt (Richtung 30°)."),
  ...schritt("Zapfen am 30°-Ende per Kopie", "Die vier Trapezlinien auswählen, **ÄNDERN → Verschieben/Kopieren** (M)."),
  ...dialog("Verschieben/Kopieren", [
    ["Typ", "Drehen"], ["Achse", "Ursprung (Z-Achse)"], ["Winkel", "Winkel (30 deg)"], ["Kopie erstellen", "Ja (Häkchen)"],
  ]),
  ...schritt("Spiel einbauen", "Die kopierten Zapfenlinien mit **ERSTELLEN → Versatz** (O) um **0,15 mm** nach innen versetzen. Zusammen ergibt das **0,3 mm Spiel** – im PLA-Test mit vier Varianten (0,15 bis 0,30 mm je Seite) hat 0,15 mm am besten gepasst, 0,1 mm war zu stramm. Die unversetzten Kopien löschen. **Skizze beenden**."),
  ...kontrolle("Am 30°-Ende ragt der Zapfen aus dem Sektor heraus, am 0°-Ende ist die Nut eingeschnitten. Zapfen und Nut haben dieselbe Form, der Zapfen ist rundum 0,15 mm kleiner. Der Zapfen wird **von oben senkrecht** in die Nut gedrückt, nicht seitlich eingeschoben."),
  ...schritt("Platte extrudieren", "**ERSTELLEN → Extrusion** (E). Profil: Ringsektor **ohne** die Nut, **plus** die Zapfenfläche (Strg gedrückt halten). Abstand **Dicke**, Vorgang **Neuer Körper**."),
  ...schritt("Leitkante und Randleiste", "Skizze auf der **Oberseite** der Platte: Kreis „2 * (R_aussen − Leit_b)“ und Kreis „2 * (R_innen + Rand_b)“ um den Ursprung.", "**Extrusion** des äußeren Rings (R 347–350) um **Leit_h**, Vorgang **Verbinden**.", "**Extrusion** des inneren Rings (R 250–254) um **Rand_h**, Vorgang **Verbinden**."),
  ...achtung("Leitkante und Randleiste **nicht** über den Zapfen hinausführen – sie enden am Sektorrand. Sonst klemmt der Schwalbenschwanz beim Zusammenstecken."),
  ...schritt("Ausklinkungen für die äußeren Gewindestangen", "Skizze auf **XY**: je ein Kreis **Ø 8 mm** bei **R 343** auf der 0°-Linie und auf der 30°-Linie. **Extrusion**, Ausmaß **Alle**, Vorgang **Ausschneiden**.", "Es entstehen zwei halbe Aussparungen – zusammen mit der Nachbarplatte eine volle."),
  ...schritt("Langlöcher für die Konsolenstifte", "Skizze auf **XY** (Unterseite), an beiden Enden: auf **R 258** und auf **R 343** je ein Rechteck **4,0 mm** (in Laufrichtung) × **4,6 mm** (radial), Mitte **10 mm** vom Plattenende.", "Extrusion **3,4 mm** nach oben, Vorgang **Ausschneiden**. Das Loch ist in Laufrichtung spielfrei (Passprobe Variante 1) und hat radial 0,3 mm Luft je Seite für die Wärmeausdehnung."),
  ...achtung("Keine Schrauben ins Plattenmaterial (Ratsbeschluss 09.11.): Bei 4 mm PETG reißt ein Gewinde nach wenigen Malen Lösen aus. Die Platte wird nur über Stifte, Stange und Klemmbock gehalten."),
  ...schritt("Exportieren", "Rechtsklick auf den Körper → **Als Netz speichern** → Format **3MF**. In Bambu Studio mit **Auf Fläche legen** (F) die Unterseite aufs Bett legen."),
  ...tipp("Eine Platte ist ca. 191 × 110 mm groß. Zwei Platten um 180° gedreht ineinander gelegt brauchen etwa 191 × 225 mm und passen damit vermutlich zusammen aufs A1-Bett – in Bambu Studio prüfen. Das halbiert die Zahl der Druckaufträge."),
  h2("5.3 Datei HA_02_Konsolen"),
  ...bild("konsolen.png", 14, "Flache Konsolen innen und außen – der Gleisbereich bleibt frei"),
  ...schritt("Konsole innen", "Neue Konstruktion **HA_02_Konsolen**. Skizze auf **XY**: Rechteck **30 × 40 mm** (30 mm radial = R 232 bis R 262). Extrusion **6 mm**, Vorgang **Neuer Körper**.", "Bei R 240 (8 mm vom Innenrand) mittig eine Bohrung **Ø 6,5** für die Stange. Oben zwei **Stifte Ø 4 × 3 mm** bei **R 258**, je **10 mm** links und rechts der Mitte (je Plattenende einer)."),
  ...schritt("Konsole außen", "Zweites Rechteck **13 × 40 mm** (R 338 bis R 351), Extrusion **6 mm**, Vorgang **Neuer Körper**.", "Bei R 343 (5 mm vom Innenrand) mittig **Ø 6,5**. Oben zwei **Stifte Ø 4 × 3 mm** bei **R 343**, je **10 mm** links und rechts der Mitte."),
  ...schritt("Klemmbock (HA_02_Klemmbock)", "Für jeden Stoß einer, auf der **Innenstange**: Bein **15,5 × 14 × 7,7 mm** (R 234–249,5) steht neben der Platte auf der Innenkonsole, Deckel **21 × 14 × 3 mm** reicht bis **R 255** über die Randleiste. Bohrung **Ø 6,5** bei R 240.", "Das Bein ist 0,2 mm niedriger als Platte + Randleiste (7,9 mm) – beim Anziehen der Mutter drückt der Deckel die Platte mit Vorspannung auf die Konsole. **In PETG drucken**, Deckel nach unten."),
  ...schritt("Auf zwei Muttern", "Jede Konsole sitzt auf **zwei Muttern M6** (Mutter + Kontermutter) mit Unterlegscheibe. Außen kommt oben keine Mutter hin – sie stieße an die Leitkante. Innen hält der **Klemmbock** mit einer Mutter von oben Platte und Konsole fest. Die Höhe stellst du an der oberen der beiden Muttern ein und konterst mit der unteren.", "Gewindeeinsätze wurden verworfen: In der nur 13 mm breiten Außenkonsole bliebe neben einem Einsatz Ø 8 kaum 1 mm Wand."),
  ...tipp("Bedarf für den ganzen Wendel: **24 Gewindestangen M6** (160–210 mm, aus 5 × 1 m), **≈ 200 Muttern M6** DIN 934 (76 Konsolen × 2, 38 Klemmböcke, 24 Stangen unten × 2 – mit Reserve 250), **≈ 160 Scheiben M6** DIN 125. Beim Absägen vorher eine Mutter aufdrehen und danach wieder abdrehen – das richtet das Gewinde."),
  ...schritt("Sonderkonsole an der unteren Ausfahrt (HA_02_Sonderkonsole_60)", "Die Außenstange bei **60°** wird auf **R 395** versetzt, damit sie nicht zwischen den Ausfahrgleisen steht. Die Sonderkonsole ist **64 × 40 × 5 mm**: Stangenbohrung Ø 6,5 bei 57 mm (R 395), Stifte Ø 4 × 3 mm bei 5 mm (R 343) ±10 mm.", "Da die Stange alle Windungen trägt, brauchst du sie dreimal: an den Stößen **11, 23 und 35**."),
  ...schritt("Anlaufklötze (HA_04_Anlaufkloetze)", "Die Stöße 1–4 liegen zu tief für eine Konsole mit Muttern darunter (2,1 bis 14,9 mm). Statt eines großen Sockels gibt es **acht kleine Klötze** – je Stoß einen innen (30 × 40 mm) und einen außen (13 × 40 mm) – mit den Höhen **2,125 / 6,375 / 10,625 / 14,875 mm**.", "Jeder Klotz hat die Bohrung Ø 6,5 für die durchgehende Stange und eine Senkbohrung Ø 3,5 zum Festschrauben auf der Erweiterung. Die Platten werden auf den Klötzen mit etwas Silikon fixiert."),
  ...schritt("Ausfahrplatte oben (HA_05_Ausfahrplatte)", "Ebene Platte **220 × 100 × 4 mm** für die obere Ausfahrt nach Osten, mit Nut für den Zapfen der letzten Wendelplatte, halber Ausklinkung bei R 343, Leitkante (4 mm breit, 10 mm hoch) und Randleiste.", "Bohrung **Ø 7** für die Außenstange bei 300° – dort liegt die Platte auf einer Mutter mit Unterlegscheibe auf. Auf der Ausfahrplatte wird Kork (2 mm) statt TPU verlegt."),
  ...kontrolle("Die Konsolen sind ganz eben – keine Stufe. Außen liegt die Konsole mit R 338 knapp außerhalb der ausschwenkenden Wagenenden (ca. R 334). Unter jedem Stoß liegen beide Plattenenden auf derselben Konsole, die Mitte der Konsole liegt genau unter der Fuge."),
  ...hinweis("Den sanften Übergang am Anfang und Ende stellst du über die Höhen der Anlaufklötze und der letzten Konsole ein (siehe " + ref("montage") + ")."),
  h2("5.4 Datei HA_03_Gleisbettung", "bettung"),
  absatz("Unter jedem Gleis liegt eine **gedruckte Bettung aus TPU 95A**. Sie dämpft das Fahrgeräusch, weil die dünne PETG-Platte sonst wie ein Resonanzboden wirkt. Die Bettung wird **lose gedruckt und weich aufgeklebt** – nicht in die Platte eingedruckt."),
  ...schritt("Parameter", "Neue Konstruktion **HA_03_Gleisbettung**, Parameter anlegen:"),
  ...dialog("Parameter ändern – Benutzerparameter", [
    ["R_gleis", "320 mm (danach 280 mm für das innere Gleis)"], ["Breite", "18 mm"],
    ["Dicke_Bett", "2 mm – genau so dick wie dein Kork auf der übrigen Anlage"], ["Winkel", "30 deg"],
  ]),
  ...achtung("**Korkdicke vorher messen** und Dicke_Bett darauf setzen. Dann liegen Wendel und Anlage am Übergang auf gleicher Höhe."),
  ...schritt("Bogenstreifen", "Skizze auf **XY**: zwei Kreise um den Ursprung mit Durchmesser „2 * R_gleis − Breite“ und „2 * R_gleis + Breite“. Zwei Linien vom Ursprung unter 0° und **Winkel**.", "**Extrusion** des Ringstücks um **Dicke_Bett**, Vorgang **Neuer Körper**."),
  ...schritt("Vier Varianten exportieren", "Jeweils über **Parameter ändern** umstellen und als **3MF** speichern:", "**außen 30°** (R_gleis 320) und **innen 30°** (R_gleis 280) – die Regelstreifen", "**außen 15°** und **innen 15°** (Winkel 15 deg) – je einer am Anfang und am Ende des Wendels"),
  ...kontrolle("Bedarf: je Gleis **41 Streifen 30°** und **2 Streifen 15°**. Durch die halben Stücke an den Enden liegen alle Streifenstöße **15° versetzt** zu den Plattenstößen."),
  ...hinweis("Druckeinstellungen für TPU 95A: siehe " + ref("druck") + "."),
  h2("5.5 Probelauf vor der Serie", "probelauf"),
  ...schritt("Probeplatten drucken", "Drei Platten und **vier Konsolenpaare** drucken (drei Platten haben vier Stöße), auf **acht Gewindestangen** montieren. Stöße auf **0 / 4,25 / 8,5 / 12,75 mm** (Regelsteigung), ein Stück Flexgleis darüberlegen.", "Zusätzlich den Anlauf testen: Anlaufklötze mit 0 / 2,125 / 6,375 mm."),
  ...schritt("Bettung im Vergleich", "Auf die erste Platte TPU-Bettung, auf die zweite Kork, die dritte bleibt nackt. Eine Lok langsam über alle drei fahren lassen und hinhören – so weißt du, was die Bettung bringt."),
  ...schritt("Biegung prüfen", "Die Platte muss sich ohne Gewalt auf die Konsolen legen und satt aufliegen. Sie wird dabei nicht nur gebogen, sondern leicht **verwunden** – genau das soll der Probelauf zeigen. Steht sie in der Mitte hoch, die Schrauben langsam anziehen – PETG gibt nach."),
  ...schritt("Fahrzeugtest", "ICE und Doppelstockwagen langsam darüberschieben. Prüfen: kein Knick am Stoß, kein Streifen an der Leitkante, Stromabnehmer berührt nichts."),
  ...schritt("Lichtraum an den Außenstangen", "Wagenenden schwenken im Bogen nach außen, bei ICE und Doppelstockwagen bis ca. R 334. Bis zur Außenkonsole (R 338) und zur Filzscheibe bleiben nur ca. **2–4 mm** – mit dem längsten Wagen prüfen."),
  ...achtung("Lichte Höhe zwischen den Windungen: regulär ca. **42 mm**, an Stoß 0 und 42 ca. 40 mm, an den Ausfahrten nur **35–37 mm** über SO (" + ref("schnittstellen") + "). Stromabnehmer im Wendelbetrieb auf **max. ca. 33 mm** über SO begrenzen oder festlegen."),
  ...kontrolle("Erst wenn der Probelauf passt, die übrigen Platten drucken – **42 Stück** für 3,5 Umdrehungen."),
  h2("5.6 Montage", "montage"),
  ...schritt("Anlaufklötze und Gewindestangen setzen", "Die Lage der Stangen anzeichnen (Wendelmitte, R 240 und R 343, alle 30°; bei 60° außen R 395). Stangen M6 mit Einschlagmuttern oder Muttern und Unterlegscheiben von unten befestigen.", "Die acht Anlaufklötze (Stoß 1–4) über die Stangen schieben und auf die Erweiterung schrauben. Unter jede Konsole eine dünne **Filzscheibe** (Ø ca. 12 mm, mittig gelocht) legen – nur unten."),
  ...schritt("Höhen einstellen", "Höhe der Auflage-Oberkante am Stoß Nummer k (gezählt ab der Einfahrt unten, Einfahrt = 0), gemessen **ab Oberkante Erweiterung**:", "**Stoß 0:** 0 mm · **Stoß 1–4:** Anlaufklötze (2,125 / 6,375 / 10,625 / 14,875 mm)", "**Stoß 5–41:** Konsolen, **Formel:** Höhe = 2,125 + (k − 1) × 4,25 mm (Stoß 41 = 172,125 mm)", "**Stoß 42:** 174,25 mm – die letzte Platte steigt wieder nur um 2,125 mm.", "Innere und äußere Konsole eines Stoßes immer auf gleiche Höhe. Höhe an der oberen Mutter einstellen, mit der unteren kontern."),
  ...tipp("Höhenlehre selbst drucken: ein Klötzchen mit Stufen in 4,25-mm-Schritten. Oder einen Holzklotz auf die erste Höhe schneiden und danach jede Konsole mit einem 4,25-mm-Distanzstück gegen die vorige einstellen."),
  ...schritt("Platten einsetzen", "Die Platten der Reihe nach einschieben: Zapfen der unteren Platte in die Nut der nächsten. Jedes Plattenende auf die beiden Stifte der Konsolen setzen, Schwalbenschwänze mit dünnflüssigem Sekundenkleber verkleben. Innen den **Klemmbock** auf die Stange setzen, Scheibe und Mutter darauf und leicht anziehen. Außen **keine Mutter von oben** – die Stange läuft frei weiter. Höhe nur an Mutter und Kontermutter **unter** der Konsole einstellen (Metall gegen Metall kontern, nie das PETG einklemmen)."),
  ...schritt("Bettung aufkleben", "TPU-Streifen mittig auf R 320 und R 280 legen, an jedem Ende mit einem **15°-Streifen** beginnen. Mit **Silikon oder Acrylkleber** dünn aufkleben – **kein Sekundenkleber**, der überträgt den Schall wieder auf die Platte."),
  ...schritt("Gleis verlegen", "Flexgleis außen (bergauf) und innen (bergab) mittig auf die Bettung legen. Flexgleis in R 280/320 federt zurück: **vorbiegen** und die Schienenstöße im Bogen **verlöten**. Schienenstöße **versetzt zu den Platten- und Bettungsstößen** anordnen. Nur mit Silikon fixieren, damit die Dämpfung erhalten bleibt."),
  ...schritt("Blöcke einteilen", "Je Gleis **drei Blöcke** (W1–W6), Trennung nur in der **schwarzen** Schiene – Details im Anschlussplan (" + ref("schnittstellen") + ")."),
  ...tipp("Die Ortsplatte über dem Wendel nur auflegen und mit Passstiften sichern – so bleibt der Wendel jederzeit zugänglich."),  h2("5.7 Ansicht, Schnittstellen und Anschlussplan", "schnittstellen"),
  ...bild("wendel_ansicht_sued.png", 16.5, "Wendel von Süden – vorn sichtbar die Leitkanten der Windungen, hinten gestrichelt die Nordhälfte"),
  ...bild("wendel_schnittstellen.png", 16, "Draufsicht mit Plattenstößen (Stoßnummern übereinanderliegender Windungen), Blockgrenzen und Übergängen"),
  ...schritt("Übergang unten (Wendel → Schattenbahnhof)", "Die erste Platte liegt mit ihrer Unterseite direkt auf der Erweiterungsplatte. Damit ihre Oberkante bündig mit der Grundplatte ist, die **Erweiterung 4 mm tiefer** montieren (Unterlegleisten unter der Grundplatte oder Erweiterung entsprechend absetzen).", "Danach liegen **TPU-Bettung im Wendel und Kork auf der Grundplatte** gleich hoch (beide 2 mm)."),
  ...tipp("Alternative, falls die Erweiterung schon fest ist: ein gedruckter Ausgleichskeil von 4 auf 0 mm über ca. 300 mm unter dem Kork vor der Einfahrt. Das ergibt nur 1,3 % zusätzliche Steigung."),
  ...schritt("Übergang oben (Wendel → Bahnhof)", "Über der letzten Windung darf an der oberen Ausfahrt nur eine **4 mm dicke Ausfahrplatte** liegen – eine 19 mm dicke Grundplatte würde die lichte Höhe darunter auf ca. 20 mm drücken. Deshalb die Ausfahrgleise auf **ebenen gedruckten Ausfahrplatten** (4 mm, PETG) bis außerhalb von R 351 führen; die obere Grundplatte beginnt erst dort.", "**Plattenoberkante = Oberkante obere Ebene**. Darauf wieder TPU im Wendel und Kork auf der Platte – gleich hoch.", "Hier liegt die **Grenze zwischen Abschnitt A und B**: an beiden Gleisen **alle Schienen** trennen."),
  ...achtung("**Engstellen an beiden Ausfahrten:** Die Ausfahrtsgleise laufen eben nach Osten, während darüber (unten) bzw. darunter (oben) eine Windung weiterläuft. Die lichte Höhe sinkt dort auf ca. **37 mm** (außen) und ca. **35 mm** (innen) über SO. Stromabnehmer max. ca. 33 mm und genau diese Stellen im Probelauf testen."),
  ...achtung("**Stange bei 60° an der unteren Ausfahrt:** Die Außenstange bei 60° steht zwischen den beiden Ausfahrgleisen, und die Konsole von Stoß 11 hängt dort nur ca. 28–30 mm über SO – zu tief für Doppelstockwagen (ca. 29 mm hoch). Diese Stange nach außen versetzen (z. B. R ≈ 395, außerhalb beider Ausfahrgleise) und Stoß 11 mit einer verlängerten Sonderkonsole tragen. Im Probeaufbau mit dem Doppelstockwagen prüfen."),
  ...schritt("Höhen messen", "Alle Konsolenhöhen aus " + ref("montage") + " werden **ab Oberkante Erweiterungsplatte** gemessen."),
  ...bild("wendel_anschlussplan.png", 16.5, "Anschlussplan des Wendels, abgewickelt: Schienen, Trennstellen, Einspeisungen und Melderkanäle"),
  ...schritt("Farbregel im Wendel", "Auf der zweigleisigen Strecke gilt: **rot = linke Schiene in Fahrtrichtung**. Im Wendel sind das die beiden Schienen, die **zueinander zeigen** (R 315,5 und R 284,5). Die beiden äußeren Schienen (R 324,5 und R 275,5) sind **schwarz**."),
  ...schritt("Trennstellen", "Je Gleis drei Blöcke: **W1–W3 außen (bergauf), W4–W6 innen (bergab)**. Blockgrenzen an den Plattenstößen **0, 14 und 28**, jeweils nur in der **schwarzen** Schiene (isolierender Schienenverbinder).", "Am Stoß **42** (oben) alle vier Schienen trennen – Abschnittsgrenze A/B."),
  ...schritt("Einspeisungen", "An den Stößen **2, 7, 12, 16, 21, 26, 30, 35 und 40** – etwa eine je Flexgleisstück. Bohrung Ø 1,5 mm durch TPU und Platte direkt neben der Schiene, nahe einer Konsole.", "**Rot** direkt an die rote Leitung von Abschnitt B. **Schwarz** je Block gebündelt an den Melderkanal: **M1.1–M1.3** außen, **M1.4–M1.6** innen. Kanäle 7 und 8 bleiben Reserve."),
  ...schritt("Leitungen führen", "Unter der Platte die Drähte **radial** zum Rand führen und flach ankleben: außen zur **Außenkante R 350**, innen zur **Innenkante R 250**.", "Von dort an einer Außenstange bzw. durch die **Wendelmitte** senkrecht nach unten zur Erweiterung. Melder M1 sitzt unter der Erweiterung."),
  ...achtung("Kein Draht darf im Bereich R 268 bis R 332 unter der Platte hängen – dort fährt die Windung darunter."),
  ...kontrolle("Nach dem Verkabeln jeden Block einzeln mit einer Lok testen: Im Steuerprogramm muss genau der richtige Block (W1–W6) belegt melden, und RailCom muss die Lokadresse zeigen."),
];
  return kap5;
}

// ---------- Kapitel 6: Bahnhof ----------
function baueKap6() {
  neueSchritte();
const kap6 = [
  h1("6 Bauanleitung Bahnhof"),
  h2("6.1 Überblick"),
  ...bild("bahnhof_draufsicht.png", 16.5, "Bahnhof von oben (gestreckt) – Brücke, beide Glasdächer, Haltestellendach, drei Aufzugtürme"),
  ...bild("querschnitt_b.png", 16.5, "Querschnitt durch Glasdach und Brücke (Westseite offen)"),
  punkt("Die Brücke reicht 50 mm in den Ort hinein und auf der Industrieseite über das letzte Gleis hinaus."),
  punkt("Unter der Brücke steht auf jeder Insel und auf der Industrieseite ein gleicher rechteckiger Aufzugturm; auf der Industrieseite auf einem Stufenplateau mit Vordach."),
  punkt("Die beiden Glasdächer sind gespiegelt und laufen nach Nordwesten bzw. Südosten spitz zu."),
];
neueSchritte();
kap6.push(
  h2("6.2 Datei HA_10_Inselbahnsteig"),
  ...schritt("Parameter", "Neue Konstruktion **HA_10_Inselbahnsteig**, Parameter anlegen:"),
  ...dialog("Parameter ändern – Benutzerparameter", [
    ["Laenge", "700 mm"], ["Breite_Ende", "33 mm"], ["Breite_Mitte", "47 mm"], ["Hoehe", "7,3 mm ab Oberkante Kork (Gleis ca. 2,5 mm + Bahnsteighöhe 4,8 mm über SO)"],
  ]),
  ...schritt("Umriss", "Skizze auf **XY**: gerade Linie der Länge **Laenge** (Seite zum Hauptgleis).", "Gegenüber mit **Bogen durch drei Punkte**: Endpunkte im Abstand **Breite_Ende**, Mittelpunkt im Abstand **Breite_Mitte** von der Geraden. Enden mit kurzen Linien schließen."),
  ...schritt("Körper", "**Extrusion** um **Hoehe**. Oberkanten zur Gleisseite mit **Fase 0,5 mm** brechen."),
  ...schritt("Teilen für den Druck", "**ÄNDERN → Körper teilen** (Split Body) mit senkrechten Ebenen so, dass jedes Stück **höchstens 240 mm** lang ist."),
  ...achtung("Der nordwestliche Teil des Bahnhofs liegt in der Anlage im Einfahrbogen (R ≈ 680 mm). Dieses Endstück erst konstruieren, wenn das Gleis liegt: Kante auf Papier abnehmen, Foto als **EINFÜGEN → Canvas** in Fusion legen und nachzeichnen. Dort Kantenabstand 13,5 mm statt 11,5 mm."),
  h2("6.3 Datei HA_11_Aufzugturm"),
  ...bild("aufzugturm_eingang.png", 16, "Aufzugturm mit Doppelaufzug (links) und Eingang auf der Industrieseite (rechts)"),
  absatz("Alle drei Türme sind **gleich**: rechteckig, mit einem **Doppelaufzug** in der Mitte und einer Treppe, die **im Rechteck** um den Aufzugschacht herumläuft. Auf der Industrieseite gleicht ein Stufenplateau den Höhenunterschied aus (" + ref("eingang") + ")."),
  ...schritt("Parameter", "Neue Konstruktion **HA_11_Aufzugturm**, Parameter anlegen:"),
  ...dialog("Parameter ändern – Benutzerparameter", [
    ["Hoehe", "42 mm (Bahnsteigoberkante bis Unterkante Brücke, am Modell abnehmen)"],
    ["Turm_L", "40 mm"], ["Turm_B", "29 mm"], ["Schacht_L", "25 mm"], ["Schacht_B", "14 mm"],
    ["Wand", "1,2 mm"], ["Lauf_b", "6 mm"],
  ]),
  ...schritt("Hülle als Faltteil (HA_11_Turm_Faltwand)", "Die vier Wände werden **nebeneinander flach** gedruckt (40 | 29 | 40 | 29 mm, zusammen 138 × 42 × 1,2 mm) und zum Turm **gefaltet** – wie Origami. An den drei Knickkanten sitzt innen eine **V-Nut (90°)**, die nur **0,3 mm** Material stehen lässt; an beiden Enden je eine halbe V-Fase für die Klebenaht.", "Jede Wand ist ein Rahmen (Rand 1,5 mm, Pfosten 1 mm, zwei Riegel bei 14 und 28 mm). Innen liegt je Wand eine Falz-Tasche 0,3 mm tief für ein Stück Folie. In der ersten kurzen Wand ist das untere Feld als **Eingang** bis zum Boden offen."),
  ...schritt("Doppelschacht", "Der Schacht ist ein **Glasschacht** mit zwei fahrenden Kabinen – siehe „Beweglicher Aufzug“ (" + ref("aufzug") + ")."),
  ...schritt("Treppe (HA_11_Treppe)", "Die Läufe werden als **Seitenprofil liegend** gedruckt – so braucht es kein Stützmaterial: **Lauf lang** (5 Stufen, Auftritt 5 mm) für die Langseiten, **Lauf kurz** (5 Stufen, Auftritt 2,8 mm) für die Schmalseiten, Steigung je **2,1 mm**, Breite 6 mm. Dazu **Eckpodeste** 6,3 × 6,3 × 2 mm.", "Je Turm: **2 lange Läufe, 2 kurze Läufe, 4 Podeste**. Vier Läufe zu je 5 Stufen ergeben 20 × 2,1 mm = 42 mm – eine Turmhöhe."),
  ...schritt("Verglasung", "Die Hülle wird **nicht aus klarem Filament** gedruckt – PETG wird nicht schön durchsichtig. Klare **PET-Folie (ca. 0,2 mm)** je Wand passend zur Falz-Tasche zuschneiden und **vor dem Falten** einkleben (Kleber für Klarsichtteile, kein Sekundenkleber – der lässt die Folie anlaufen)."),
  ...schritt("Druck und Falten", "Faltwand mit der **Außenseite nach unten** auf die glatte Platte, **0,2-mm-Düse, 0,1 mm Schichthöhe** (dann sind die 0,3 mm im Knick drei Schichten). Am besten in **PETG schwarz** – es biegt sich, ohne zu brechen. Bei PLA die Knickkanten vorher mit dem Föhn anwärmen.", "Langsam um 90° falten, bis sich die V-Nuten schließen; die letzte Ecke (halbe Fasen) verkleben. Schacht und Treppe vorher einsetzen."),
  ...kontrolle("Der Turm steht auf der Inselmitte (ca. 45 mm breit unter der Brücke) mit rund 8 mm Platz bis zu jeder Bahnsteigkante. Die Langseite liegt **längs zum Gleis**."),
  h2("Beweglicher Aufzug", "aufzug"),
  absatz("Im Glasschacht fahren **zwei Kabinen gegenläufig**: Ein Mikroservo unter der oberen Platte zieht die eine hoch, die andere sinkt durch ihr Eigengewicht nach unten. Alle drei Türme sind gleich – die Teile werden dreimal gedruckt."),
  ...bild("aufzug_teile.png", 16, "Teile des beweglichen Aufzugs: Glasschacht als Faltwand, Boden und Kopfstück, Kabine, Servohalter, Doppelhebel"),
  ...tabelle(["Teil", "Maße", "Aufgabe"], [
    ["HA_11_Glasschacht_Faltwand", "25 | 14 | 25 | 14 × 42 × 1,0 mm", "Glasschacht, gefaltet wie der Turm, Folie innen"],
    ["Schachtboden", "23 × 12 × 1,5 mm", "hält Röhrchen und Führungsdrähte unten"],
    ["Kopfstück", "23 × 12 × 4 mm", "Seillöcher über den Kabinen, Rille oben zur Mitte, Röhrchen 2 mm eingesteckt"],
    ["HA_11_Kabine (2 je Turm)", "9,5 × 10 × 14 mm", "Fenster an drei Seiten, Kerbe für das Röhrchen, Seilöse, Führungsloch, Ballastmulde"],
    ["HA_11_Servohalter", "Winkel 50 × 22 / 45 mm", "Mikroservo SG90 (Laschen 27,8 mm), Fenster für das Röhrchen"],
    ["HA_11_Servohebel", "40 × 5 × 2 mm", "auf das Servohorn kleben, Seillöcher bei ±14 und ±16 mm"],
  ], [3000, 2600, BREITE - 5600]),
  ...tabelle(["Kaufteil (je Turm)", "Menge"], [
    ["Mikroservo SG90 (oder baugleich)", "1"],
    ["Messingröhrchen Ø 1,5 mm (innen ca. 1,0)", "ca. 80 mm"],
    ["Messingdraht Ø 0,5 mm (Führung)", "2 × ca. 40 mm"],
    ["Schwarzer Faden (Nylon, ca. 0,15–0,2 mm)", "2 × ca. 150 mm"],
    ["Ballast: Walzblei-Plättchen ca. 7 × 7 × 1 mm oder Stahlkugeln", "je Kabine ca. 0,5–1 g"],
    ["Klare PET-Folie 0,2 mm", "Reste"],
    ["Servodecoder mit 4 Ausgängen (z. B. ESU SwitchPilot Servo)", "1 für alle drei Türme"],
  ], [6400, BREITE - 6400]),
);
neueSchritte();
kap6.push(
  absatz("**Zusammenbau in 7 Bildern** – neue Teile sind farbig, schon verbaute blass."),
  ...bild("aufzug/schritt1.png", 11, "Folie einlegen und Schacht falten"),
  ...bild("aufzug/schritt2.png", 11, "Boden einkleben"),
  ...bild("aufzug/schritt3.png", 11, "Röhrchen (Ø 1,6 mm bohren) und Führungsdrähte"),
  ...bild("aufzug/schritt4.png", 11, "Kabinen mit Ballast einsetzen"),
  ...bild("aufzug/schritt5.png", 11, "Kopfstück aufsetzen, Fäden durch die Rille ins Röhrchen"),
  ...achtung("Kabinen müssen sich **von Hand leicht** bewegen, bevor der Servo dran kommt. Lochkanten anfasen, Hauch Silikonöl oder Grafit auf die Rille."),
  ...bild("aufzug/schritt6.png", 11, "Servohalter unter die obere Platte, Fäden an den Hebel"),
  ...bild("aufzug/schritt7.png", 11, "Endlagen am Servodecoder: ±45°, langsam, in der Endlage abschalten"),
  ...kontrolle("Ca. 22 mm Hub. Servo hängt ca. 45 mm unter der Platte – nicht über einer Weichenstraße montieren."),
  ...tipp("Licht: zuerst eine SMD-LED unter dem Kopfstück (Schachtlicht); später ein Hängekabel zur Kabinen-LED."),
  ...hinweis("SG90-Maße schwanken – Servohalter zuerst einzeln drucken und anprobieren."),
  h2("6.4 Datei HA_12_Glasbruecke"),
  ...schritt("Maße", "Brücke **332 × 91 mm**. Höhen über SO: Unterkante Tragwerk 47, Boden 55, Glas bis 78, Dachplatte bis 81 mm.", "Weil 332 mm nicht auf das Bett passen, wird die Brücke **zweigeteilt** – die Fuge liegt an einem Fensterpfosten über dem inneren Inselbahnsteig, nicht über den Hauptgleisen (dort wäre sie genau in deiner Blickachse). Gefügt mit einer Schwalbenschwanz-Verbindung."),
  ...schritt("Tragwerk und Boden", "Skizze auf XY: Rechteck 332 × 91 mm, mit **Körper teilen** an der Fuge in zwei Teile (keins länger als 240 mm). Extrusion **8 mm** als Tragwerk. Seitlich ein Fachwerk-Muster (Dreiecke, Teilung 20 mm) **2 mm tief ausschneiden**."),
  ...schritt("Seitenwände als Fensterrahmen", "Separate Körper: Rahmen in den Längen der beiden Brückenteile, 23 mm hoch, 1,5 mm dick, Pfosten alle 19 mm, 1 mm breit. Flach mit der 0,2-mm-Düse drucken."),
  ...schritt("Läden", "Einsätze 30–40 mm lang als Kästen mit offener Vorderseite auf den Boden stellen; Platz für LED-Streifen warmweiß unter der Dachplatte lassen."),
  ...schritt("Dachplatte", "Je Brückenteil passend, 3 mm dick, mit 2 mm Überstand ringsum."),
  ...kontrolle("Unterkante 47 mm über SO: mit aufgesetztem Fahrdraht-Mast und ICE mit Stromabnehmer prüfen."),
  h2("6.5 Datei HA_13_Glasdach"),
  ...bild("glasdach.png", 12, "Glasdach – Umriss und Rautengitter (eines von zwei, gespiegelt)"),
  ...schritt("Umriss", "Skizze auf XY: gerade Linie **236 mm** (Anschluss an die Brücke). Von ihren Enden je ein **Bogen durch drei Punkte** zur Spitze **150 mm** entfernt auf der Mittellinie. Bogen leicht nach außen wölben (siehe Abb.)."),
  ...schritt("Platte und Rand", "Extrusion **3 mm**. Den Umriss mit **Versatz 3 mm** nach innen kopieren – das wird der Rand."),
  ...schritt("Rautengitter", "Im Inneren eine Raute (Diagonalen 12 − 1,6 mm) zeichnen und **ausschneiden**. **ERSTELLEN → Muster → Rechteckiges Muster** über die ganze Fläche (Abstand 12 mm in beide Diagonalrichtungen). Danach den 3-mm-Rand aus Schritt 2 per Extrusion mit Vorgang **Verbinden** wieder auffüllen – so sind angeschnittene Rauten am Rand geschlossen."),
  ...schritt("Wölbung", "Zwei **Bogenbinder** konstruieren: Bogen mit Sehne 236 mm und Stich 10 mm (R ≈ 700 mm), 3 × 4 mm Querschnitt. Einer sitzt an der Brücke, einer auf halber Länge."),
  ...schritt("Druck und Montage", "Gitter flach in **PETG dunkelgrau** drucken, Folie von unten aufkleben, über die Bogenbinder biegen und verkleben. Stützen aus Messingrohr Ø 2–3 mm, je Insel zwei pro Dach, Länge am Modell abnehmen – die Stützen stehen seitlich vom Scheitel und sind deshalb kürzer als 63 mm."),
  ...achtung("Spiegelbild nicht vergessen: Das zweite Dach mit **ERSTELLEN → Spiegeln** erzeugen, nicht einfach ein zweites Mal drucken."),
  h2("6.6 Datei HA_14_Haltestellendach"),
  ...schritt("Gleiches Prinzip, kleiner", "Umriss **164 × 34 mm** mit spitzen Enden (Sechseck), Rautengitter wie beim Glasdach, Rand 2 mm. Zwei Stützen, Höhe **30 mm** über Ortsniveau."),
  h2("6.7 Datei HA_15_Eingang_Industrie", "eingang"),
  absatz("Auf der Industrieseite steht der Turm nicht auf einem Bahnsteig, sondern auf dem Boden. Damit trotzdem **derselbe 42-mm-Turm** passt, steht er auf einem **Stufenplateau** von 7,3 mm Höhe ab Oberkante Kork – genau die Höhe der Bahnsteige. Vor dem Eingang liegt ein kleiner überdachter Vorplatz wie an der Haltestelle."),
  ...schritt("Plateau", "Neue Konstruktion **HA_15_Eingang_Industrie**. Skizze auf **XY**: Rechteck **58 × 40 mm** (Turm plus Vorplatz). Extrusion **7,3 mm**."),
  ...schritt("Stufen", "Auf der Zugangsseite drei Stufen: je **10 mm** tief und **2,43 mm** hoch. Am einfachsten: Profil auf **XZ** als Treppenlinie zeichnen und um die Plateaubreite extrudieren, Vorgang **Verbinden**."),
  ...schritt("Vordach", "Gleiches Prinzip wie HA_14, nur kleiner: Sechseck **60 × 12 mm** mit spitzen Enden, Rautengitter, Rand 2 mm. Zwei Stützen aus Messingrohr Ø 2 mm, Vordach ca. **30 mm über dem Plateau**."),
  ...kontrolle("Turmhöhe 42 mm + Plateau 7,3 mm = Unterkante Brücke über der Industrieebene. Wenn dort das Gelände höher oder tiefer liegt, nur das Plateau anpassen – der Turm bleibt gleich."),
);
  return kap6;
}

// ---------- Kapitel 7: KV-Terminal und Gewerbegebiet ----------
function baueKap7() {
  neueSchritte();
const kap7 = [
  h1("7 Bauanleitung KV-Terminal und Gewerbe"),
  h2("7.1 Überblick"),
  absatz("Auf dem Gleis **Industrie 1** entsteht ein kleines **Terminal für den kombinierten Verkehr**. Ein **Portalkran** hebt Container und Sattelauflieger zwischen Taschenwagen, LKW und Lager um. Am Stumpfende sitzt eine **Kopframpe** für die Rollende Landstraße (RoLa). Der übrige Innenraum wird **Gewerbegebiet** mit zwei Anschlussgleisen."),
  ...bild("kv_terminal.png", 16, "KV-Terminal und Gewerbegebiet – Draufsicht (schematisch)"),
  ...hinweis("Beim Vorbild werden Sattelauflieger **mit dem Kran** in die Taschenwagen gehoben (Greifkanten am Auflieger). Über die Kopframpe fahren dagegen ganze LKW auf Niederflurwagen der RoLa."),
  punkt("**Zufahrt:** Straße von der Südkante über einen **Bahnübergang** über beide Hauptgleise ins Gewerbegebiet und weiter zur LKW-Spur am Kran."),
  punkt("**Wagen:** Doppel-Taschenwagen (T3000, ca. 214 mm), Containertragwagen (Sgns, ca. 123 mm). Auf das 58-cm-Ladegleis passen etwa zwei bis drei Wagen."),
  punkt("**Gewerbe:** flache Hallen (Baustoffhandel, Getränkelager, Spedition, Werkstatt) – sie verdecken den Blick auf den Bahnhof nicht."),
  ...tabelle(["Container (1:160)", "Länge × Breite × Höhe"], [
    ["40 Fuß", "76,2 × 15,2 × 16,2 mm"],
    ["20 Fuß", "37,9 × 15,2 × 16,2 mm"],
    ["Sattelauflieger (zum Vergleich)", "ca. 85 × 16 mm"],
  ], [4400, BREITE - 4400]),
  ...tipp("Containerlager-Füllung muss nicht detailliert sein: einfache Quader mit Rillen in den Seiten, in verschiedenen Farben gedruckt, sehen im Stapel sehr glaubhaft aus. Vorn am Rand lieber ein paar gekaufte, fein bedruckte Container."),
];
neueSchritte();
kap7.push(
  h2("7.2 Datei HA_20_Kranbahn"),
  ...schritt("Parameter", "Neue Konstruktion **HA_20_Kranbahn**, Parameter anlegen:"),
  ...dialog("Parameter ändern – Benutzerparameter", [
    ["Spur_Kran", "100 mm (Achsabstand der beiden Kranschienen)"], ["Laenge", "200 mm (ein Stück, zwei Stück hintereinander)"],
    ["Balken_b", "6 mm"], ["Balken_h", "so, dass Oberkante Messing = SO (auf Kork ca. 2,3 mm) – am Gleis messen"], ["Nut", "1,1 mm (für Messing-Vierkant 1 × 1 mm)"],
  ]),
  ...schritt("Balken", "Skizze auf **XY**: zwei Rechtecke **Laenge × Balken_b**, Mittellinien im Abstand **Spur_Kran**. Extrusion **Balken_h**.", "Auf der Oberseite jedes Balkens mittig eine Nut **Nut × Nut** über die ganze Länge zeichnen und **0,8 mm tief ausschneiden** – der Messingstab steht dann 0,2 mm über."),
  ...schritt("Ausrichten ohne Stege", "Zwischen den Balken liegen Ladegleis und LKW-Spur – dort darf **kein Quersteg** liegen. Stattdessen eine **Abstandslehre** drucken (Bügel mit zwei Nasen im Abstand **Spur_Kran**), die Balken damit beim Kleben ausrichten und die Lehre danach abnehmen."),
  ...kontrolle("Die Kranbahn liegt plan auf der Platte, die Oberkante des Messingstabs schließt mit dem Pflaster ab. Ladegleis und LKW-Spur liegen zwischen den beiden Schienen."),
  ...schritt("Druck", "PLA grau, 0,4-mm-Düse, flach. Messing-Vierkant mit Sekundenkleber in die Nut drücken."),
  h2("7.3 Datei HA_21_Portalkran"),
  ...bild("portalkran.png", 14.5, "Portalkran – Stirnansicht mit Taschenwagen, LKW und Lager"),
  absatz("Der Kran wird aus **flachen Einzelteilen** gedruckt und verklebt: zwei Stützrahmen, zwei Fachwerkwände für den Hauptträger, Deckplatte, Laufkatze und Spreader. Er fährt nicht motorisch – du schiebst ihn von Hand über den Wagen."),
  ...schritt("Parameter", "Neue Konstruktion **HA_21_Portalkran**, Parameter anlegen:"),
  ...dialog("Parameter ändern – Benutzerparameter", [
    ["Spur_Kran", "100 mm"], ["Lichte_H", "75 mm (Unterkante Träger über Pflaster)"], ["Traeger_L", "120 mm"],
    ["Traeger_H", "8 mm"], ["Traeger_B", "12 mm"], ["Radstand", "30 mm (Stützenabstand längs der Kranbahn)"], ["Wand", "1,5 mm"],
  ]),
  ...schritt("Stützrahmen", "Skizze auf **XZ**: ein **A-förmiger Rahmen** – unten **Radstand + 6 mm** breit, oben 20 mm, Höhe **Lichte_H**. Zwei schräge Stützen je **4 mm** breit, oben ein Querriegel 4 mm, unten ein Fahrwerksbalken **Radstand + 6 × 5 mm**.", "**Extrusion** um **3 mm**, Vorgang **Neuer Körper**. Unter dem Fahrwerksbalken eine Rille **1,3 mm breit, 0,8 mm tief** ausschneiden – sie läuft auf dem Messingstab."),
  ...schritt("Zweiter Stützrahmen", "**ERSTELLEN → Spiegeln** an einer Ebene im Abstand **Spur_Kran / 2** – so stehen beide Rahmen exakt auf Kranbahnspur."),
  ...schritt("Fachwerkwand des Trägers", "Skizze auf **XZ**: Rechteck **Traeger_L × Traeger_H**, mit **Versatz** (O) **1,2 mm** nach innen. Im Inneren eine Diagonale von unten links nach oben in **10 mm** Abstand und zurück (Zickzack) zeichnen, Linienbreite durch zweiten Versatz 0,6 mm.", "Mit **Rechteckiges Muster** in der Skizze über die ganze Länge wiederholen. Extrusion **Wand**, Vorgang **Neuer Körper**. Zweite Wand per **Verschieben/Kopieren** im Abstand **Traeger_B − Wand**."),
  ...tipp("Ist dir das Zickzack zu fummelig: Die dreieckigen Öffnungen als Dreiecke zeichnen und mit **Ausschneiden** aus der vollen Wand entfernen – das Ergebnis ist dasselbe."),
  ...schritt("Deck- und Bodenplatte", "Zwei Platten **Traeger_L × Traeger_B × 1 mm** oben und unten zwischen die Wände setzen, Vorgang **Neuer Körper**. Auf der Deckplatte bleibt in der Mitte ein Schlitz **2 mm** breit frei – darin läuft die Laufkatze."),
  ...schritt("Laufkatze und Spreader", "**Laufkatze:** Quader **15 × Traeger_B × 5 mm** mit Führungsnase 1,8 × 2 mm nach unten in den Schlitz.", "**Spreader:** Rahmen **76 × 15 × 3 mm** (Größe eines 40-Fuß-Containers), innen offen, an den Ecken vier Zapfen 1 × 1 mm. Hängt an zwei dunklen Fäden von der Laufkatze."),
  ...kontrolle("Lichte Höhe 75 mm reicht für einen doppelt gestapelten Container (2 × 16,2 mm) und einen Container auf dem Taschenwagen mit Abstand. Gesamthöhe ca. 88 mm."),
  ...schritt("Druck", "Alle Teile flach in **PLA** – Stützrahmen und Träger **gelb oder orange**, Laufkatze und Spreader **grau**. Feine Fachwerkwände mit der **0,2-mm-Düse**."),
  ...achtung("Den Kran **vor dem Verkleben** einmal trocken auf die Kranbahn stellen: Beide Rahmen müssen gleichzeitig auf beiden Messingstäben aufsitzen, sonst kippelt er."),
  h2("7.4 Datei HA_22_Kopframpe"),
  absatz("Die Kopframpe sitzt am Stumpfende des Ladegleises und ist zugleich der Prellbock. LKW fahren von der Seite hoch und über die Rampe auf die Niederflurwagen."),
  ...schritt("Parameter", "Neue Konstruktion **HA_22_Kopframpe**:"),
  ...dialog("Parameter ändern – Benutzerparameter", [
    ["H_Rampe", "Wagenboden über Grundplatte (am Modell messen, ca. SO-Höhe + 2,6 mm)"],
    ["Breite", "28 mm"], ["Plateau_L", "30 mm"], ["Auffahrt_L", "50 mm"], ["Puffer_H", "6,4 mm über SO (NEM 303 prüfen)"],
  ]),
  ...schritt("Plateau und Auffahrt", "Skizze auf **XZ** als Seitenprofil: Plateau **Plateau_L** lang auf Höhe **H_Rampe**, daran eine schräge Auffahrt **Auffahrt_L** bis auf 0. Extrusion um **Breite**."),
  ...schritt("Prellbockfront", "An der Gleisseite eine Stirnwand 3 mm dick, dazu zwei Pufferteller **Ø 2,5 mm** im Abstand **10,9 mm** (Vorbild 1750 mm) auf **Puffer_H**.", "Unten in der Mitte eine Aussparung ca. **12 mm breit** für das Gleis (Schienenfüße am Gleis nachmessen), damit die Rampe direkt am Schienenende anliegt."),
  ...schritt("Oberfläche", "Auf Plateau und Auffahrt Riffelblech andeuten: Rautenmuster **0,3 mm tief** ausschneiden (wie beim Glasdach, nur fein)."),
  ...tipp("Die Rampe nur aufstecken, nicht kleben – dann kann sie später wieder einem abnehmbaren Prellbock weichen."),
  h2("7.5 Datei HA_23_Bahnuebergang"),
  ...schritt("Fahrbahnplatten", "Neue Konstruktion **HA_23_Bahnuebergang**. Je Gleis drei Platten: eine zwischen den Schienen, zwei außen; zwischen den beiden Gleisen zusätzlich eine **Mittelplatte**. Straßenbreite **36 mm** (ca. 6 m).", "**Innenplatte:** Breite **9 mm − 2 × 1,1 mm Spurrille** = **6,8 mm**. **Außenplatten:** 8 mm. **Mittelplatte:** füllt den Rest bis zum Nachbargleis – bei 40 mm Gleisabstand ca. 11 mm, am Gleis messen."),
  ...schritt("Höhe", "Plattenoberkante **0,2 mm unter SO** – sonst schleifen Radkränze und Schleifer. Dicke = Schienenhöhe Code 55 (1,4 mm) minus 0,2 mm = **1,2 mm**, die Platten liegen auf den Schwellen."),
  ...schritt("Druck und Einbau", "PLA dunkelgrau, 0,2-mm-Düse, Oberfläche mit leichter Pflasterstruktur. Erst einbauen, wenn beide Gleise liegen und probegefahren sind; mit wenig Kleber auf die Schwellen setzen."),
  ...kontrolle("Mit dem tiefsten Fahrzeug (Schneepflug, Taschenwagen) über den Bahnübergang fahren – nichts darf hängen bleiben."),
  ...tipp("Andreaskreuze mit Blinklicht gibt es fertig. Digital kannst du das Blinken über einen Belegtmelder vor dem Übergang schalten."),
);
  return kap7;
}

// ---------- Kapitel 8: Elektrik und Digital ----------
function baueKap8() {
  neueSchritte();
const kap8 = [
  h1("8 Elektrik und Digital", "elektrik"),
  h2("8.1 Konzept"),
  absatz("Die Anlage wird **digital (DCC)** gefahren – teils automatisch per PC, teils von Hand. Die Hauptstrecke, der Wendel und der Schattenbahnhof laufen **automatisch** über ein Steuerprogramm. Den **Rangierbetrieb** (Rangiergruppe, KV-Terminal, Gewerbe, Hafen) fährst du **von Hand mit der Köf** über den Handregler."),
  ...bild("elektrik_uebersicht.png", 15, "Aufbau: Zentrale, Booster, drei Stromabschnitte und Belegtmelder"),
  ...tabelle(["Gerät", "Aufgabe"], [
    ["Z21 (schwarz)", "Zentrale mit eigenem Programmiergleis, LAN zum Router, CAN-Bus für Melder und Booster; versorgt Abschnitt A"],
    ["Z21 dual Booster", "zwei getrennte Ausgänge für Abschnitt B (Wendel, Schattenbahnhof) und C (Rangierbereich)"],
    ["WLAN-Router", "verbindet PC, Handy-App und Z21 WLANMAUS (die Z21 multiMAUS wird per Kabel an den X-Bus gesteckt)"],
    ["Belegtmelder mit RailCom", "melden, wo welche Lok steht – Grundlage für den Automatikbetrieb"],
    ["Steuerprogramm (PC)", "iTrain, Rocrail oder TrainController – fährt die Züge im Automatikbereich"],
  ], [3000, BREITE - 3000]),
  ...hinweis("Vor dem Kauf die aktuellen Gerätebezeichnungen und Bus-Anschlüsse beim Hersteller prüfen. Wichtig ist das Prinzip: eine Zentrale mit Programmiergleis, ein Booster mit zwei Ausgängen und RailCom-fähige Melder."),
  h2("8.2 Stromabschnitte"),
  ...tabelle(["Abschnitt", "Bereich", "Versorgung", "Betrieb"], [
    ["A", "Strecke obere Ebene, Bahnhof, Abzweig", "Z21", "automatisch"],
    ["B", "Wendel, Schattenbahnhof, Aufgleisgleis", "Booster Ausgang 1", "automatisch"],
    ["C", "Rangiergruppe, KV-Terminal, Gewerbe, Hafen", "Booster Ausgang 2", "von Hand"],
  ], [1200, 4200, 2200, BREITE - 7600]),
  punkt("Jeder Abschnitt hat seine **eigene Kurzschlussabschaltung**: Ein Kurzschluss beim Rangieren hält den Schattenbahnhof nicht an."),
  punkt("An den Grenzen zwischen zwei Abschnitten werden **beide Schienen** getrennt (isolierende Schienenverbinder)."),
  ...achtung("Die Polarität an jeder Abschnittsgrenze muss gleich sein – sonst gibt es beim Überfahren einen Kurzschluss. Farbregel konsequent einhalten (siehe " + ref("verkabelung") + ")."),
];
neueSchritte();
kap8.push(
  h2("8.3 Verkabelung", "verkabelung"),
  ...schritt("Farbregel festlegen", "Für die zweigleisige Strecke im Richtungsbetrieb: **rot = linke Schiene in Fahrtrichtung**, **schwarz = rechte Schiene**. In Bereichen ohne feste Fahrtrichtung (Schattenbahnhof, Rangieren, Hafen) die Farbe vom anschließenden Streckengleis weiterführen. Auf einen Zettel schreiben und an die Anlage kleben. Beispiel Wendel: siehe " + ref("schnittstellen") + "."),
  ...schritt("Hauptleitung", "Je Abschnitt zwei Drähte **1,5 mm²** unter der Platte entlang der Gleise, leicht verdrillt. Sternförmig vom Gerät zum Abschnitt – **keine geschlossene Ringleitung**."),
  ...schritt("Einspeisungen", "Dünne Drähte **0,25–0,5 mm²** von unten an die Schienen löten – möglichst an **jedes Stück Flexgleis**, mindestens alle 1–1,5 m. Bohrung Ø 1,5 mm durch Kork und Platte, Draht vor dem Verlegen an die Schienenunterseite löten."),
  ...tipp("Bei Code 55 ist der Schienenfuß sehr schmal. Draht vorher verzinnen, Lötkolben heiß und kurz (2–3 s), damit die Schwellen nicht schmelzen."),
  ...schritt("Unifrog-Weichen", "Unifrog-Weichen brauchen **keine isolierenden Schienenverbinder**. Den Herzstückdraht an einen **Umschaltkontakt am Weichenantrieb** oder an einen **elektronischen Herzstückpolarisator** anschließen.", "Weichenantriebe am besten langsam laufend (Motor oder Servo) mit Weichendecoder."),
  ...achtung("Ohne angeschlossenes Herzstück bleibt die Köf mit ihrem kurzen Radstand auf jeder Weiche stehen. Im Rangierbereich ist das Herzstück deshalb Pflicht."),
  ...schritt("Kreuzung am Abzweig", "Peco liefert Code-55-Kreuzungen in Spur N nach unserem Stand als **Insulfrog** (z. B. SL-394F – Typ und Winkel beim Kauf prüfen). Dann ist **keine Polarisierung** nötig, die Herzstücke sind aber stromlos. Für die Streckenloks ist das unkritisch, die Köf fährt dort nicht.", "Sollte es doch eine Unifrog-Ausführung sein: je Herzstück einen elektronischen Herzstückpolarisator. Vor dem Einbau einzeln mit allen Loks testen."),
  ...schritt("Münztest", "Nach jedem verkabelten Abschnitt mit einer Münze an mehreren Stellen über beide Schienen tippen. Die Abschaltung muss **sofort** auslösen. Tut sie es nicht oder nur träge: Leitung zu dünn, zu lang oder schlechte Lötstelle."),
  h2("8.4 Blöcke und Belegtmelder"),
  absatz("Für jeden Block wird **eine Schiene** (immer dieselbe Seite) mit isolierendem Schienenverbinder getrennt. Die Einspeisung dieser Schiene läuft über einen Ausgang des Melders, die andere Schiene bleibt durchgehend an der Hauptleitung."),
  ...tabelle(["Bereich", "Blöcke", "Bemerkung"], [
    ["Bahnhof (4 Gleise)", "8", "je Gleis Halteabschnitt und Bremsabschnitt"],
    ["Strecke obere Ebene", "ca. 6", "je Richtung 3 Blöcke"],
    ["Wendel", "6", "je Gleis 3 Blöcke"],
    ["Schattenbahnhof (4 Abstellgleise)", "12", "je Gleis 3 Abschnitte – zwei Züge hintereinander"],
    ["Durchgehendes Hauptgleis unten", "2", ""],
    ["Ein- und Ausfahrt, Aufgleisgleis", "3", ""],
    ["Rangierbereich", "ca. 4", "Übergabegleis, Annäherung Bahnübergang"],
    ["Summe", "ca. 41", "6 Melder mit je 8 Abschnitten reichen mit Reserve"],
  ], [3600, 1200, BREITE - 4800]),
  ...tipp("Die Blockgrenzen schon beim Gleisverlegen festlegen und die Trennstellen beim Kork-Kleben markieren – nachträglich sind sie unter dem Schotter schwer zu finden."),
  h2("8.5 Belegtanzeige im Gleisbild"),
  absatz("Für die Anzeige im Gleisbild brauchst du **keine zusätzlichen Decoder in den Loks**. Notwendig sind nur die Belegtmelder, getrennte Blöcke und das Gleisbild im Steuerprogramm. Damit die Anzeige zuverlässig ist, gehören aber noch einige Dinge dazu."),
  ...tabelle(["Baustein", "Wozu", "Pflicht?"], [
    ["Belegtmelder (z. B. M1 am Wendel)", "meldet Stromfluss im Block an die Zentrale", "ja"],
    ["Getrennte Blöcke", "eine Schiene je Block über einen Melderkanal", "ja"],
    ["Gleisbild im Steuerprogramm", "jedem Block seinen Melderkanal zuordnen", "ja"],
    ["Widerstandsachsen", "damit auch Wagen ohne Beleuchtung erkannt werden", "ja – mindestens im letzten Wagen"],
    ["RailCom in Decoder und Melder", "zeigt, welche Lok im Block steht", "empfohlen"],
    ["Weichendecoder", "Weichen und Fahrstraßen per Klick stellen", "für Automatik ja"],
    ["Rückmeldung Weichenlage", "meldet, ob die Weiche wirklich umgelaufen ist", "optional"],
  ], [3400, 4400, BREITE - 7800]),
);
neueSchritte();
kap8.push(
  ...schritt("Widerstandsachsen einbauen", "Mindestens der **letzte Wagen jedes Zuges** bekommt eine Achse mit Widerstand – besser jeder Wagen, dann wird auch ein abgerissener Zugteil erkannt.", "Üblich in Spur N: ca. **10 kΩ** je Achse. Möglich sind fertige Widerstandsradsätze, ein SMD-Widerstand (Bauform 0603 oder 0805) mit Leitsilber zwischen Rad und Achse oder ein Strich Leitlack auf der isolierten Seite."),
  ...achtung("Ohne Widerstandsachse „sieht“ die Anlage einen Wagen nicht, der allein in einem Block steht. Im Schattenbahnhof und im Wendel kann der nächste Zug dann auffahren."),
  ...tipp("Wagen mit Innenbeleuchtung (z. B. die S-Bahn) werden meist schon über die Beleuchtung erkannt. Mit einer Lok und einem einzelnen Wagen im Block testen."),
  ...schritt("RailCom einschalten", "In jedem Lokdecoder RailCom aktivieren (ESU und Zimo: im Decoder einstellbar, meist über CV 29 und CV 28). Die schwarze Z21 erzeugt die nötige Austastlücke selbst.", "Im Steuerprogramm prüfen, ob beim Einfahren in einen Block die richtige Lokadresse erscheint."),
  ...schritt("Weichendecoder", "Für Automatik und Fahrstraßen braucht jede Weiche einen **Antrieb mit Weichendecoder**. Das Unifrog-Herzstück wird aus dem Block gespeist, in dem die Weiche liegt – also über den Melderkanal dieses Blocks. Bei Unifrog-Weichen sollte der Antrieb (oder der Decoder) einen **Umschaltkontakt für das Herzstück** haben – sonst einen Herzstückpolarisator verwenden (siehe " + ref("verkabelung") + ").", "Langsam laufende Antriebe (Motor oder Servo) schonen die feinen Code-55-Weichen."),
  ...schritt("Rückmeldung der Weichenlage (optional)", "Ein Endlagenkontakt am Antrieb meldet über einen freien Melderkanal, ob die Weiche wirklich umgelaufen ist. Für den Automatikbetrieb ist das zusätzliche Sicherheit, aber kein Muss."),
  ...kontrolle("Jeden Block mit Lok **und** mit einem einzelnen Wagen testen: Beide müssen im Gleisbild als belegt erscheinen."),
);
  return kap8;
}

function baueKapBauablauf() {
  neueSchritte();
  return [
  h1("Bauablauf – wo und wie anfangen", "bauablauf"),
  absatz("Die Reihenfolge folgt drei Regeln: **erst testen, dann bauen** – **unten vor oben**, weil der Schattenbahnhof später schwer zugänglich ist – und **Elektrik gleich beim Gleisbau** mitverlegen. Geschottert und gestaltet wird erst, wenn alles fährt."),
  h2("Phase 1 – Tisch und Proben"),
  punkt("Z21 mit Programmiergleis auf dem Tisch in Betrieb nehmen, alle Loks programmieren, RailCom einschalten, Widerstandsachsen einbauen."),
  punkt("Gleisplan 1:1 auf Papier ausdrucken und auslegen, **maximale Zuglänge** festlegen (" + ref("zuglaengen") + ")."),
  punkt("Wendel-Probe: drei Platten, Anlaufklötze, Konsolen, Bettungsvergleich, Lichtraum mit den längsten Wagen (" + ref("probelauf") + ")."),
  punkt("Kreuzung und eine Unifrog-Weiche einzeln mit allen Loks testen – auch mit der Köf."),
  h2("Phase 2 – Unterbau"),
  punkt("Rahmen, untere Platte und Erweiterung bauen (Erweiterung 4 mm tiefer), Stützen außerhalb des Lichtraums (" + ref("unterbau") + ")."),
  punkt("Revisionsöffnung in der Wendelmitte und abnehmbare Segmente über dem Schattenbahnhof vorsehen."),
  punkt("Hauptleitungen für die Abschnitte und Plätze für Booster und Melder vorbereiten."),
  h2("Phase 3 – Untere Ebene"),
  punkt("Kork verlegen, Blockgrenzen und Trennstellen markieren."),
  punkt("Schattenbahnhof, Weichen und Aufgleisgleis verlegen, Einspeisungen sofort anlöten."),
  punkt("Abschnitt B verkabeln, Münztest, Melder anschließen; unten vorübergehend als Kreis fahren."),
  h2("Phase 4 – Wendel"),
  punkt("Anlaufklötze und Gewindestangen setzen, Konsolen einstellen, Platten einbauen."),
  punkt("TPU-Bettung, Gleis und Blöcke W1–W6 verkabeln (" + ref("schnittstellen") + ")."),
  punkt("Dauerlauf beider Gleise mit allen Zügen; die beiden Ausfahrten besonders prüfen."),
  h2("Phase 5 – Obere Ebene"),
  punkt("Stützen und obere Platte mit abnehmbaren Segmenten, Ausfahrplatten am Wendel."),
  punkt("Abzweig mit Kreuzung, Strecke und Bahnhofsgleise verlegen; Abschnitt A anschließen."),
  punkt("Gesamtrundkurs testen, Automatik zunächst mit **einem** Zug."),
  h2("Phase 6 – Rangierbereich und Terminal"),
  punkt("Abschnitt C, Herzstücke anschließen, Köf-Test auf allen Weichen."),
  punkt("Kranbahn, Bahnübergang und Kopframpe einbauen."),
  h2("Phase 7 – Bahnhofsbauten"),
  punkt("Inselbahnsteige und Stufenplateau, Kantenabstand mit dem längsten Wagen prüfen."),
  punkt("Aufzugtürme, Brücke (LEDs vorher verdrahten), Glasdächer, Oberleitungsmasten."),
  h2("Phase 8 – Steuerung"),
  punkt("Alle Blöcke und Fahrstraßen im Steuerprogramm einrichten."),
  punkt("Mehrzugbetrieb, Übergabe an den Handbereich, Sound (" + ref("steuerung") + ")."),
  h2("Phase 9 – Gestaltung"),
  punkt("Ortsplatte (abnehmbar), Gelände, Straßen."),
  punkt("Schottern erst nach allen Tests (elastischer Schotterkleber), dann Gebäude und Details."),
  ];
}

function baueKapUnterbau() {
  neueSchritte();
  return [
  h1("Unterbau", "unterbau"),
  absatz("Der Unterbau ist noch nicht festgelegt. Die folgenden Punkte sind Planungswerte und Empfehlungen – vor dem Bau entscheiden."),
  ...tabelle(["Thema", "Empfehlung"], [
    ["Platten", "Sperrholz, Planungswert ca. 19 mm für die obere Platte (daraus folgen 155 mm Freiraum bei 174 mm SO–SO)"],
    ["Stützen der oberen Ebene", "nur außerhalb des Lichtraums der Abstellgleise und Weichenstraßen; Lage auf dem 1:1-Plan festlegen"],
    ["Zugang Schattenbahnhof", "Nord- und Ostseite stehen an der Wand: obere Ebene über dem Schattenbahnhof in abnehmbaren Segmenten oder mit Klappen; Weichenstraßen möglichst vorn bzw. im Süden"],
    ["Erweiterung (Wendel)", "4 mm tiefer als die Grundplatte, damit die erste Wendelplatte bündig ist (" + ref("schnittstellen") + ")"],
    ["Revisionsöffnung", "in der Wendelmitte ca. Ø 450 mm (innerhalb der inneren Stangen R 240)"],
    ["Ortsplatte", "über Wendel und Abzweig abnehmbar, mit Passstiften"],
  ], [3000, BREITE - 3000]),
  ...achtung("Mit 155 mm Freiraum und 1 m Tiefe kommt man an die Wandseite des Schattenbahnhofs kaum heran. Die Zugänge **vor** dem Bau der oberen Ebene festlegen."),
  ];
}

function baueKapSteuerung() {
  neueSchritte();
  return [
  h1("Steuerung, Automatik und Sound", "steuerung"),
  h2("Automatik und Rangieren zusammen"),
  punkt("Im Steuerprogramm gehören nur die Abschnitte A und B zum **Automatikbereich**. Der Rangierbereich C wird als **Handbereich** angelegt – das Programm fährt dort keine Züge hinein."),
  punkt("**Übergabegleis:** Ein Güterzug fährt automatisch auf das Übergabegleis. Danach übernimmst du mit der Köf am Handregler, stellst die Wagen zu und baust den Zug neu zusammen. Zum Schluss gibst du ihn im Programm wieder frei."),
  punkt("Die Köf meldet sich über RailCom in jedem Block, auch im Handbereich. So sieht das Programm, wenn sie auf ein Gleis der Hauptstrecke fährt, und hält den nächsten Zug davor an."),
  ...tabelle(["Steuerprogramm", "Eigenschaft"], [
    ["iTrain", "übersichtliche Oberfläche, kostenpflichtig, Testversion verfügbar"],
    ["Rocrail", "kostenlos, sehr mächtig, aber steilere Lernkurve"],
    ["TrainController", "sehr umfangreich, Hand- und Automatikbetrieb kombinierbar, teurer"],
  ], [3000, BREITE - 3000]),
  h2("Aufzüge schalten"),
  punkt("Die drei Aufzug-Servos hängen an **einem Servodecoder mit vier Ausgängen** (Abschnitt A, Zubehöradressen). Im Steuerprogramm je Turm ein Zubehör „Aufzug“ anlegen; ein Klick fährt die Kabinen um."),
  punkt("Im Automatikbetrieb kann das Programm die Aufzüge auch zeitgesteuert oder bei Zughalt im Bahnhof fahren lassen."),
  h2("Sound", "sound"),
  absatz("**Köf (Liliput L162585, Köf 11 056 = Bauart Köf III, 49 mm):** In der Lok ist kaum Platz für Lautsprecher und Sounddecoder. Deshalb bekommt der Rangierbereich einen **festen Sounddecoder unter der Platte**."),
  ...schritt("Stationärer Sound für die Köf", "Einen LokSound-Decoder mit passendem Sound (Köf III / BR 332 – Soundprojekt beim Händler prüfen) unter der Platte im Rangierbereich befestigen, Gleisanschluss an die Hauptleitung von Abschnitt C.", "Als Last statt des Motors einen kleinen Motor oder Lastwiderstand anschließen (vorher auf dem Tisch testen, wie der Decoder ohne echten Motor reagiert).", "Lautsprecher **20–28 mm** mit Schallkapsel von unten unter eine Öffnung in der Platte setzen, oben mit Gebäude oder Schotter abdecken.", "Den Decoder auf **dieselbe Adresse wie die Köf** programmieren und bei ihm **RailCom ausschalten** (CV 29 Bit 3), sonst senden zwei Decoder gleichzeitig. Fahrstufen und Beschleunigung (CV 3, CV 4) an die Köf anpassen."),
  ...tipp("Weil der Rangierbereich klein ist, fällt kaum auf, dass der Sound nicht mitfährt. Ein großer Lautsprecher unter der Platte klingt deutlich voller als ein Winzling in der Lok."),
  absatz("**S-Bahn (Piko BR 440, PluX12):** Der Triebwagen hat eine PluX12-Schnittstelle. Für den Sound gibt es drei Wege – siehe Tabelle."),
  ...tabelle(["Weg", "Vorteil", "Nachteil"], [
    ["Piko 46190 (Sound mit Lautsprecher, SUSI) zusammen mit dem mitgelieferten Piko-Decoder", "laut Händlerangaben für Talent 2 / Coradia BR 440 vorgesehen", "nur wenn der Piko-Decoder eine SUSI-Buchse hat – prüfen"],
    ["Sounddecoder mit PluX12-Stecker (z. B. ZIMO MS540P12)", "direkt in die Schnittstelle, kein Löten", "anderer Hersteller als die Köf"],
    ["ESU LokSound 5 Nano (Einzellitzen oder E24 mit Adapter)", "gleiche Software wie die übrigen ESU-Decoder", "kein PluX12-Stecker ab Werk – Adapter oder Löten nötig"],
  ], [3600, 3000, BREITE - 6600]),
  ...hinweis("PluX-Decoder richten sich am Indexstift (Pin 11) aus. Ein PluX16-Decoder passt mechanisch auch auf eine PluX12-Schnittstelle, braucht aber mehr Platz. Vor dem Aufstecken Einbauraum und Pin 1 prüfen."),
  ];
}

function baueAnhangA() {
  neueSchritte();
  return [
  h1("Arbeiten mit Fusion", "anhangFusion", true, "A"),
  h2("Arbeitsweise und Dateiliste"),
  absatz("Wie bei den Schwalm-Arkaden wird **jedes Teil für sich am Ursprung (0|0|0)** konstruiert. Im Dokument stehen deshalb nur Teilmaße, keine Lagekoordinaten in der Anlage. Einstellung: **Z nach oben**, Einheit **mm**."),
  ...tabelle(["Datei", "Inhalt"], [
    ["HA_01_Wendelplatte", "Flache 30°-Platte des Wendels, 4 mm, mit Schwalbenschwanz"],
    ["HA_02_Konsolen", "Flache Auflager innen und außen an jedem Plattenstoß"],
    ["HA_03_Gleisbettung", "TPU-Bogenstreifen unter den Wendelgleisen (30° und 15°)"],
    ["HA_04_Anlaufkloetze", "Acht Klötze für die Stöße 1–4 am Wendelanfang"],
    ["HA_05_Ausfahrplatte", "Ebene 4-mm-Platte für die obere Wendelausfahrt bis außerhalb R 351"],
    ["HA_02_Sonderkonsole_60", "Verlängerte Konsole für die versetzte Stange bei 60°"],
    ["HA_10_Inselbahnsteig", "Linsenförmiger Inselbahnsteig"],
    ["HA_11_Aufzugturm", "Rechteckiger Glasturm mit Doppelaufzug und umlaufender Treppe"],
    ["HA_12_Glasbruecke", "Brücke mit Läden, zweiteilig"],
    ["HA_13_Glasdach", "Rautengitter-Dach, spitz zulaufend"],
    ["HA_14_Haltestellendach", "Vordach Bus und Tram"],
    ["HA_15_Eingang_Industrie", "Stufenplateau mit Vordach für den Turm auf der Industrieseite"],
    ["HA_20_Kranbahn", "Zwei Kranschienen mit Messing-Vierkant, Spur 100 mm"],
    ["HA_21_Portalkran", "Portalkran aus flachen Teilen mit Laufkatze und Spreader"],
    ["HA_22_Kopframpe", "RoLa-Rampe am Stumpfende, zugleich Prellbock"],
    ["HA_23_Bahnuebergang", "Fahrbahnplatten für die Zufahrt zum Gewerbegebiet"],
  ], [3400, BREITE - 3400]),
  ];
}

function baueAnhangC() {
  neueSchritte();
  return [
  h1("Druckdateien und Stückzahlen", "druckliste", true, "C"),
  absatz("Die Teile sind in **SolidCraft** konstruiert und als **3MF** (direkt für Bambu Studio), **STEP** (für Fusion) und **SC** (SolidCraft mit Bauverlauf) geliefert. Alle Teile sind per Volumen gegen eine Handrechnung geprüft."),
  ...tabelle(["Datei", "Stück", "Material", "Hinweis"], [
    ["HA_01_Wendelplatte", "42", "PETG", "zwei passen zusammen aufs Bett; Spiel 0,15 mm je Seite"],
    ["HA_02_Konsolen (innen + außen)", "38 innen, 35 außen", "PETG", "Stöße 5–42"],
    ["HA_02_Sonderkonsole_60", "3", "PETG", "Stöße 11, 23, 35"],
    ["HA_04_Anlaufkloetze", "1 Satz (8)", "PETG", "Stöße 1–4"],
    ["HA_05_Ausfahrplatte", "1", "PETG", "obere Ausfahrt"],
    ["HA_03_Bettung_aussen_30", "41", "TPU 95A", "R 320"],
    ["HA_03_Bettung_aussen_15", "2", "TPU 95A", "Anfang und Ende"],
    ["HA_03_Bettung_innen_30", "41", "TPU 95A", "R 280"],
    ["HA_03_Bettung_innen_15", "2", "TPU 95A", "Anfang und Ende"],
    ["HA_11_Turm_Faltwand", "3", "PETG schwarz", "0,2-mm-Düse, 0,1 mm Schicht"],
    ["HA_11_Glasschacht_Faltwand", "3", "PETG schwarz", "0,2-mm-Düse, 0,1 mm Schicht"],
    ["HA_11_Schacht_Boden_Kopf", "3", "PLA grau", "Boden und Kopfstück"],
    ["HA_11_Kabine", "6", "PLA oder PETG", "stehend, 0,2-mm-Düse"],
    ["HA_11_Servohalter", "3", "PETG", "liegend"],
    ["HA_11_Servohebel", "3", "PETG", "liegend"],
    ["HA_11_Treppe (Lauf lang, Lauf kurz, Podest)", "je Turm 2 / 2 / 4", "PLA grau", "liegend"],
    ["HA_15_Stufenplateau", "1", "PLA grau", "mit Mulde für den Turm"],
  ], [3300, 1500, 1500, BREITE - 6300]),
  ...hinweis("Noch nicht als Datei vorhanden: Inselbahnsteige, Glasbrücke, Glasdächer und Haltestellendach. Die Bahnsteige hängen von der tatsächlichen Gleislage ab und werden nach dem Verlegen gebaut."),
  ];
}

// ---------- Dokument zusammensetzen ----------
/** Reihenfolge der Kapitel im Dokument. */
const REIHENFOLGE = [baueKap1, baueKapBauablauf, baueKap2, baueKap3, baueKapUnterbau, baueKap8, baueKap5, baueKap6, baueKap7, baueKapSteuerung, baueAnhangA, baueKap4, baueAnhangC];
const bildStart = bildNr;
/** Baut alle Kapitel; zwei Durchläufe, damit Verweise auf spätere Abschnitte stimmen. */
function baueInhalt() {
  kapNr = 0; bildNr = bildStart; VERZ = [];
  return REIHENFOLGE.flatMap((f) => f());
}
baueInhalt();
/** Inhaltsverzeichnis aus dem ersten Durchlauf (ohne Seitenzahlen). */
const verzeichnis = [
  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Inhalt")] }),
  ...VERZ.map((e) => new Paragraph({
    spacing: { before: e.ebene === 1 ? 80 : 0, after: 0, line: 240 },
    indent: { left: e.ebene === 1 ? 0 : 400 },
    children: [new TextRun({ text: e.text, bold: e.ebene === 1, size: e.ebene === 1 ? 19 : 17 })],
  })),
];
const inhalt = [...verzeichnis, ...baueInhalt()];

const doc = new Document({
  creator: "Andy Jäckel",
  title: "Heimanlage Spur N – Bahnhof & Gleiswendel",
  styles: {
    default: { document: { run: { font: SCHRIFT, size: 21, color: FARBE.text } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: SCHRIFT, size: 34, bold: true, color: FARBE.titel },
        paragraph: { spacing: { before: 120, after: 200 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: SCHRIFT, size: 26, bold: true, color: FARBE.titel },
        paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: SCHRIFT, size: 22, bold: true, color: FARBE.titel },
        paragraph: { spacing: { before: 200, after: 80 }, keepNext: true, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [{ reference: "punkte", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [
    { properties: { page: { margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } }, children: deckblatt },
    {
      properties: { page: { margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
      headers: { default: new Header({ children: [new Paragraph({
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: FARBE.linie, space: 4 } },
        children: [new TextRun({ text: "Heimanlage Spur N · Bahnhof, Wendel & Terminal", size: 17, color: FARBE.grau })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "Seite ", size: 17, color: FARBE.grau }), new TextRun({ children: [PageNumber.CURRENT], size: 17, color: FARBE.grau })] })] }) },
      children: inhalt,
    },
  ],
});

Packer.toBuffer(doc).then((puffer) => {
  fs.writeFileSync("Heimanlage_Spur_N_Bahnhof_Wendel.docx", puffer);
  console.log("Dokument geschrieben");
});
