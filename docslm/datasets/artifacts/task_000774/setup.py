# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 580], ["South", 499], ["East", 428], ["West", 296]]:
    ws.append(r)

wb.save("task_000774_wb.xlsx")
print("ok")
