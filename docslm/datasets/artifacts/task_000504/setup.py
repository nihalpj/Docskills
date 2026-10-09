# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 636], ["South", 526], ["East", 256], ["West", 207]]:
    ws.append(r)

wb.save("task_000504_wb.xlsx")
print("ok")
