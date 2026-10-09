# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 766], ["South", 743], ["East", 528], ["West", 261]]:
    ws.append(r)

wb.save("task_000207_wb.xlsx")
print("ok")
