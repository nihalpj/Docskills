# DocSLM xlsx scan — issue scan via the skill CLI
import json, subprocess, sys

proc = subprocess.run([sys.executable, "/home/nihal/.zcode/cli/plugins/cache/zcode-plugins-official/document-skills/0.1.4/skills/xlsx/xlsx.py", "scan", "task_000805_wb.xlsx"],
                      capture_output=True, text=True, timeout=120)
data = json.loads(proc.stdout)
assert "total_findings" in data, f"unexpected scan output: {proc.stdout[:200]}"
assert data["total_findings"] == 0, f"findings: {data}"
print(json.dumps({"exit": 0, "artifact": "task_000805_wb.xlsx", "findings": 0}))
