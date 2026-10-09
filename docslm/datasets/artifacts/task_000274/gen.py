# DocSLM docx toc_fix — add TOC placeholder entries
import json, subprocess, sys

BASE = "task_000274_doc.docx"
TOOL = "/home/nihal/.zcode/cli/plugins/cache/zcode-plugins-official/document-skills/0.1.4/skills/docx/scripts/add_toc_placeholders.py"
proc = subprocess.run([sys.executable, TOOL, BASE, "--auto"],
                      capture_output=True, text=True, timeout=60)
out = proc.stdout + proc.stderr
assert proc.returncode == 0, f"add_toc_placeholders failed: {out[-300:]}"
assert "placeholder" in out.lower(), f"no placeholders reported: {out[-300:]}"
print(json.dumps({"exit": 0, "artifact": BASE, "toc_placeholders": True}))
