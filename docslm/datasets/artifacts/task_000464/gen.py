# DocSLM pdf extract_image — via the skill's pdf.py CLI
import json, subprocess, sys

TOOL = "/home/nihal/.zcode/cli/plugins/cache/zcode-plugins-official/document-skills/0.1.4/skills/pdf/scripts/pdf.py"
def run(args):
    return subprocess.run([sys.executable, TOOL] + args,
                          capture_output=True, text=True, timeout=120)

def _json_of(proc):
    s = proc.stdout
    return json.loads(s[s.find("{"):s.rfind("}") + 1]) if "{" in s else {}

proc = run(["extract.image", "task_000464_img.pdf"])
data = _json_of(proc)
assert data.get("status") == "success", proc.stdout[-200:]
print(json.dumps({"exit": 0, "artifact": "task_000464_img.pdf", "route": "extract_image"}))
