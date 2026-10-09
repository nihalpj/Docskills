"""PDF generators — report (reportlab platypus) and process (pypdf merge).
English-only (Helvetica base fonts)."""
from string import Template
import json as _json
from .. import content as C

_REPORT = Template("""# DocSLM pdf report — reportlab ($scene)
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

PRIMARY = HexColor(0x$primary)
FONT = "Helvetica"

styles = {
    "title": ParagraphStyle("title", fontName=FONT, fontSize=20, leading=26,
                            textColor=PRIMARY, spaceAfter=10),
    "h1": ParagraphStyle("h1", fontName=FONT, fontSize=15, leading=20,
                         textColor=PRIMARY, spaceBefore=14, spaceAfter=6),
    "body": ParagraphStyle("body", fontName=FONT, fontSize=10.5, leading=15, spaceAfter=6),
    "meta": ParagraphStyle("meta", fontName=FONT, fontSize=9.5, leading=13,
                           textColor=HexColor(0x666666)),
}

doc = SimpleDocTemplate("$artifact", pagesize=A4,
                        leftMargin=20 * mm, rightMargin=20 * mm,
                        topMargin=18 * mm, bottomMargin=18 * mm)
story = [Paragraph("$title", styles["title"]),
         Paragraph("$meta", styles["meta"]),
         Spacer(1, 6), PageBreak()]
$sections_block
doc.build(story)
print(json.dumps({"exit": 0, "artifact": "$artifact"}))
""")

_PROCESS_SETUP = Template("""# setup: source pdfs to merge
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from reportlab.lib.styles import ParagraphStyle

style = ParagraphStyle("b", fontName="Helvetica", fontSize=11, leading=16)
for i, name in enumerate($names, 1):
    doc = SimpleDocTemplate(name, pagesize=A4)
    doc.build([Paragraph("%s — part %d" % ($title, i), style), PageBreak(),
               Paragraph("Content page.", style)])
print("ok")
""")

_PROCESS = Template("""# DocSLM pdf process — merge with pypdf
import json
from pypdf import PdfReader, PdfWriter

writer = PdfWriter()
for name in $names:
    reader = PdfReader(name)
    for page in reader.pages:
        writer.add_page(page)
with open("$artifact", "wb") as f:
    writer.write(f)
print(json.dumps({"exit": 0, "artifact": "$artifact",
                  "pages": len(PdfReader("$artifact").pages)}))
""")


def gen_report(spec, rng):
    primary, accent, light = C.palette(rng)
    artifact = f"{spec.task_id}_doc.pdf"
    title = ("Monthly Business Analysis Report" if spec.scene == "business-report"
             else "Certificate of Achievement")
    org, date = C.company(rng, spec.lang), "2026-09"
    secs = C.report_sections(rng, spec.lang, 3 + min(spec.difficulty, 2))
    blocks = []
    kpi = C.kpi_rows(rng, spec.lang, 4)
    t, b = secs[0]
    blocks.append(f'story.append(Paragraph({_json.dumps(t, ensure_ascii=False)}, styles["h1"]))')
    blocks.append(f'story.append(Paragraph({_json.dumps(b, ensure_ascii=False)}, styles["body"]))')
    hdr = ["Item", "Revenue (k)", "YoY"]
    data = [hdr] + [[str(c) for c in row] for row in kpi]
    blocks.append(
        'tbl = Table(' + _json.dumps(data, ensure_ascii=False) + ', repeatRows=1)\n'
        'tbl.setStyle(TableStyle([\n'
        '    ("GRID", (0, 0), (-1, -1), 0.5, HexColor(0xCCCCCC)),\n'
        '    ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),\n'
        '    ("TEXTCOLOR", (0, 0), (-1, 0), HexColor(0xFFFFFF)),\n'
        '    ("FONTNAME", (0, 0), (-1, -1), FONT),\n'
        '    ("FONTSIZE", (0, 0), (-1, -1), 9),\n'
        ']))\n'
        'story.append(tbl)')
    for t, b in secs[1:]:
        blocks.append(f'story.append(Paragraph({_json.dumps(t, ensure_ascii=False)}, styles["h1"]))')
        reps = spec.difficulty if spec.difficulty >= 2 else 1
        sents = [s.strip() + "." for s in b.split(".") if s.strip()]
        for k in range(reps):
            para = ". ".join(sents[k % len(sents):] + sents[:k % len(sents)])
            blocks.append(f'story.append(Paragraph({_json.dumps(para, ensure_ascii=False)}, styles["body"]))')
    code = _REPORT.substitute(scene=spec.scene, primary=primary,
                              artifact=artifact, title=title,
                              meta=f"{org} · {date}", sections_block="\n".join(blocks))
    request = (f"Generate PDF '{title}' with reportlab (A4, data table, primary #{primary}), "
               f"save as {artifact}.")
    return {"runner": "python", "code": code, "artifact": artifact,
            "expect": {"kind": "pdf", "min_pages": 2},
            "request": request, "mutation": None}


def gen_process(spec, rng):
    artifact = f"{spec.task_id}_merged.pdf"
    names = [f"{spec.task_id}_p{i}.pdf" for i in range(1, 4)]
    title = _json.dumps(C.project(rng, spec.lang), ensure_ascii=False)
    setup = _PROCESS_SETUP.substitute(names=_json.dumps(names), title=title)
    code = _PROCESS.substitute(names=_json.dumps(names), artifact=artifact)
    request = (f"Merge {names[0]}, {names[1]}, {names[2]} in order into {artifact} "
               f"and verify the page count.")
    return {"runner": "python", "code": code, "setup_runner": "python", "setup_code": setup,
            "artifact": artifact, "expect": {"kind": "pdf", "min_pages": 6},
            "request": request, "mutation": None}
