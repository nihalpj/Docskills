# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 143], ["South", 203], ["East", 389], ["West", 630]]:
    ws.append(r)

wb.save("task_000537_wb.xlsx")
print("ok")
