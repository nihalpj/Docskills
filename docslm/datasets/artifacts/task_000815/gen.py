# DocSLM docx footer_fix — normalize bare PAGE fields in footers
import json, subprocess, sys

BASE = "task_000815_doc.docx"
TOOL = "/home/nihal/.zcode/cli/plugins/cache/zcode-plugins-official/document-skills/0.1.4/skills/docx/scripts/fix_footer_fields.py"
proc = subprocess.run([sys.executable, TOOL, BASE],
                      capture_output=True, text=True, timeout=60)
out = proc.stdout + proc.stderr
assert proc.returncode == 0, f"fix_footer_fields failed: {out[-300:]}"
print(json.dumps({"exit": 0, "artifact": BASE, "footer_fields_fixed": True}))
