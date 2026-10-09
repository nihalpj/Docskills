# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 381], ["South", 620], ["East", 871], ["West", 767]]:
    ws.append(r)

wb.save("task_000057_wb.xlsx")
print("ok")
