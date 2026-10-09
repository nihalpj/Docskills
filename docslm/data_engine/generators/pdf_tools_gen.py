"""PDF tool-route generators — the model learns to operate pdf.py's own
subcommands (pages ops, extraction, forms, metadata, fonts, TOC, palettes)
and the pdf_qa.py quality gate. English-only.

Fixtures are built in setup (reportlab); the turn-1 script drives the plugin
CLI via subprocess and asserts on its JSON output. Scripts reference the
sandbox mount /skills/ (mapped to the real plugin dir by the verifier).
"""
from string import Template
from .. import content as C

_REPORT_SETUP = Template("""# setup: source report pdf ($pages pages)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import grey
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, PageBreak

style = ParagraphStyle("b", fontName="Helvetica", fontSize=11, leading=15)
doc = SimpleDocTemplate("$name", pagesize=A4)
grid = TableStyle([("GRID", (0, 0), (-1, -1), 0.5, grey)])
story = [Paragraph("$title", style), Paragraph("Revenue by item:", style),
         Table([["Item", "Revenue"], ["Orbit CRM", "120"], ["Pulse Dashboard", "240"]],
               style=grid),
         PageBreak(), Paragraph("Second page content for $title.", style)]
doc.build(story)
print("ok")
""")

_FORM_SETUP = Template("""# setup: AcroForm feedback pdf
from reportlab.pdfgen import canvas as cvs

c = cvs.Canvas("$name", pagesize=(612, 792))
c.setFont("Helvetica", 12)
c.drawString(72, 750, "$form_title")
c.acroForm.textfield(name="fullname", x=72, y=700, width=300, height=20,
                     borderColor=None, fillColor=None, relative=False)
c.acroForm.textfield(name="email", x=72, y=650, width=300, height=20,
                     borderColor=None, fillColor=None, relative=False)
c.save()
print("ok")
""")

_IMAGE_SETUP = Template("""# setup: pdf with an embedded image
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Image

img = PILImage.new("RGB", (200, 120), (31, 78, 121))
img.save("$png")
doc = SimpleDocTemplate("$name", pagesize=A4)
doc.build([Image("$png", width=80 * mm, height=48 * mm)])
print("ok")
""")

_PDF = '"/skills/pdf/scripts/pdf.py"'
_QA = '"/skills/pdf/scripts/pdf_qa.py"'

_WRAP = Template('''# DocSLM pdf $route — via the skill's pdf.py CLI
import json, subprocess, sys

TOOL = $pdf
def run(args):
    return subprocess.run([sys.executable, TOOL] + args,
                          capture_output=True, text=True, timeout=120)

def _json_of(proc):
    s = proc.stdout
    return json.loads(s[s.find("{"):s.rfind("}") + 1]) if "{" in s else {}

$calls
print(json.dumps({"exit": 0, "artifact": "$artifact", "route": "$route"}))
''')

_QA_WRAP = Template('''# DocSLM pdf qa — run the skill's quality gate
import json, subprocess, sys

proc = subprocess.run([sys.executable, $qa, "$input"],
                      capture_output=True, text=True, timeout=180)
out = proc.stdout + proc.stderr
assert "PASS" in out or "WARN" in out, f"qa report missing verdict: {out[-300:]}"
print(json.dumps({"exit": 0, "verdict_line": out.strip().splitlines()[-1][:80]}))
''')

_PAL = Template('''# DocSLM pdf palette — generate a document palette via the skill CLI
import json, subprocess, sys

proc = subprocess.run([sys.executable, $pdf, "palette.generate",
                       "--intent", "business"],
                      capture_output=True, text=True, timeout=120)
out = proc.stdout + proc.stderr
assert proc.returncode == 0, f"palette.generate failed: {out[-300:]}"
assert "Intent" in out, f"palette header missing: {out[:200]}"
with open("$artifact", "w", encoding="utf-8") as f:
    f.write(out)
print(json.dumps({"exit": 0, "artifact": "$artifact", "palette": True}))
''')


def _wrap(route, calls, artifact, pdf=_PDF):
    return _WRAP.substitute(route=route, pdf=pdf, calls=calls, artifact=artifact)


def _setup_report(spec, name, pages=2):
    title = C.report_sections(rng=spec_rng(spec), lang=spec.lang, n=1)[0][0]
    return _REPORT_SETUP.substitute(name=name, pages=pages, title=title)


def spec_rng(spec):
    import random
    return random.Random(spec.seed)


def gen_merge(spec, rng):
    a, b, out = f"{spec.task_id}_a.pdf", f"{spec.task_id}_b.pdf", f"{spec.task_id}_merged.pdf"
    setup = (_setup_report(spec, a) + "\n" +
             _REPORT_SETUP.substitute(name=b, pages=2, title="Appendix Document"))
    calls = (
        f'proc = run(["pages.merge", "{a}", "{b}", "--output", "{out}"])\n'
        f'data = _json_of(proc)\n'
        f'assert data.get("status") == "success", proc.stdout[-200:]\n'
        f'from pypdf import PdfReader\n'
        f'assert len(PdfReader("{out}").pages) == 4, "merged page count wrong"')
    code = _wrap("merge", calls, out)
    request = (f"Merge {a} and {b} into {out} using the pdf skill's pages.merge command, "
               f"then confirm the merged file has 4 pages.")
    return {"runner": "python", "code": code, "setup_runner": "python", "setup_code": setup,
            "artifact": out, "expect": {"kind": "tool", "json_status": False,
                                        "artifact": out}, "request": request, "mutation": None}


