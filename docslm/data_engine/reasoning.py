"""Grounded chain-of-thought generation.

Every assistant turn gets a <think> block that is derived from the task spec,
the plan, and (for repairs) the measured failure signal — so the reasoning is
always consistent with what the script actually does (supervised CoT, no
hallucinated rationale). Format follows the Qwen3 convention:
`<think> ... </think>` placed in the assistant message content before tool_calls.
"""

FIX_EXPLANATION = {
    "heading_level_skip": "restore HeadingLevel.HEADING_2 on the subheading style so heading levels stay continuous",
    "trailing_blank_page": "remove the two trailing PageBreak paragraphs that created a blank final page",
    "shading_solid": "switch ShadingType.SOLID back to ShadingType.CLEAR (SOLID hides text and fails postcheck)",
    "missing_import": "re-add the missing docx-js import line so the destructured symbols are defined",
    "undefined_helper": "restore the correct helper name (h1) at the call site",
    "missing_import_py": "fix the mistyped module import (DocumentX → Document)",
    "attr_typo": "fix the mistyped method name (savee → save)",
    "py_syntax": "fix the mistyped print(json.dumps(...)) call that raised the NameError",
    "ref_unknown_sheet": "point the cross-sheet formula back at the existing 'Data' sheet instead of the missing one",
    "openpyxl_import": "fix the mistyped openpyxl import (Workbok → Workbook)",
    "undefined_method": "restore the correct pptxgenjs method name (writefiles → writeFile)",
    "bad_chart_enum": "restore the correct pptx.ChartType enum value",
    "pdf_syntax": "close the unclosed doc.build(story) call",
    "cli_flag_typo": "correct the misspelled --output flag so the CLI accepts the call",
}

ERROR_CLASS_CAUSE = {
    "api_error": "an API/import name was mistyped, so the runtime reference does not exist",
    "format_violation": "a formatting rule was violated while the script still executed",
    "syntax": "a typo broke the code before it could run",
    "range_error": "a formula references a sheet/range that does not exist in the workbook",
    "cli_error": "the plugin CLI rejected the call because a flag is misspelled",
}


def _route_line(spec, artifact: str) -> str:
    return (f"Route: {spec.skill}/{spec.route}, scene '{spec.scene}', "
            f"difficulty L{spec.difficulty}, output '{artifact}'.")


def _authoring_rules(spec) -> str:
    if spec.skill == "docx":
        return ("Formatting rules that postcheck enforces: line spacing 312 twips (1.3x) on "
                "every paragraph, ShadingType.CLEAR for all shading, table margins set, "
                "tableHeader/cantSplit on rows, heading levels continuous from H1, no blank "
                "pages, cover as a full-width recipe table.")
    if spec.skill == "xlsx":
        return ("Spreadsheet rules: styled header row + freeze panes, explicit formulas (no "
                "hardcoded results), all cross-sheet references must point at existing sheets "
                "and in-range cells, charts reference real ranges.")
    if spec.skill == "pptx":
        return ("Deck rules: 16:9 layout defined first, title bar on every slide, font sizes "
                "12-40pt, tables with explicit colW, charts via pptx.ChartType.")
    return ("PDF rules: A4 SimpleDocTemplate, built-in Helvetica styles, tables with GRID + "
            "styled header row, then verify pages/text with pypdf.")


