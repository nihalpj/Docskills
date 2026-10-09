# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 738], ["South", 544], ["East", 545], ["West", 116]]:
    ws.append(r)

wb.save("task_000447_wb.xlsx")
print("ok")
