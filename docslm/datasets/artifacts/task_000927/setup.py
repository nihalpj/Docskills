# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 894], ["South", 812], ["East", 217], ["West", 432]]:
    ws.append(r)

wb.save("task_000927_wb.xlsx")
print("ok")
