# DocSLM docx comment route — plugin document.py comment API
import json, os, shutil, sys, zipfile
sys.path.insert(0, "/home/nihal/.zcode/cli/plugins/cache/zcode-plugins-official/document-skills/0.1.4/skills/..")
from skills.docx.scripts.document import Document

BASE, UNPACK = "task_000276_doc.docx", "task_000276_unpack"
shutil.rmtree(UNPACK, ignore_errors=True); os.makedirs(UNPACK)
with zipfile.ZipFile(BASE) as z:
    z.extractall(UNPACK)

doc = Document(UNPACK, author="DocSLM", initials="DS")
node = doc["word/document.xml"].get_node(tag="w:p", contains="project status")
doc.add_comment(start=node, end=node, text="Please verify this section before release.")
doc.save()

OUT = "task_000276_reviewed.docx"
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(UNPACK):
        for f in files:
            full = os.path.join(root, f)
            z.write(full, os.path.relpath(full, UNPACK))
print(json.dumps({"exit": 0, "artifact": OUT, "commented": True}))
