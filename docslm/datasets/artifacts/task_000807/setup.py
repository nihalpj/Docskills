# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 671], ["South", 330], ["East", 222], ["West", 249]]:
    ws.append(r)

wb.save("task_000807_wb.xlsx")
print("ok")
