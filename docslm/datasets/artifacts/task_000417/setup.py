# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 624], ["South", 526], ["East", 714], ["West", 508]]:
    ws.append(r)

wb.save("task_000417_wb.xlsx")
print("ok")
