# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 215], ["South", 589], ["East", 762], ["West", 235]]:
    ws.append(r)

wb.save("task_000897_wb.xlsx")
print("ok")
