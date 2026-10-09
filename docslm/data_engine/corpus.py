"""Context pack assembly — grounds each task's system prompt in the REAL
document-skills plugin corpus (Data Engine §4 step 1: "teacher sees what
DocSLM will see"). Excerpts are sliced from the actual SKILL.md / reference
files at build time, so packs stay in sync with the pinned plugin rev.
"""
from pathlib import Path
from . import PLUGIN_DIR, PLUGIN_REV, ROLE_PREAMBLE

def _read(rel: str) -> str:
    return (PLUGIN_DIR / rel).read_text(encoding="utf-8", errors="replace")

def _slice(text: str, start_marker: str, max_chars: int) -> str:
    i = text.find(start_marker)
    if i == -1:
        return text[:max_chars]
    return text[i:i + max_chars]

# Caches
_cache: dict[str, str] = {}

def _cached(rel: str) -> str:
    if rel not in _cache:
        _cache[rel] = _read(rel)
    return _cache[rel]

def _docx_router_rules() -> str:
    sk = _cached("docx/SKILL.md")
    task_router = _slice(sk, "### Task Router", 1200)
    fmt = _slice(sk, "## Formatting Standards", 900)
    units = _slice(sk, "## Unit Quick Reference", 420)
    common = _cached("docx/references/common-rules.md")
    compat = _slice(common, "### Features to AVOID", 800)
    return "\n".join([task_router, fmt, units,
                      "\n### Compatibility rules (mandatory)\n" + compat])

def _xlsx_rules() -> str:
    sk = _cached("xlsx/SKILL.md")
    preflight = _slice(sk, "## Pre-Flight: Intent Gate", 700)
    return preflight + (
        "\n\n### openpyxl rules\n"
        "- Header row: PatternFill solid + bold white font + freeze_panes='A2'; column widths set.\n"
        "- Numbers carry explicit number_format; formulas use absolute references where stable.\n"
        "- Charts (BarChart/LineChart/PieChart) must reference existing ranges; add charts to a dashboard sheet.\n"
        "- Never hardcode computed values that a formula should compute.\n"
    )

def _pptx_rules() -> str:
    sk = _cached("pptx/SKILL.md")
    return _slice(sk, "# ", 700) + (
        "\n\n### pptxgenjs rules\n"
        "- defineLayout 13.33x7.5 (16:9) and set pptx.layout before adding slides.\n"
        "- Title bar on every slide; body text boxes keep 0.5in margins; font sizes 12-40pt.\n"
        "- Tables: explicit colW summing to box width; header row filled with theme color.\n"
        "- Charts via pptx.ChartType with x/y/w/h set; colors from one theme palette.\n"
    )

def _pdf_rules() -> str:
    sk = _cached("pdf/SKILL.md")
    triage = _slice(sk, "## Triage", 600)
    return triage + (
        "\n\n### reportlab rules\n"
        "- SimpleDocTemplate A4; styles: Title 20pt bold, H1 15pt, H2 12.5pt, Body 10.5pt leading 15.\n"
        "- Fonts: use built-in Helvetica (and Helvetica-Bold for headings) via the style fontName.\n"
        "- Tables: TableStyle with GRID 0.5 + header background HexColor; repeatRows=1.\n"
        "- Verify afterwards with pypdf: page count and extractable text.\n"
    )

def _scene_excerpt(skill: str, route: str, scene: str) -> str:
    path = {
        ("docx", "report"): "docx/scenes/report.md",
        ("docx", "contract"): "docx/scenes/contract.md",
        ("docx", "resume"): "docx/scenes/resume.md",
        ("docx", "exam"): "docx/scenes/exam.md",
        ("docx", "academic"): "docx/scenes/academic.md",
        ("docx", "official-doc"): "docx/scenes/official-doc.md",
        ("docx", "copywriting"): "docx/scenes/copywriting.md",
    }.get((skill, scene))
    if not path:
        return ""
    head = _cached(path)[:1100]
    return f"\n### Scene spec excerpt ({scene})\n{head}\n"

