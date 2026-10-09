# DocSLM pdf form_fill — via the skill's pdf.py CLI
import json, subprocess, sys

TOOL = "/home/nihal/.zcode/cli/plugins/cache/zcode-plugins-official/document-skills/0.1.4/skills/pdf/scripts/pdf.py"
def run(args):
    return subprocess.run([sys.executable, TOOL] + args,
                          capture_output=True, text=True, timeout=120)

def _json_of(proc):
    s = proc.stdout
    return json.loads(s[s.find("{"):s.rfind("}") + 1]) if "{" in s else {}

proc = run(["form.fill", "task_000915_form.pdf", "-o", "task_000915_filled.pdf",
            "-d", json.dumps({"fullname": "Jane Doe", "email": "jane@example.com"})])
_json_of(proc)
assert proc.returncode == 0, proc.stdout[-200:]
info = run(["form.info", "task_000915_filled.pdf"])
assert "Jane Doe" in info.stdout, "filled value not visible in form.info"
print(json.dumps({"exit": 0, "artifact": "task_000915_filled.pdf", "route": "form_fill"}))
