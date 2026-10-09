# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 626], ["South", 452], ["East", 665], ["West", 196]]:
    ws.append(r)

wb.save("task_000327_wb.xlsx")
print("ok")
