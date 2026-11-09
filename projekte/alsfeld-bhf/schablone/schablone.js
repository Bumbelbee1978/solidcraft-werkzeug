/**
 * Baut das Word-Dokument „Wendel – Bohrschablone 1:1“.
 * Teil 1: Anleitung, Übersicht und Höhentabelle (normale Ränder).
 * Teil 2: 12 Kacheln A1–D3 im Maßstab 1:1 (A4 hochkant, 10 mm Rand).
 */
const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType,
        AlignmentType, HeadingLevel, BorderStyle, ShadingType, PageBreak } = require("docx");

const MM = 96 / 25.4;                       // Pixel je mm (docx-js rechnet mit 96 dpi)
const kacheln = JSON.parse(fs.readFileSync("kacheln.json"));
const tabelle = JSON.parse(fs.readFileSync("tabelle.json"));

/** Absatz mit **fett**-Markierung. */
function absatz(text, opt = {}) {
  const teile = text.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map(t =>
    t.startsWith("**") ? new TextRun({ text: t.slice(2, -2), bold: true }) : new TextRun(t));
  return new Paragraph({ children: teile, spacing: { after: 100 }, ...opt });
}
/** Aufzählungspunkt. */
const punkt = t => absatz(t, { bullet: { level: 0 } });
/** Überschrift. */
const ueber = (t, ebene = HeadingLevel.HEADING_1) => new Paragraph({ text: t, heading: ebene, spacing: { before: 200, after: 120 } });

const rand = { style: BorderStyle.SINGLE, size: 4, color: "999999" };
const raender = { top: rand, bottom: rand, left: rand, right: rand };
/** Tabellenzelle. */
function zelle(text, breite, kopf = false) {
  return new TableCell({
    width: { size: breite, type: WidthType.DXA }, borders: raender,
    shading: kopf ? { fill: "DCE8F5", type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({ children: [new TextRun({ text, bold: kopf, size: 18 })] })],
  });
}

// ---------- Höhentabelle ----------
const sp = [900, 1500, 1500, 1500, 1500, 1500, 1060];     // Summe 9460 DXA
const kopf = new TableRow({ tableHeader: true, children: ["Stange", "Lage", "Ebene 1", "Ebene 2", "Ebene 3", "Ebene 4", "Länge*"].map((t, i) => zelle(t, sp[i], true)) });
const reihen = tabelle.map(z => {
  const e = z.eintraege.map(([m, w]) => /^\d/.test(w) ? `St.${m}: ${w} mm` : `St.${m}: ${w.replace("Platte liegt auf dem Brett", "Brett").replace("Anlaufklotz", "Klotz")}`);
  while (e.length < 4) e.push("–");
  return new TableRow({ children: [z.name, z.lage, ...e, `${z.laenge} mm`].map((t, i) => zelle(t, sp[i])) });
});

