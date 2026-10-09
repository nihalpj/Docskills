# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 526], ["South", 603], ["East", 468], ["West", 874]]:
    ws.append(r)

wb.save("task_000204_wb.xlsx")
print("ok")
