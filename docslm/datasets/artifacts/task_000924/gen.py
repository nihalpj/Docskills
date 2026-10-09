# DocSLM xlsx inspect — workbook structure report via the skill CLI
import json, subprocess, sys

proc = subprocess.run([sys.executable, "/home/nihal/.zcode/cli/plugins/cache/zcode-plugins-official/document-skills/0.1.4/skills/xlsx/xlsx.py", "inspect", "task_000924_wb.xlsx"],
                      capture_output=True, text=True, timeout=120)
data = json.loads(proc.stdout)
sheets = data.get("sheets", [])
assert sheets and sheets[0]["name"] == "Data", f"unexpected inspect output: {proc.stdout[:200]}"
print(json.dumps({"exit": 0, "artifact": "task_000924_wb.xlsx", "sheets": [s["name"] for s in sheets]}))
