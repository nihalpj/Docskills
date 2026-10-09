"""DOCX tool-route generators — train the model to operate the plugin's own
repair tooling: add_toc_placeholders.py, fix_footer_fields.py, and the
document.py comment API. English-only.

Generated scripts reference plugin skills at the sandbox mount /skills/; the
verifier maps /skills/ to the real plugin dir at exec time.
"""
from string import Template
from .. import content as C

# Fixture: docx with TOC field + footer PAGE field (docx-js), like the skill
# corpus produces before running its repair utilities.
_FIXTURE_JS = Template("""// fixture: $label
const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, TableOfContents,
        Footer, PageNumber, AlignmentType } = require("docx");

const doc = new Document({ sections: [{
  properties: {}, features: { updateFields: true },
  children: [
    new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { line: 312 },
      children: [new TextRun({ text: "$title", bold: true,
        font: { ascii: "Arial" } })] }),
    new Paragraph({ spacing: { line: 312 },
      children: [new TextRun({ text: "$intro", font: { ascii: "Times New Roman" } })] }),
    new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
    new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { line: 312 },
      children: [new TextRun({ text: "Section A", bold: true,
        font: { ascii: "Arial" } })] }),
    new Paragraph({ spacing: { line: 312 },
      children: [new TextRun({ text: "$body", font: { ascii: "Times New Roman" } })] }),
    new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { line: 312 },
      children: [new TextRun({ text: "Section B", bold: true,
        font: { ascii: "Arial" } })] }),
    new Paragraph({ spacing: { line: 312 },
      children: [new TextRun({ text: "$body2", font: { ascii: "Times New Roman" } })] }),
  ],
  footers: { default: new Footer({ children: [new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { line: 312 },
    children: [new TextRun({ text: "Page ", font: { ascii: "Times New Roman" } }),
               new TextRun({ children: [PageNumber.CURRENT],
                 font: { ascii: "Times New Roman" } })] })] }) },
}]});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync("$base", b);
  console.log(JSON.stringify({ exit: 0, artifact: "$base" })); });
""")

_TOC_FIX = Template('''# DocSLM docx toc_fix — add TOC placeholder entries
import json, subprocess, sys

BASE = "$base"
TOOL = "/skills/docx/scripts/add_toc_placeholders.py"
proc = subprocess.run([sys.executable, TOOL, BASE, "--auto"],
                      capture_output=True, text=True, timeout=60)
out = proc.stdout + proc.stderr
assert proc.returncode == 0, f"add_toc_placeholders failed: {out[-300:]}"
assert "placeholder" in out.lower(), f"no placeholders reported: {out[-300:]}"
print(json.dumps({"exit": 0, "artifact": BASE, "toc_placeholders": True}))
''')

_FOOTER_FIX = Template('''# DocSLM docx footer_fix — normalize bare PAGE fields in footers
import json, subprocess, sys

BASE = "$base"
TOOL = "/skills/docx/scripts/fix_footer_fields.py"
proc = subprocess.run([sys.executable, TOOL, BASE],
                      capture_output=True, text=True, timeout=60)
out = proc.stdout + proc.stderr
assert proc.returncode == 0, f"fix_footer_fields failed: {out[-300:]}"
print(json.dumps({"exit": 0, "artifact": BASE, "footer_fields_fixed": True}))
''')

_COMMENT = Template('''# DocSLM docx comment route — plugin document.py comment API
import json, os, shutil, sys, zipfile
sys.path.insert(0, "/skills/..")
from skills.docx.scripts.document import Document

BASE, UNPACK = "$base", "$unpack"
shutil.rmtree(UNPACK, ignore_errors=True); os.makedirs(UNPACK)
with zipfile.ZipFile(BASE) as z:
    z.extractall(UNPACK)

doc = Document(UNPACK, author="DocSLM", initials="DS")
node = doc["word/document.xml"].get_node(tag="w:p", contains="$anchor")
doc.add_comment(start=node, end=node, text="$comment_text")
doc.save()

OUT = "$artifact"
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(UNPACK):
        for f in files:
            full = os.path.join(root, f)
            z.write(full, os.path.relpath(full, UNPACK))
print(json.dumps({"exit": 0, "artifact": OUT, "commented": True}))
''')


def _fixture(spec, rng, label):
    title = C.report_sections(rng, spec.lang, 2)[0][0]
    return _FIXTURE_JS.substitute(
        label=label, title=title,
        intro="This document describes the project status and next steps.",
        body="The team completed the milestone on schedule.",
        body2="Follow-up actions are tracked in the project board.",
        base=f"{spec.task_id}_doc.docx")


def gen_toc_fix(spec, rng):
    base = f"{spec.task_id}_doc.docx"
    setup = _fixture(spec, rng, "report draft with TOC field")
    code = _TOC_FIX.substitute(base=base)
    request = (f"The document {base} contains a TOC field but no entries. Run the skill's "
               f"add_toc_placeholders tool to insert placeholder entries so the table of "
               f"contents renders, keeping the file at {base}.")
    return {"runner": "python", "code": code, "setup_runner": "node", "setup_code": setup,
            "artifact": base, "expect": {"kind": "docx", "ignore_warnings": ["line-spacing"]}, "request": request, "mutation": None}


def gen_footer_fix(spec, rng):
    base = f"{spec.task_id}_doc.docx"
    setup = _fixture(spec, rng, "report draft with footer PAGE field")
    code = _FOOTER_FIX.substitute(base=base)
    request = (f"The footer PAGE field in {base} uses bare field runs that Word may render "
               f"inconsistently. Run the skill's fix_footer_fields tool on {base} to "
               f"normalize the field structure.")
    return {"runner": "python", "code": code, "setup_runner": "node", "setup_code": setup,
            "artifact": base, "expect": {"kind": "docx", "ignore_warnings": ["line-spacing"]}, "request": request, "mutation": None}


def gen_comment(spec, rng):
    base = f"{spec.task_id}_doc.docx"
    anchor = "This document describes the project status and next steps."
    setup = _fixture(spec, rng, "report draft for review")
    code = _COMMENT.substitute(base=base, unpack=f"{spec.task_id}_unpack",
                               artifact=f"{spec.task_id}_reviewed.docx",
                               anchor="project status", comment_text="Please verify this section before release.")
    request = (f"Review {base}: add a document comment saying 'Please verify this section "
               f"before release.' anchored on the intro paragraph, using the skill's "
               f"document.py comment API. Save the reviewed copy as {spec.task_id}_reviewed.docx.")
    return {"runner": "python", "code": code, "setup_runner": "node", "setup_code": setup,
            "artifact": f"{spec.task_id}_reviewed.docx",
            "expect": {"kind": "docx", "ignore_warnings": ["line-spacing"]}, "request": request, "mutation": None}
