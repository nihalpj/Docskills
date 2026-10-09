# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 518], ["South", 520], ["East", 514], ["West", 887]]:
    ws.append(r)

wb.save("task_000177_wb.xlsx")
print("ok")