def plan_reasoning(spec, plan, runner: str) -> str:
    """Turn-1 reasoning: route, rules, execution plan, verification plan."""
    artifact = plan["artifact"]
    route = spec.route
    if route in ("toc_fix", "footer_fix", "comment"):
        tool = {
            "toc_fix": ("/skills/docx/scripts/add_toc_placeholders.py --auto",
                        "it inserts placeholder entries for the TOC field and reports them"),
            "footer_fix": ("/skills/docx/scripts/fix_footer_fields.py",
                           "it normalizes bare PAGE fields in the footer XML"),
        }.get(route)
        if route == "comment":
            steps = ("Unpack the docx, use the plugin comment API "
                     "(skills.docx.scripts.document.Document: get_node(contains=...) then "
                     "add_comment(start, end, text)), save, and re-zip the unpacked tree.")
        else:
            steps = f"Run the plugin tool `{tool[0]}` — {tool[1]}."
        return (
            "<think>\nTask: operate the docx skill's repair tooling.\n"
            f"{_route_line(spec, artifact)}\n{steps}\n"
            "The artifact must still pass postcheck afterwards (line-spacing warnings on the "
            "input fixture are pre-existing and not this task's target).\n"
            "Plan: one tool call now; then postcheck; repair budget 2 turns if needed.\n</think>")
    if spec.skill == "pdf" and route != "report":
        return (
            "<think>\nTask: drive the pdf skill CLI.\n"
            f"{_route_line(spec, artifact)}\n"
            "Contract: /skills/pdf/scripts/pdf.py subcommands print JSON with status "
            "'success' on success and exit 1 on errors (extract the JSON object from stdout "
            "to tolerate warning lines). Some subcommands (form.fill, meta.set) write the "
            "output file and may print no JSON — verify via the follow-up check instead.\n"
            f"Steps: run the '{route}' subcommand with explicit --output/-o, assert on the "
            "JSON status or the follow-up probe (pypdf / form.info / meta.get), then report.\n"
            "Plan: one tool call now; then postcheck; repair budget 2 turns.\n</think>")
    if spec.skill == "xlsx" and route in ("inspect", "scan", "audit", "pivot"):
        return (
            "<think>\nTask: operate the xlsx skill CLI.\n"
            f"{_route_line(spec, artifact)}\n"
            "Contract: /skills/xlsx/xlsx.py inspect/scan/audit print JSON summaries; pivot "
            "takes --source Sheet!A1:B5 --values <header> --rows <header> plus input and "
            "output paths, and writes a new workbook.\n"
            "Steps: run the subcommand, assert on its JSON (or reopen the pivot output with "
            "openpyxl), then report.\n"
            "Plan: one tool call now; then postcheck; repair budget 2 turns.\n</think>")
    if spec.skill == "pptx" and route != "create":
        return (
            "<think>\nTask: edit a deck with python-pptx.\n"
            f"{_route_line(spec, artifact)}\n"
            "Plan: open the deck, append a slide via slide_layouts (guard the index — "
            "pptxgenjs decks ship few layouts), add a titled textbox, save, then reopen to "
            "assert the slide count and title.\n"
            "One tool call now; then postcheck; repair budget 2 turns.\n</think>")
    # authoring routes
    lib = "docx-js" if runner == "node" else ("pptxgenjs" if spec.skill == "pptx"
                                              else "python (openpyxl/python-docx/reportlab/pypdf)")
    return (
        "<think>\n"
        f"Task: produce a {spec.scene} document.\n{_route_line(spec, artifact)}\n"
        f"Approach: generate it with {lib}, writing '{artifact}'.\n"
        f"{_authoring_rules(spec)}\n"
        "Plan: write the complete script in one tool call, execute it, then call postcheck "
        "on the artifact. On violations: targeted patch only (never regenerate); repair "
        "budget 2 turns, then escalate.\n</think>")


def repair_reasoning(spec, plan, mutation_name: str, error_class: str,
                     fail_signal: str, turn: int) -> str:
    cause = ERROR_CLASS_CAUSE.get(error_class, error_class)
    fix = FIX_EXPLANATION.get(mutation_name, "apply the targeted correction")
    return (
        "<think>\n"
        f"Failure analysis (repair turn {turn}/2).\n"
        f"Measured signal: {fail_signal}\n"
        f"Root cause: {cause}.\n"
        f"Patch plan: minimal, targeted change only — {fix}. Keep the rest of the working "
        "script unchanged; do not regenerate the whole artifact.\n"
        "Then re-run and postcheck again; if it still fails, escalate.\n</think>")


def verify_reasoning(spec, plan) -> str:
    return (
        "<think>\n"
        f"The script reported success for '{plan['artifact']}'. Postcheck is authoritative "
        "for docx formatting (or the format-specific structural check), so verify before "
        "answering. Expect zero violations; if any appear, issue a targeted patch within "
        "the remaining repair budget.\n</think>")


def shallow_reasoning(spec) -> str:
    """Deliberately weak rationale for the rejected DPO side."""
    return ("<think>\n"
            "Simple task — just write the script and run it, no need to check the skill "
            "rules or verify the artifact afterwards.\n</think>")


def routing_reasoning(label: dict, request_head: str) -> str:
    return (
        "<think>\n"
        f"The request mentions '{request_head}' — this is a {label['skill']} task. "
        f"Intent matches the {label['route']} route; content/scene indicators map to "
        f"'{label['scene']}'.\n</think>")
