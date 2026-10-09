# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 502], ["South", 106], ["East", 437], ["West", 338]]:
    ws.append(r)

wb.save("task_000926_wb.xlsx")
print("ok")
