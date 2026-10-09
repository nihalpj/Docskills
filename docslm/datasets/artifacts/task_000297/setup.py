# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 832], ["South", 408], ["East", 796], ["West", 855]]:
    ws.append(r)

wb.save("task_000297_wb.xlsx")
print("ok")
