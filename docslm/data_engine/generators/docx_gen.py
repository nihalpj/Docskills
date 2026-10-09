"""DOCX generators — English-only. create (docx-js via Node), edit/format/read
(python-docx).

Emitted code follows the plugin rules the corpus packs carry: spacing line 312,
ShadingType.CLEAR, table margins, tableHeader/cantSplit, validated-recipe-style
cover table.
"""
from string import Template
import json as _j
from .. import content as C

FONT_BODY = '{ ascii: "Times New Roman" }'
FONT_HEAD = '{ ascii: "Arial" }'

_CREATE_JS = Template("""// DocSLM create route — docx-js ($scene)
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, WidthType, ShadingType, PageBreak,
} = require("docx");

const PAL = { primary: "$primary", accent: "$accent", light: "$light" };
const BODY_FONT = $font_body;
const HEAD_FONT = $font_head;

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
$cover_block
$sections_block

const doc = new Document({
  sections: [{
    properties: { page: { margin: { top: 1440, bottom: 1440, left: 1800, right: 1800 } } },
    children: sections,
  }],
});
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("$artifact", buf);
  console.log(JSON.stringify({ exit: 0, artifact: "$artifact", bytes: buf.length }));
}).catch((e) => { console.error(e.message); process.exit(1); });
""")


def json_s(s: str) -> str:
    return _j.dumps(s, ensure_ascii=False)


def hdr_kpi():
    return _j.dumps(["Item", "Revenue (k)", "YoY"], ensure_ascii=False)


def kpi_js(rows):
    return _j.dumps([[str(a), str(b), f"{int(c * 1000) / 10}%"]
                     for a, b, c in rows], ensure_ascii=False)


def _sections_report(spec, rng, sections):
    kpi = C.kpi_rows(rng, spec.lang, 5)
    blocks = []
    titles, bodies = zip(*sections)
    blocks.append(f"sections.push(h1({json_s(titles[0])}));")
    blocks.append(f"sections.push(bodyP({json_s(bodies[0])}));")
    blocks.append(f"sections.push(h1({json_s(titles[1])}));")
    blocks.append(f"sections.push(bodyP({json_s(bodies[1])}));")
    blocks.append(f"sections.push(dataTable({hdr_kpi()}, {kpi_js(kpi)}));")
    for t, b in sections[2:]:
        blocks.append(f"sections.push(h1({json_s(t)}));")
        blocks.append(f"sections.push(bodyP({json_s(b)}));")
    return "\n".join(blocks)


def _sections_contract(spec, rng, fields):
    blocks = ['sections.push(h1("Software Development Services Agreement"));',
              f"sections.push(bodyP({json_s('Party A: ' + fields['party_a'])}));",
              f"sections.push(bodyP({json_s('Party B: ' + fields['party_b'])}));"]
    recital = (f"This Agreement (amount: {fields['amount']}) covers the "
               f"{fields['project']} engagement and is entered into by the parties "
               f"as of the date of last signature.")
    blocks.append(f"sections.push(bodyP({json_s(recital)}));")
    for i, cl in enumerate(fields["clauses"], 1):
        blocks.append(f"sections.push(h2({json_s(f'Clause {i}. {cl}')}));")
        blocks.append("sections.push(bodyP(\"The parties agree to the rights and obligations "
                      "under this Clause as detailed herein and in the attachments hereto.\"));")
    blocks.append('sections.push(h2("Miscellaneous"));')
    blocks.append('sections.push(bodyP("This Agreement is executed in two counterparts, '
                  'effective upon signature by both parties."));')
    return "\n".join(blocks)


def _sections_resume(spec, rng):
    name, tel, mail = C.person(rng, spec.lang), "555-0100", "candidate@example.com"
    educ = "2018-2022  B.S. Computer Science, State University"
    jobs = [(y, C.company(rng, spec.lang), C.title_(rng, spec.lang))
            for y in ("2022", "2024")]
    blocks = [f"sections.push(h1({json_s(name + '  —  Resume')}));",
              f"sections.push(bodyP({json_s(f'Tel: {tel}  Email: {mail}')}));",
              'sections.push(h2("Education"));',
              f"sections.push(bodyP({json_s(educ)}));",
              'sections.push(h2("Experience"));']
    for y, co, ti in jobs:
        line = f"{y}-present  {co}  {ti}: owned core module design and delivery; " \
               f"drove cross-team launches on schedule."
        blocks.append(f"sections.push(bodyP({json_s(line)}));")
    blocks += ['sections.push(h2("Skills"));',
               'sections.push(bodyP("Proficient in Python / JavaScript with data processing '
               'and document automation experience."));']
    return "\n".join(blocks)


def _sections_exam(spec, rng, subject, items):
    title = f"2026 {subject} Final Exam"
    blocks = [f"sections.push(h1({json_s(title)}));"]
    for i, (kind, q, opts) in enumerate(items, 1):
        head = f"{i}. [{kind}] {q}"
        blocks.append(f"sections.push(h2({json_s(head)}));")
        labels = ["A", "B", "C", "D"][: len(opts)]
        for lab, opt in zip(labels, opts):
            blocks.append(f"sections.push(bodyP({json_s(f'{lab}. {opt}')}));")
    return "\n".join(blocks)


SCENE_TITLES = {
    "report": "Quarterly Business Analysis Report",
    "academic": "Research Paper Draft",
    "official-doc": "Work Notice: Key Project Advancement",
    "copywriting": "Product Launch Copy Script",
}


def gen_create(spec, rng):
    scene = spec.scene
    primary, accent, light = C.palette(rng)
    artifact = f"{spec.task_id}_doc.docx"
    title = SCENE_TITLES.get(scene, SCENE_TITLES["report"])
    org, dept, date = C.company(rng, spec.lang), C.department(rng, spec.lang), "2026-09"
    cover_block = (f'cover({json_s(title)}, {json_s(C.project(rng, spec.lang))}, '
                   f'[{json_s(org)}, {json_s(dept)}, {json_s(date)}]);')

    if scene == "contract":
        fields = C.contract_fields(rng, spec.lang)
        sections_block = _sections_contract(spec, rng, fields)
    elif scene == "resume":
        sections_block = _sections_resume(spec, rng)
    elif scene == "exam":
        subject, items = C.exam_items(rng, spec.lang, 4)
        sections_block = _sections_exam(spec, rng, subject, items)
    else:
        secs = C.report_sections(rng, spec.lang, 3 + min(spec.difficulty, 2))
        sections_block = _sections_report(spec, rng, secs)

    code = _CREATE_JS.substitute(
        scene=scene, primary=primary, accent=accent, light=light,
        font_body=FONT_BODY, font_head=FONT_HEAD,
        artifact=artifact, cover_block=cover_block, sections_block=sections_block)

    table_req = "a data table" if scene != "exam" else "exam layout"
    request = (f"Create '{title}' with docx-js: professional cover (primary #{primary}), "
               f"1.3x body line spacing, {table_req}, org {org}, dated {date}. "
               f"Output file {artifact}.")
    return {"runner": "node", "code": code, "artifact": artifact,
            "expect": {"kind": "docx"}, "request": request, "mutation": None}
