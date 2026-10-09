# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 145], ["South", 515], ["East", 342], ["West", 179]]:
    ws.append(r)

wb.save("task_000357_wb.xlsx")
print("ok")
