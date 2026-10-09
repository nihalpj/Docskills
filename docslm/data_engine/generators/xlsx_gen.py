"""XLSX generators (openpyxl) — create / edit / analyze. English-only."""
from string import Template
import json as _json
from .. import content as C

_CREATE = Template("""# DocSLM xlsx create — openpyxl ($scene)
import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.chart import BarChart, Reference

PRIMARY = "$primary"

wb = Workbook()
ws = wb.active
ws.title = "Data"
headers = $headers
ws.append(headers)
rows = $rows
for r in rows:
    ws.append(r)
last = ws.max_row
for row in ws.iter_rows(min_row=2, min_col=4, max_col=4):
    row[0].value = "=ROUND(B{0}-C{0},1)".format(row[0].row)
ws.append(["$total_label", "=SUM(B2:B{0})".format(last), "=SUM(C2:C{0})".format(last), "=ROUND(B{1}-C{1},1)".format(last, last + 1)])
total_row = ws.max_row
for c in ws[1]:
    c.font = Font(bold=True, color="FFFFFF")
    c.fill = PatternFill(fill_type="solid", fgColor=PRIMARY)
    c.alignment = Alignment(horizontal="center")
for c in ws[total_row]:
    c.font = Font(bold=True)
ws.freeze_panes = "A2"
for i, w in enumerate([22, 14, 14, 14], start=1):
    ws.column_dimensions[chr(64 + i)].width = w

chart = BarChart()
chart.title = "$chart_title"
chart.y_axis.title = "$axis"
chart.height, chart.width = 8, 16
data = Reference(ws, min_col=2, min_row=1, max_row=last)
cats = Reference(ws, min_col=1, min_row=2, max_row=last)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
ws.add_chart(chart, "F2")

summary = wb.create_sheet("Summary")
summary["A1"] = "$kpi_label"
summary["A2"], summary["B2"] = "$rev_label", "=SUM(Data!B2:B{0})".format(last)
summary["A3"], summary["B3"] = "$cost_label", "=SUM(Data!C2:C{0})".format(last)
summary["A4"], summary["B4"] = "$margin_label", "=ROUND(SUM(Data!B2:B{0})-SUM(Data!C2:C{0}),1)".format(last)
for col in ("A", "B"):
    cell = summary[f"{col}1"]
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill(fill_type="solid", fgColor=PRIMARY)
summary.column_dimensions["A"].width = 20
summary.column_dimensions["B"].width = 16

wb.save("$artifact")
print(json.dumps({"exit": 0, "artifact": "$artifact", "sheets": 2}))
""")


def gen_create(spec, rng):
    primary, accent, light = C.palette(rng)
    artifact = f"{spec.task_id}_wb.xlsx"
    n = 5 + spec.difficulty
    rows = []
    for i in range(n):
        name = (C.product(rng, spec.lang) if i % 2 == 0 else C.department(rng, spec.lang))
        rows.append([name, rng.randrange(80, 600), rng.randrange(40, 400)])
    headers = ["Item", "Revenue (k)", "Cost (k)", "Margin (k)"]
    code = _CREATE.substitute(
        scene=spec.scene, primary=primary,
        headers=_json.dumps(headers, ensure_ascii=False),
        rows=_json.dumps(rows, ensure_ascii=False),
        total_label="Total",
        chart_title="Revenue vs Cost",
        axis="k USD",
        kpi_label="KPI",
        rev_label="Total revenue",
        cost_label="Total cost",
        margin_label="Total margin",
        artifact=artifact)
    request = (f"Create workbook {artifact} with openpyxl: a Data sheet with {n} rows, formula "
               f"margin column, totals row, bar chart, and a Summary sheet with cross-sheet "
               f"formulas; styled header, frozen first row.")
    return {"runner": "python", "code": code, "artifact": artifact,
            "expect": {"kind": "xlsx", "min_rows": n + 1, "charts": 1},
            "request": request, "mutation": None}


_EDIT = Template("""# DocSLM xlsx edit — extend workbook
import json
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill

wb = load_workbook("$base")
ws = wb["Data"]
for r in $new_rows:
    ws.append(r)
last = ws.max_row
for row in ws.iter_rows(min_row=$old_last + 1, min_col=4, max_col=4):
    row[0].value = "=ROUND(B{0}-C{0},1)".format(row[0].row)
ws.cell(row=last + 1, column=1, value="$total_label")
ws.cell(row=last + 1, column=2, value="=SUM(B2:B{0})".format(last))
ws.cell(row=last + 1, column=3, value="=SUM(C2:C{0})".format(last))
ws.cell(row=last + 1, column=4, value="=ROUND(B{0}-C{0},1)".format(last + 1))
for c in ws[1]:
    c.font = Font(bold=True, color="FFFFFF")
    c.fill = PatternFill(fill_type="solid", fgColor="$primary")
wb.save("$artifact")
print(json.dumps({"exit": 0, "artifact": "$artifact", "appended": True}))
""")


def gen_edit(spec, rng):
    base = f"{spec.task_id}_src.xlsx"
    artifact = f"{spec.task_id}_upd.xlsx"
    base_rows = _json.dumps([[f"row{i}", 100 + i * 10, 60 + i * 5] for i in range(1, 5)])
    setup = (
        "import json\nfrom openpyxl import Workbook\n"
        "wb = Workbook(); ws = wb.active; ws.title = \"Data\"\n"
        "ws.append(['Item', 'Revenue', 'Cost', 'Margin'])\n"
        f"for r in {base_rows}:\n"
        "    ws.append(r)\n"
        "wb.save(\"" + base + "\")\nprint('ok')\n")
    new_rows = _json.dumps([[C.product(rng, spec.lang), rng.randrange(80, 500), rng.randrange(40, 300)]
                            for _ in range(3)], ensure_ascii=False)
    code = _EDIT.substitute(base=base, artifact=artifact,
                            new_rows=new_rows, old_last=5, total_label="Total",
                            primary="1F4E79")
    request = (f"Update {base}: append 3 rows, fill formula column and totals row, restyle the "
               f"header, save as {artifact}.")
    return {"runner": "python", "code": code, "setup_runner": "python", "setup_code": setup,
            "artifact": artifact, "expect": {"kind": "xlsx", "min_rows": 9, "charts": 0},
            "request": request, "mutation": None}


def gen_analyze(spec, rng):
    """analyze = create + aggregate summary sheet."""
    plan = gen_create(spec, rng)
    plan["expect"]["kind"] = "xlsx"
    plan["request"] = plan["request"] + " The summary sheet aggregates margin by item."
    return plan
