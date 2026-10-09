# DocSLM pdf palette — generate a document palette via the skill CLI
import json, subprocess, sys

proc = subprocess.run([sys.executable, "/home/nihal/.zcode/cli/plugins/cache/zcode-plugins-official/document-skills/0.1.4/skills/pdf/scripts/pdf.py", "palette.generate",
                       "--intent", "business"],
                      capture_output=True, text=True, timeout=120)
out = proc.stdout + proc.stderr
assert proc.returncode == 0, f"palette.generate failed: {out[-300:]}"
assert "Intent" in out, f"palette header missing: {out[:200]}"
with open("palette_out.txt", "w", encoding="utf-8") as f:
    f.write(out)
print(json.dumps({"exit": 0, "artifact": "palette_out.txt", "palette": True}))
