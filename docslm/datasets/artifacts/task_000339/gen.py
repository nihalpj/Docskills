# DocSLM pdf split — via the skill's pdf.py CLI
import json, subprocess, sys

TOOL = "/home/nihal/.zcode/cli/plugins/cache/zcode-plugins-official/document-skills/0.1.4/skills/pdf/scripts/pdf.py"
def run(args):
    return subprocess.run([sys.executable, TOOL] + args,
                          capture_output=True, text=True, timeout=120)

def _json_of(proc):
    s = proc.stdout
    return json.loads(s[s.find("{"):s.rfind("}") + 1]) if "{" in s else {}

proc = run(["pages.split", "task_000339_src.pdf"])
data = _json_of(proc)
assert data.get("status") == "success", proc.stdout[-200:]
import glob
parts = [p for p in glob.glob("*.pdf") if p != "task_000339_src.pdf"]
assert len(parts) >= 2, f"expected split parts, got {parts}"
print(json.dumps({"exit": 0, "artifact": "task_000339_src.pdf", "route": "split"}))
