// fixture: report draft with footer PAGE field
const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, TableOfContents,
        Footer, PageNumber, AlignmentType } = require("docx");

const doc = new Document({ sections: [{
  properties: {}, features: { updateFields: true },
  children: [
    new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { line: 312 },
      children: [new TextRun({ text: "Next-Step Plan", bold: true,
        font: { ascii: "Arial" } })] }),
    new Paragraph({ spacing: { line: 312 },
      children: [new TextRun({ text: "This document describes the project status and next steps.", font: { ascii: "Times New Roman" } })] }),
    new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
    new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { line: 312 },
      children: [new TextRun({ text: "Section A", bold: true,
        font: { ascii: "Arial" } })] }),
    new Paragraph({ spacing: { line: 312 },
      children: [new TextRun({ text: "The team completed the milestone on schedule.", font: { ascii: "Times New Roman" } })] }),
    new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { line: 312 },
      children: [new TextRun({ text: "Section B", bold: true,
        font: { ascii: "Arial" } })] }),
    new Paragraph({ spacing: { line: 312 },
      children: [new TextRun({ text: "Follow-up actions are tracked in the project board.", font: { ascii: "Times New Roman" } })] }),
  ],
  footers: { default: new Footer({ children: [new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { line: 312 },
    children: [new TextRun({ text: "Page ", font: { ascii: "Times New Roman" } }),
               new TextRun({ children: [PageNumber.CURRENT],
                 font: { ascii: "Times New Roman" } })] })] }) },
}]});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync("task_000305_doc.docx", b);
  console.log(JSON.stringify({ exit: 0, artifact: "task_000305_doc.docx" })); });
