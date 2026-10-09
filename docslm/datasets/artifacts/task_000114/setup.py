# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 323], ["South", 798], ["East", 781], ["West", 369]]:
    ws.append(r)

wb.save("task_000114_wb.xlsx")
print("ok")
