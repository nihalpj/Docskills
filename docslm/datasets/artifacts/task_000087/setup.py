# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 459], ["South", 817], ["East", 887], ["West", 827]]:
    ws.append(r)

wb.save("task_000087_wb.xlsx")
print("ok")
