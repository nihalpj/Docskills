# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 555], ["South", 178], ["East", 427], ["West", 316]]:
    ws.append(r)

wb.save("task_000117_wb.xlsx")
print("ok")