def _route_excerpt(skill: str, route: str) -> str:
    m = {
        ("docx", "create"): ("docx/routes/create.md", 900),
        ("docx", "edit"): ("docx/routes/edit.md", 700),
        ("docx", "format"): ("docx/routes/format.md", 700),
        ("docx", "read"): ("docx/routes/read.md", 700),
    }
    if (skill, route) in m:
        rel, n = m[(skill, route)]
        return f"\n### Route instructions excerpt ({route})\n" + _cached(rel)[:n] + "\n"
    return ""

import re

_CJK_CHAR = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
_CJK_RULE = re.compile(r"SimSun|SimHei|YaHei|STSong|CJK|\u4e2d\u6587", re.I)

def _english_only(text: str) -> str:
    """English-only corpus policy: drop any line containing CJK characters or
    CJK-specific font/rule references (stale guidance for the English corpus)."""
    return "\n".join(line for line in text.splitlines()
                     if not _CJK_CHAR.search(line) and not _CJK_RULE.search(line))


# Per-capability tooling hints (sandbox mounts the plugin at /skills/)
ROUTE_HINTS = {
    "toc_fix": "- TOC repair tool: `python3 /skills/docx/scripts/add_toc_placeholders.py <file.docx> --auto`.\n",
    "footer_fix": "- Footer field repair tool: `python3 /skills/docx/scripts/fix_footer_fields.py <file.docx>`.\n",
    "comment": "- Comment API: `sys.path.insert(0, '/skills')` then `from skills.docx.scripts.document import Document`; "
               "Document(<unpacked_dir>, author=...); get_node(tag='w:p', contains='...'); "
               "add_comment(start=node, end=node, text='...'); save(); re-zip the unpacked dir.\n",
    "qa": "- Quality gate: `python3 /skills/pdf/scripts/pdf_qa.py <file.pdf>` prints a PASS/WARN verdict.\n",
    "palette": "- Palette generator: `pdf.py palette.generate --intent business` prints palette code with an Intent header.\n",
    "font_check": "- `pdf.py font.check <file.pdf>` prints JSON with status 'ok' and total_issues.\n",
    "toc_check": "- `pdf.py toc.check <file.pdf>` prints JSON with a pass field.\n",
}
_TOOL_HINT = ("- The pdf skill CLI lives at `/skills/pdf/scripts/pdf.py`. Subcommands "
              "(pages.merge/split/rotate/crop, extract.text/table/image, form.info/fill, "
              "meta.get/set, font.check, toc.check) print JSON with status 'success' on "
              "success and exit 1 on errors. mutates require explicit --output.\n")
_XLSX_TOOL_HINT = ("- The xlsx skill CLI lives at `/skills/xlsx/xlsx.py`. Subcommands: "
                   "inspect, scan, audit (JSON summaries) and pivot "
                   "(--source, --values, --rows, <input> <output>).\n")
_PPTX_TOOL_HINT = ("- python-pptx: `Presentation(src)`; `slides.add_slide(layout)`; "
                   "add_textbox for titles; `save(out)`.\n")


def _route_hint(route: str, skill: str) -> str:
    if route in ROUTE_HINTS:
        return "\n### Tooling hint\n" + ROUTE_HINTS[route]
    if skill == "pdf" and route not in ("report",):
        return "\n### Tooling hint\n" + _TOOL_HINT
    if skill == "xlsx" and route not in ("create", "edit", "analyze"):
        return "\n### Tooling hint\n" + _XLSX_TOOL_HINT
    if skill == "pptx" and route != "create":
        return "\n### Tooling hint\n" + _PPTX_TOOL_HINT
    return ""


def load_context_pack(skill: str, route: str, scene: str) -> dict:
    """Returns {'system': str, 'files': [plugin paths used]}."""
    if skill == "docx":
        rules = _docx_router_rules()
    elif skill == "xlsx":
        rules = _xlsx_rules()
    elif skill == "pptx":
        rules = _pptx_rules()
    else:
        rules = _pdf_rules()
    parts = [
        ROLE_PREAMBLE,
        "\n## Skill rules (from document-skills corpus)\n" + _english_only(rules),
        _route_excerpt(skill, route),
        _scene_excerpt(skill, route, scene),
        _route_hint(route, skill),
        "\nUse the postcheck tool after every artifact. Repair with targeted patches only.",
    ]
    parts = [_english_only(p) for p in parts]
    files = [f"document-skills@{PLUGIN_REV}:{skill}/SKILL.md"]
    return {"system": "".join(parts), "files": files}
