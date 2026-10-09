# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 133], ["South", 167], ["East", 291], ["West", 442]]:
    ws.append(r)

wb.save("task_000654_wb.xlsx")
print("ok")
