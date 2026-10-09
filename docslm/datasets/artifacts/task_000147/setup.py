# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 280], ["South", 482], ["East", 110], ["West", 747]]:
    ws.append(r)

wb.save("task_000147_wb.xlsx")
print("ok")
