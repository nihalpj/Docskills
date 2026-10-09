# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 144], ["South", 858], ["East", 123], ["West", 398]]:
    ws.append(r)

wb.save("task_000387_wb.xlsx")
print("ok")
