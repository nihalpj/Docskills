# DocSLM xlsx audit — formula audit via the skill CLI
import json, subprocess, sys

proc = subprocess.run([sys.executable, "/home/nihal/.zcode/cli/plugins/cache/zcode-plugins-official/document-skills/0.1.4/skills/xlsx/xlsx.py", "audit", "task_000896_wb.xlsx"],
                      capture_output=True, text=True, timeout=120)
data = json.loads(proc.stdout)
assert "total_formulas" in data, f"unexpected audit output: {proc.stdout[:200]}"
assert data.get("error_count", 0) == 0, f"formula errors: {data}"
print(json.dumps({"exit": 0, "artifact": "task_000896_wb.xlsx", "formulas": data["total_formulas"]}))