const teil1 = [
  new Paragraph({ children: [new TextRun({ text: "Wendel – Bohrschablone 1:1", bold: true, size: 40 })], spacing: { after: 80 } }),
  absatz("Erweiterungsbrett 70 × 70 cm · 24 Gewindestangen M6 · Höhen der Muttern ab Oberkante Brett"),
  ueber("1. Drucken"),
  punkt("Im Druckdialog **„Tatsächliche Größe“ / 100 %** wählen – **nicht** „An Seite anpassen“."),
  punkt("Auf den Blättern A3–D3 ist unten ein **Prüfmaß** – es muss mit dem Messschieber genau **100 mm** messen. Wenn nicht: Druckereinstellung prüfen."),
  ueber("2. Zusammenkleben"),
  punkt("12 Blätter: **4 Spalten (A–D) × 3 Reihen (1–3)**, unten rechts auf jedem Blatt steht der Name."),
  punkt("Den **grauen Streifen** links bzw. oben an der gestrichelten Linie abschneiden und das Blatt auf das Nachbarblatt legen, bis Kreise und Gitterlinien genau übereinander liegen. Mit Klebeband fixieren."),
  punkt("Der schwarze Rahmen ist die **Brettkante**. Schablone bündig auflegen: **Norden an die Wand**, **Osten zur Grundplatte**, mit Malerkrepp festkleben."),
  new Paragraph({ children: [new ImageRun({ type: "png", data: fs.readFileSync("uebersicht.png"), transformation: { width: 125 * MM, height: 125 * MM } })], alignment: AlignmentType.CENTER }),
  ueber("3. Ankörnen und Bohren"),
  punkt("Jeden Kreuzungspunkt mit Körner oder Nagel **durch das Papier** markieren, dann die Schablone abnehmen."),
  punkt("**Senkrecht bohren** (Bohrständer oder Winkel daneben stellen) – eine schiefe Stange verschiebt die oberen Konsolen."),
  punkt("Lochgröße für die **Einschlagmutter M6** von **unten** einsetzen (meist Ø 8 mm – Maß auf der Packung). Die Stange von oben eindrehen und unten mit **Scheibe + Kontermutter** sichern."),
  punkt("**Kein Filz an den Stangen:** Filz gibt nach, die Stangen wackeln und die Höhen wandern. Zur Schalldämmung lieber Filz oder Kork **unter das ganze Brett**."),
  punkt("Warum Einschlagmuttern: Die Konsole an Stoß 5 sitzt nur 11,5 mm über dem Brett – eine Mutter oben auf dem Brett hätte dort keinen Platz. So bleibt die Brettoberseite überall frei."),
  ueber("4. Muttern einstellen"),
  punkt("Die Zahl in der Tabelle ist die Höhe der **Oberkante der oberen Mutter** (darauf kommt die Scheibe 1,6 mm und dann die Konsole) – gemessen **ab Oberkante Brett**."),
  punkt("Auf jeder Stange liegen die Ebenen genau **51,0 mm** auseinander (eine Windung). Tipp: unterste Mutter mit dem Messschieber (Tiefenmaß) einstellen, die nächste dann 51 mm darüber – so bleibt der Messschieber im Bereich bis 150 mm."),
  punkt("Neben jedem Loch auf der Schablone ist ein Feld **„Ist: ____“** – dort den gemessenen Wert eintragen."),
  punkt("**St.** = Stoßnummer (0 = Einfahrt unten, 42 = Ausfahrt oben). Stöße 1–4 liegen auf **Anlaufklötzen**, A11 trägt die **Sonderkonsolen** (5 mm statt 6 mm)."),
  new Paragraph({ children: [new PageBreak()] }),
  ueber("5. Höhentabelle aller Stangen"),
  new Table({ width: { size: 9460, type: WidthType.DXA }, columnWidths: sp, rows: [kopf, ...reihen] }),
  absatz("* Stangenlänge **über** dem Brett, gerundet. Dazu kommen Brettdicke und ca. 10 mm für Scheibe und Kontermutter unten.", { spacing: { before: 120 } }),
  absatz("I = innen (R 240), A = außen (R 343, A11 auf R 395). Lage = Winkel in der Draufsicht (0° = Osten, gegen den Uhrzeigersinn)."),
];

// ---------- Kacheln ----------
const teil2 = kacheln.map((n, i) => new Paragraph({
  pageBreakBefore: i > 0, spacing: { before: 0, after: 0 },
  children: [new ImageRun({ type: "png", data: fs.readFileSync(`kachel_${n}.png`), transformation: { width: 190 * MM, height: 277 * MM } })],
}));

const a4 = { width: 11906, height: 16838 };
const mm = v => Math.round(v * 56.7);
const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 21 } } } },
  numbering: { config: [] },
  sections: [
    { properties: { page: { size: a4, margin: { top: mm(18), bottom: mm(18), left: mm(18), right: mm(18) } } }, children: teil1 },
    { properties: { page: { size: a4, margin: { top: mm(10), bottom: mm(10), left: mm(10), right: mm(10), header: 0, footer: 0 } } }, children: teil2 },
  ],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync("Wendel_Bohrschablone_1zu1.docx", b); console.log("geschrieben"); });