def gen_split(spec, rng):
    src = f"{spec.task_id}_src.pdf"
    setup = _setup_report(spec, src)
    calls = (
        f'proc = run(["pages.split", "{src}"])\n'
        f'data = _json_of(proc)\n'
        f'assert data.get("status") == "success", proc.stdout[-200:]\n'
        f'import glob\n'
        f'parts = [p for p in glob.glob("*.pdf") if p != "{src}"]\n'
        f'assert len(parts) >= 2, f"expected split parts, got {{parts}}"')
    code = _wrap("split", calls, src)
    request = (f"Split {src} into single-page PDFs with the pdf skill's pages.split "
               f"command and verify at least two part files were produced.")
    return {"runner": "python", "code": code, "setup_runner": "python", "setup_code": setup,
            "artifact": src, "expect": {"kind": "tool", "json_status": False,
                                        "artifact": src}, "request": request, "mutation": None}


def gen_rotate(spec, rng):
    src, out = f"{spec.task_id}_src.pdf", f"{spec.task_id}_rot.pdf"
    setup = _setup_report(spec, src)
    calls = (
        f'proc = run(["pages.rotate", "{src}", "90", "--output", "{out}"])\n'
        f'data = _json_of(proc)\n'
        f'assert data.get("status") == "success", proc.stdout[-200:]')
    code = _wrap("rotate", calls, out)
    request = (f"Rotate all pages of {src} by 90 degrees using the pdf skill's "
               f"pages.rotate command, writing {out}.")
    return {"runner": "python", "code": code, "setup_runner": "python", "setup_code": setup,
            "artifact": out, "expect": {"kind": "tool", "json_status": False,
                                        "artifact": out}, "request": request, "mutation": None}


def gen_crop(spec, rng):
    src, out = f"{spec.task_id}_src.pdf", f"{spec.task_id}_crop.pdf"
    setup = _setup_report(spec, src)
    calls = (
        f'proc = run(["pages.crop", "{src}", "20,20,575,820", "-o", "{out}"])\n'
        f'data = _json_of(proc)\n'
        f'assert data.get("status") == "success", proc.stdout[-200:]')
    code = _wrap("crop", calls, out)
    request = (f"Crop the page box of {src} to 20,20,575,820 (pt) with the pdf skill's "
               f"pages.crop command, writing {out}.")
    return {"runner": "python", "code": code, "setup_runner": "python", "setup_code": setup,
            "artifact": out, "expect": {"kind": "tool", "json_status": False,
                                        "artifact": out}, "request": request, "mutation": None}


def gen_extract_text(spec, rng):
    src = f"{spec.task_id}_src.pdf"
    setup = _setup_report(spec, src)
    title = C.report_sections(rng, spec.lang, 1)[0][0]
    calls = (
        f'proc = run(["extract.text", "{src}"])\n'
        f'data = _json_of(proc)\n'
        f'assert data.get("status") == "success", proc.stdout[-200:]\n'
        f'text = json.dumps(data)\n'
        f'assert "{title.split()[0]}" in text, "extracted text missing title"')
    code = _wrap("extract_text", calls, src)
    request = (f"Extract the text layer of {src} with the pdf skill's extract.text command "
               f"and confirm the document title appears in the output.")
    return {"runner": "python", "code": code, "setup_runner": "python", "setup_code": setup,
            "artifact": src, "expect": {"kind": "tool", "json_status": False,
                                        "artifact": src}, "request": request, "mutation": None}


def gen_extract_table(spec, rng):
    src = f"{spec.task_id}_src.pdf"
    setup = _setup_report(spec, src)
    calls = (
        f'proc = run(["extract.table", "{src}"])\n'
        f'data = _json_of(proc)\n'
        f'assert data.get("status") == "success", proc.stdout[-200:]\n'
        f'assert data["data"]["total_tables"] >= 1, "no tables detected"\n'
        f'assert "Orbit CRM" in json.dumps(data), "table row not extracted"')
    code = _wrap("extract_table", calls, src)
    request = (f"Extract tables from {src} using the pdf skill's extract.table command "
               f"and confirm the 'Orbit CRM' revenue row came through.")
    return {"runner": "python", "code": code, "setup_runner": "python", "setup_code": setup,
            "artifact": src, "expect": {"kind": "tool", "json_status": False,
                                        "artifact": src}, "request": request, "mutation": None}


