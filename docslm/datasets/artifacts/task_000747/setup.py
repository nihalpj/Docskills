# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 194], ["South", 607], ["East", 408], ["West", 484]]:
    ws.append(r)

wb.save("task_000747_wb.xlsx")
print("ok")
