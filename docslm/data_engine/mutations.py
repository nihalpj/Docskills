"""Failure injection for the repair curriculum (Data Engine §5).

Each mutation applies a deterministic defect to a known-good script and pairs
it with the inverse fix. Only mutations with a REAL failure signal are used:
either the execution fails, or the skill verifier flags a violation.
"""
from dataclasses import dataclass
from typing import Callable


@dataclass
class Mutation:
    name: str
    error_class: str
    mutate: Callable[[str], str]
    fix: Callable[[str], str]
    applies_to: str  # "docx-js" | "python" | "xlsx" | "pptx-js" | "pdf"
    scenes: tuple | None = None  # None = all scenes of the kind


def _sub1(code: str, old: str, new: str, count: int = 1) -> str:
    return code.replace(old, new, count)


DOCX_JS_MUTATIONS = [
    Mutation(
        "heading_level_skip", "format_violation",
        lambda c: _sub1(c, "heading: HeadingLevel.HEADING_2", "heading: HeadingLevel.HEADING_3", 1),
        lambda c: _sub1(c, "heading: HeadingLevel.HEADING_3", "heading: HeadingLevel.HEADING_2", 1),
        "docx-js", scenes=("contract", "resume", "exam")),
    Mutation(
        "trailing_blank_page", "format_violation",
        lambda c: _sub1(c, "const doc = new Document({",
                        "sections.push(new Paragraph({ children: [new PageBreak()] }));\n"
                        "sections.push(new Paragraph({ children: [new PageBreak()] }));\n"
                        "const doc = new Document({", 1),
        lambda c: _sub1(c,
                        "sections.push(new Paragraph({ children: [new PageBreak()] }));\n"
                        "sections.push(new Paragraph({ children: [new PageBreak()] }));\n"
                        "const doc", "const doc", 1),
        "docx-js"),
    Mutation(
        "shading_solid", "format_violation",
        lambda c: _sub1(c, "ShadingType.CLEAR", "ShadingType.SOLID", 2),
        lambda c: _sub1(c, "ShadingType.SOLID", "ShadingType.CLEAR", 2),
        "docx-js"),
    Mutation(
        "missing_import", "api_error",
        lambda c: _sub1(c, "  HeadingLevel, AlignmentType, WidthType, ShadingType, PageBreak,\n", ""),
        lambda c: _sub1(c, "  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,\n",
                        "  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,\n"
                        "  HeadingLevel, AlignmentType, WidthType, ShadingType, PageBreak,\n"),
        "docx-js"),
    Mutation(
        "undefined_helper", "api_error",
        lambda c: _sub1(c, "sections.push(h1(", "sections.push(head1(", 1),
        lambda c: _sub1(c, "sections.push(head1(", "sections.push(h1(", 1),
        "docx-js"),
]

PY_MUTATIONS = [
    Mutation(
        "missing_import_py", "api_error",
        lambda c: _sub1(c, "from docx import Document\n", "from docx import DocumentX\n"),
        lambda c: _sub1(c, "from docx import DocumentX\n", "from docx import Document\n"),
        "python"),
    Mutation(
        "attr_typo", "api_error",
        lambda c: _sub1(c, "doc.save(", "doc.savee(", 1),
        lambda c: _sub1(c, "doc.savee(", "doc.save(", 1),
        "python"),
    Mutation(
        "py_syntax", "syntax",
        lambda c: _sub1(c, "print(json.dumps(", "print(json.dumpsS(", 1),
        lambda c: _sub1(c, "print(json.dumpsS(", "print(json.dumps(", 1),
        "python"),
]

# for plugin-CLI task scripts (they all end with print(json.dumps(...)))
TOOL_MUTATIONS = [PY_MUTATIONS[2]]

# pdf tool scripts also invoke pdf.py with --output flags
PDF_TOOL_MUTATIONS = TOOL_MUTATIONS + [
    Mutation(
        "cli_flag_typo", "cli_error",
        lambda c: _sub1(c, '"--output"', '"--outpu"', 1),
        lambda c: _sub1(c, '"--outpu"', '"--output"', 1),
        "python-cli"),
]

XLSX_MUTATIONS = [
    Mutation(
        "ref_unknown_sheet", "range_error",
        lambda c: _sub1(c, '"=SUM(Data!B2:B{0})"', '"=SUM(Missing!B2:B{0})"', 1),
        lambda c: _sub1(c, '"=SUM(Missing!B2:B{0})"', '"=SUM(Data!B2:B{0})"', 1),
        "xlsx"),
    Mutation(
        "openpyxl_import", "api_error",
        lambda c: _sub1(c, "from openpyxl import Workbook\n", "from openpyxl import Workbok\n"),
        lambda c: _sub1(c, "from openpyxl import Workbok\n", "from openpyxl import Workbook\n"),
        "xlsx"),
]

PPTX_MUTATIONS = [
    Mutation(
        "undefined_method", "api_error",
        lambda c: _sub1(c, "pptx.writeFile(", "pptx.writefiles(", 1),
        lambda c: _sub1(c, "pptx.writefiles(", "pptx.writeFile(", 1),
        "pptx-js"),
    Mutation(
        "bad_chart_enum", "api_error",
        lambda c: _sub1(c, "pptx.ChartType.bar", "pptx.ChartType.barr", 1),
        lambda c: _sub1(c, "pptx.ChartType.barr", "pptx.ChartType.bar", 1),
        "pptx-js"),
]

PDF_MUTATIONS = [
    Mutation(
        "pdf_syntax", "syntax",
        lambda c: _sub1(c, "doc.build(story)", "doc.build(story", 1),
        lambda c: _sub1(c, "doc.build(story", "doc.build(story)", 1),
        "pdf"),
]

ALL = (DOCX_JS_MUTATIONS + PY_MUTATIONS + XLSX_MUTATIONS
       + PPTX_MUTATIONS + PDF_MUTATIONS + TOOL_MUTATIONS + PDF_TOOL_MUTATIONS)


def pick_mutation(kind: str, scene: str, rng) -> Mutation | None:
    """kind: tag from build._kind_tag ('node-docx', 'python-docx', '<skill>-tools',
    ...). 15% of tasks get no mutation."""
    if rng.random() < 0.15:
        return None
    pool = {
        "node-docx": DOCX_JS_MUTATIONS,
        "node-pptx": PPTX_MUTATIONS,
        "python-docx": PY_MUTATIONS,
        "python-xlsx": XLSX_MUTATIONS,
        "python-pdf": PDF_MUTATIONS + PY_MUTATIONS,
        "docx-tools": TOOL_MUTATIONS,
        "pdf-tools": PDF_TOOL_MUTATIONS,
        "xlsx-tools": TOOL_MUTATIONS,
        "pptx-tools": TOOL_MUTATIONS,
    }[kind]
    pool = [m for m in pool if m.scenes is None or scene in m.scenes]
    return rng.choice(pool)