def gen_extract_image(spec, rng):
    src, png = f"{spec.task_id}_img.pdf", f"{spec.task_id}_chart.png"
    setup = _IMAGE_SETUP.substitute(name=src, png=png)
    calls = (
        f'proc = run(["extract.image", "{src}"])\n'
        f'data = _json_of(proc)\n'
        f'assert data.get("status") == "success", proc.stdout[-200:]')
    code = _wrap("extract_image", calls, src)
    request = (f"Extract the embedded image from {src} with the pdf skill's extract.image "
               f"command and report the result.")
    return {"runner": "python", "code": code, "setup_runner": "python", "setup_code": setup,
            "artifact": src, "expect": {"kind": "tool", "json_status": False,
                                        "artifact": src}, "request": request, "mutation": None}


def gen_form_fill(spec, rng):
    src, out = f"{spec.task_id}_form.pdf", f"{spec.task_id}_filled.pdf"
    setup = _FORM_SETUP.substitute(name=src, form_title=C.company(rng, spec.lang) + " Feedback Form")
    calls = (
        f'proc = run(["form.fill", "{src}", "-o", "{out}",\n'
        f'            "-d", json.dumps({{"fullname": "Jane Doe", "email": "jane@example.com"}})])\n'
        f'_json_of(proc)\n'
        f'assert proc.returncode == 0, proc.stdout[-200:]\n'
        f'info = run(["form.info", "{out}"])\n'
        f'assert "Jane Doe" in info.stdout, "filled value not visible in form.info"')
    code = _wrap("form_fill", calls, out)
    request = (f"Fill the AcroForm fields of {src} (fullname 'Jane Doe', email "
               f"'jane@example.com') using the pdf skill's form.fill command, save as "
               f"{out}, and verify the values via form.info.")
    return {"runner": "python", "code": code, "setup_runner": "python", "setup_code": setup,
            "artifact": out, "expect": {"kind": "tool", "json_status": False,
                                        "artifact": out}, "request": request, "mutation": None}


def gen_meta_edit(spec, rng):
    src, out = f"{spec.task_id}_src.pdf", f"{spec.task_id}_meta.pdf"
    setup = _setup_report(spec, src)
    title = "DocSLM Batch Report"
    calls = (
        f'proc = run(["meta.set", "{src}", "-o", "{out}",\n'
        f'            "-d", json.dumps({{"title": "{title}", "author": "DocSLM"}})])\n'
        f'assert proc.returncode == 0, proc.stdout[-200:]\n'
        f'get = run(["meta.get", "{out}"])\n'
        f'assert "{title}" in get.stdout, "title not set"')
    code = _wrap("meta_edit", calls, out)
    request = (f"Set the metadata of {src} (title '{title}', author 'DocSLM') with the pdf "
               f"skill's meta.set command into {out}, and confirm via meta.get.")
    return {"runner": "python", "code": code, "setup_runner": "python", "setup_code": setup,
            "artifact": out, "expect": {"kind": "tool", "json_status": False,
                                        "artifact": out}, "request": request, "mutation": None}


def gen_font_check(spec, rng):
    src = f"{spec.task_id}_src.pdf"
    setup = _setup_report(spec, src)
    calls = (
        f'proc = run(["font.check", "{src}"])\n'
        f'data = _json_of(proc)\n'
        f'assert data.get("status") in ("ok", "success"), proc.stdout[-200:]')
    code = _wrap("font_check", calls, src)
    request = (f"Run the pdf skill's font.check on {src} and report whether any font "
               f"embedding issues are found.")
    return {"runner": "python", "code": code, "setup_runner": "python", "setup_code": setup,
            "artifact": src, "expect": {"kind": "tool", "json_status": False,
                                        "artifact": src}, "request": request, "mutation": None}


def gen_toc_check(spec, rng):
    src = f"{spec.task_id}_src.pdf"
    setup = _setup_report(spec, src)
    calls = (
        f'proc = run(["toc.check", "{src}"])\n'
        f'data = _json_of(proc)\n'
        f'assert data.get("pass") is True or data.get("status") == "success", proc.stdout[-200:]')
    code = _wrap("toc_check", calls, src)
    request = (f"Validate the table-of-contents structure of {src} with the pdf skill's "
               f"toc.check command.")
    return {"runner": "python", "code": code, "setup_runner": "python", "setup_code": setup,
            "artifact": src, "expect": {"kind": "tool", "json_status": False,
                                        "artifact": src}, "request": request, "mutation": None}


def gen_palette(spec, rng):
    code = _PAL.substitute(pdf=_PDF, artifact="palette_out.txt")
    request = ("Generate a business-intent color palette with the pdf skill's "
               "palette.generate command and save the generated palette to palette_out.txt.")
    return {"runner": "python", "code": code, "artifact": "palette_out.txt",
            "expect": {"kind": "tool", "json_status": False, "artifact": "palette_out.txt"},
            "request": request, "mutation": None}


def gen_qa(spec, rng):
    src = f"{spec.task_id}_src.pdf"
    setup = _setup_report(spec, src)
    code = _QA_WRAP.substitute(qa=_QA, input=src)
    request = (f"Run the pdf skill's quality gate (pdf_qa) over {src} and report the "
               f"verdict line.")
    return {"runner": "python", "code": code, "setup_runner": "python", "setup_code": setup,
            "artifact": src, "expect": {"kind": "tool", "json_status": False,
                                        "artifact": src}, "request": request, "mutation": None}
