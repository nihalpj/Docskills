# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 260], ["South", 397], ["East", 220], ["West", 576]]:
    ws.append(r)

wb.save("task_000717_wb.xlsx")
print("ok")
