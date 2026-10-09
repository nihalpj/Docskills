# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 436], ["South", 890], ["East", 177], ["West", 766]]:
    ws.append(r)

wb.save("task_000657_wb.xlsx")
print("ok")
