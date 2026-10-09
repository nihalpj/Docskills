# DocSLM pdf merge — via the skill's pdf.py CLI
import json, subprocess, sys

TOOL = "/home/nihal/.zcode/cli/plugins/cache/zcode-plugins-official/document-skills/0.1.4/skills/pdf/scripts/pdf.py"
def run(args):
    return subprocess.run([sys.executable, TOOL] + args,
                          capture_output=True, text=True, timeout=120)

def _json_of(proc):
    s = proc.stdout
    return json.loads(s[s.find("{"):s.rfind("}") + 1]) if "{" in s else {}

proc = run(["pages.merge", "task_000608_a.pdf", "task_000608_b.pdf", "--output", "task_000608_merged.pdf"])
data = _json_of(proc)
assert data.get("status") == "success", proc.stdout[-200:]
from pypdf import PdfReader
assert len(PdfReader("task_000608_merged.pdf").pages) == 4, "merged page count wrong"
print(json.dumps({"exit": 0, "artifact": "task_000608_merged.pdf", "route": "merge"}))
