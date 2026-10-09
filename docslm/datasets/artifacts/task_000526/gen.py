# DocSLM pdf meta_edit — via the skill's pdf.py CLI
import json, subprocess, sys

TOOL = "/home/nihal/.zcode/cli/plugins/cache/zcode-plugins-official/document-skills/0.1.4/skills/pdf/scripts/pdf.py"
def run(args):
    return subprocess.run([sys.executable, TOOL] + args,
                          capture_output=True, text=True, timeout=120)

def _json_of(proc):
    s = proc.stdout
    return json.loads(s[s.find("{"):s.rfind("}") + 1]) if "{" in s else {}

proc = run(["meta.set", "task_000526_src.pdf", "-o", "task_000526_meta.pdf",
            "-d", json.dumps({"title": "DocSLM Batch Report", "author": "DocSLM"})])
assert proc.returncode == 0, proc.stdout[-200:]
get = run(["meta.get", "task_000526_meta.pdf"])
assert "DocSLM Batch Report" in get.stdout, "title not set"
print(json.dumps({"exit": 0, "artifact": "task_000526_meta.pdf", "route": "meta_edit"}))
