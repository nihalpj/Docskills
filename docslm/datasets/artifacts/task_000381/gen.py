# DocSLM xlsx create — openpyxl (general)
import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.chart import BarChart, Reference

PRIMARY = "33544A"

wb = Workbook()
ws = wb.active
ws.title = "Data"
headers = ["Item", "Revenue (k)", "Cost (k)", "Margin (k)"]
ws.append(headers)
rows = [["Orbit CRM", 82, 111], ["Engineering", 537, 192], ["Orbit CRM", 120, 82], ["Operations", 443, 330], ["Vertex Payroll", 137, 93], ["Operations", 504, 77]]
for r in rows:
    ws.append(r)
last = ws.max_row
for row in ws.iter_rows(min_row=2, min_col=4, max_col=4):
    row[0].value = "=ROUND(B{0}-C{0},1)".format(row[0].row)
ws.append(["Total", "=SUM(B2:B{0})".format(last), "=SUM(C2:C{0})".format(last), "=ROUND(B{1}-C{1},1)".format(last, last + 1)])
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
chart.title = "Revenue vs Cost"
chart.y_axis.title = "k USD"
chart.height, chart.width = 8, 16
data = Reference(ws, min_col=2, min_row=1, max_row=last)
cats = Reference(ws, min_col=1, min_row=2, max_row=last)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
ws.add_chart(chart, "F2")

summary = wb.create_sheet("Summary")
summary["A1"] = "KPI"
summary["A2"], summary["B2"] = "Total revenue", "=SUM(Data!B2:B{0})".format(last)
summary["A3"], summary["B3"] = "Total cost", "=SUM(Data!C2:C{0})".format(last)
summary["A4"], summary["B4"] = "Total margin", "=ROUND(SUM(Data!B2:B{0})-SUM(Data!C2:C{0}),1)".format(last)
for col in ("A", "B"):
    cell = summary[f"{col}1"]
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill(fill_type="solid", fgColor=PRIMARY)
summary.column_dimensions["A"].width = 20
summary.column_dimensions["B"].width = 16

wb.save("task_000381_wb.xlsx")
print(json.dumps({"exit": 0, "artifact": "task_000381_wb.xlsx", "sheets": 2}))
