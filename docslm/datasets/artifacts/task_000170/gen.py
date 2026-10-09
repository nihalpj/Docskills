# DocSLM pdf qa — run the skill's quality gate
import json, subprocess, sys

proc = subprocess.run([sys.executable, "/home/nihal/.zcode/cli/plugins/cache/zcode-plugins-official/document-skills/0.1.4/skills/pdf/scripts/pdf_qa.py", "task_000170_src.pdf"],
                      capture_output=True, text=True, timeout=180)
out = proc.stdout + proc.stderr
assert "PASS" in out or "WARN" in out, f"qa report missing verdict: {out[-300:]}"
print(json.dumps({"exit": 0, "verdict_line": out.strip().splitlines()[-1][:80]}))
