# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 228], ["South", 810], ["East", 868], ["West", 111]]:
    ws.append(r)

wb.save("task_000507_wb.xlsx")
print("ok")
