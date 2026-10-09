// DocSLM create route — docx-js (report)
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, WidthType, ShadingType, PageBreak,
} = require("docx");

const PAL = { primary: "5B2C6F", accent: "7D4E9E", light: "EADDF3" };
const BODY_FONT = { ascii: "Times New Roman" };
const HEAD_FONT = { ascii: "Arial" };

function bodyP(text, opts = {}) {
  return new Paragraph({
    spacing: { line: 312 },
    alignment: AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, size: 24, color: "333333", font: BODY_FONT })],
    ...opts,
  });
}
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { line: 312, before: 240, after: 120 },
    children: [new TextRun({ text, bold: true, size: 30, color: PAL.primary, font: HEAD_FONT })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { line: 312, before: 180, after: 90 },
    children: [new TextRun({ text, bold: true, size: 26, color: PAL.accent, font: HEAD_FONT })],
  });
}
function cellP(text, opts = {}) {
  return new Paragraph({
    spacing: { line: 312 },
    children: [new TextRun({ text: String(text), size: 21, font: BODY_FONT, ...opts })],
  });
}
function dataTable(headers, rows) {
  const headerRow = new TableRow({
    tableHeader: true,
    cantSplit: true,
    children: headers.map((h) => new TableCell({
      shading: { type: ShadingType.CLEAR, fill: PAL.primary },
      margins: { top: 100, bottom: 100, left: 150, right: 150 },
      children: [cellP(h, { bold: true, color: "FFFFFF", font: HEAD_FONT })],
    })),
  });
  const bodyRows = rows.map((r, i) => new TableRow({
    cantSplit: true,
    children: r.map((c) => new TableCell({
      shading: { type: ShadingType.CLEAR, fill: i % 2 === 1 ? PAL.light : "FFFFFF" },
      margins: { top: 80, bottom: 80, left: 150, right: 150 },
      children: [cellP(c)],
    })),
  }));
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    margins: { top: 80, bottom: 80, left: 150, right: 150 },
    rows: [headerRow, ...bodyRows],
  });
}
function cover(title, subtitle, metaLines) {
  const metaParas = metaLines.map((m) => new Paragraph({
    spacing: { line: 312 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: m, size: 22, color: PAL.light, font: BODY_FONT })],
  }));
  return [
    new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      margins: { top: 80, bottom: 80, left: 150, right: 150 },
      rows: [new TableRow({
        children: [new TableCell({
          shading: { type: ShadingType.CLEAR, fill: PAL.primary },
          margins: { top: 2400, bottom: 2400, left: 300, right: 300 },
          children: [
            new Paragraph({
              spacing: { line: 312 },
              alignment: AlignmentType.CENTER,
              children: [new TextRun({ text: title, bold: true, size: 52, color: "FFFFFF", font: HEAD_FONT })],
            }),
            new Paragraph({
              spacing: { line: 312 },
              alignment: AlignmentType.CENTER,
              children: [new TextRun({ text: subtitle, size: 26, color: PAL.light, font: BODY_FONT })],
            }),
            ...metaParas,
          ],
        })],
      })],
    }),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

const sections = [];
cover("Quarterly Business Analysis Report", "Project Falcon", ["Bluepeak Systems", "Marketing", "2026-09"]);
sections.push(h1("Summary and Recommendations"));
sections.push(bodyP("Cost pressure and regional competition remain the principal risks to monitor. The business delivered steady growth this quarter, with core KPIs on target. We recommend expanding channel investment and rebalancing resourcing to sustain growth."));
sections.push(h1("Risks and Challenges"));
sections.push(bodyP("We recommend expanding channel investment and rebalancing resourcing to sustain growth. Cross-team efficiency rose and delivery lead times shortened versus last quarter. Cost pressure and regional competition remain the principal risks to monitor."));
sections.push(dataTable(["Item", "Revenue (k)", "YoY"], [["Pulse Dashboard", "971", "14.3%"], ["Sales", "926", "23.2%"], ["Finance", "528", "44.6%"], ["Operations", "443", "36.7%"], ["Pulse Dashboard", "697", "24.1%"]]));
sections.push(h1("Executive Overview"));
sections.push(bodyP("We recommend expanding channel investment and rebalancing resourcing to sustain growth. Cross-team efficiency rose and delivery lead times shortened versus last quarter. The business delivered steady growth this quarter, with core KPIs on target."));
sections.push(h1("Performance Analysis"));
sections.push(bodyP("Revenue concentration in the main product line increased and retention improved. Cost pressure and regional competition remain the principal risks to monitor. The business delivered steady growth this quarter, with core KPIs on target."));

const doc = new Document({
  sections: [{
    properties: { page: { margin: { top: 1440, bottom: 1440, left: 1800, right: 1800 } } },
    children: sections,
  }],
});
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("task_000450_doc.docx", buf);
  console.log(JSON.stringify({ exit: 0, artifact: "task_000450_doc.docx", bytes: buf.length }));
}).catch((e) => { console.error(e.message); process.exit(1); });
