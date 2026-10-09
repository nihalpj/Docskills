# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 754], ["South", 476], ["East", 688], ["West", 175]]:
    ws.append(r)

wb.save("task_000025_wb.xlsx")
print("ok")
