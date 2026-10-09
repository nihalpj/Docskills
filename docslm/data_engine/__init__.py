"""DocSLM data engine — execution-verified training data factory.

Implements docs/03_DATA_ENGINE.md. Every generated trajectory is grounded in
real execution: scripts actually run against the document-skills plugin's own
verification scripts, and only verified records are emitted.
"""
import os
from pathlib import Path

ENGINE_VERSION = "1.2.0"
PLUGIN_REV = "0.1.4"
DEFAULT_SEED = 2026

REPO_ROOT = Path(__file__).resolve().parent.parent
SANDBOX_ENV = REPO_ROOT / "sandbox_env"
PLUGIN_DIR = Path(os.environ.get(
    "DOCSLM_PLUGIN_DIR",
    "/home/nihal/.zcode/cli/plugins/cache/zcode-plugins-official/document-skills/0.1.4/skills",
))
DATASETS_DIR = REPO_ROOT / "datasets"

# Tool surface the model is trained to emit — mirrors docs/02_ARCHITECTURE.md §2.
TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "run_node",
        "description": "Execute a JavaScript (Node.js) script in the sandbox. Use for docx-js and pptxgenjs generation.",
        "parameters": {"type": "object", "properties": {
            "code": {"type": "string", "description": "Complete script source."},
        }, "required": ["code"]},
    }},
    {"type": "function", "function": {
        "name": "run_python",
        "description": "Execute a Python script in the sandbox. Use for openpyxl, python-docx, reportlab, pypdf work.",
        "parameters": {"type": "object", "properties": {
            "code": {"type": "string", "description": "Complete script source."},
        }, "required": ["code"]},
    }},
    {"type": "function", "function": {
        "name": "postcheck",
        "description": "Run the skill's verification on an artifact (docx formatting rules, workbook recalculation checks, render smoke tests). Returns violations as JSON.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Artifact path relative to the workspace."},
        }, "required": ["path"]},
    }},
    {"type": "function", "function": {
        "name": "load_reference",
        "description": "Page in a skill reference file (ooxml, toc, chart-templates, math-formulas, design-system) when the packed context is insufficient.",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "enum": [
                "ooxml", "toc", "chart-templates", "math-formulas",
                "design-system", "common-rules", "faq"]},
        }, "required": ["name"]},
    }},
    {"type": "function", "function": {
        "name": "escalate",
        "description": "Escalate the task to a stronger model after exhausting the repair budget. Carries task, artifact state, and diagnostics.",
        "parameters": {"type": "object", "properties": {
            "reason": {"type": "string"},
        }, "required": ["reason"]},
    }},
]

ROLE_PREAMBLE = (
    "You are DocSLM, a document-production agent. You complete document tasks by "
    "writing and executing code (docx-js, python-docx, openpyxl, pptxgenjs, reportlab, pypdf) "
    "inside a sandboxed workspace, then verifying the artifact. Rules of the loop:\n"
    "1. Exactly one tool call per turn; arguments must be strict JSON.\n"
    "2. After producing an artifact, call postcheck. If violations are returned, issue a "
    "TARGETED PATCH that fixes only the reported violations — never regenerate from scratch.\n"
    "3. Repair budget: 2 repair turns. If still failing, call escalate.\n"
    "4. Follow the formatting rules in the context exactly (line spacing 312 twips = 1.3x, "
    "ShadingType.CLEAR for all shading, table margins always set, tableHeader+cantSplit on rows, "
    "cover pages built from validated recipes only).\n"
    "5. Respond in the user's language."
)
