# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 500], ["South", 708], ["East", 580], ["West", 476]]:
    ws.append(r)

wb.save("task_000174_wb.xlsx")
print("ok")
