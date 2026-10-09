# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 401], ["South", 414], ["East", 752], ["West", 750]]:
    ws.append(r)

wb.save("task_000687_wb.xlsx")
print("ok")
