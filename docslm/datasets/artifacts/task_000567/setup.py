# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 863], ["South", 186], ["East", 448], ["West", 196]]:
    ws.append(r)

wb.save("task_000567_wb.xlsx")
print("ok")
