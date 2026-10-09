# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 561], ["South", 267], ["East", 657], ["West", 487]]:
    ws.append(r)

wb.save("task_000237_wb.xlsx")
print("ok")
