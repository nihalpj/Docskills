# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 742], ["South", 642], ["East", 344], ["West", 839]]:
    ws.append(r)

wb.save("task_000027_wb.xlsx")
print("ok")
