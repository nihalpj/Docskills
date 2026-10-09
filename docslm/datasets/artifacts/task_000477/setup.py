# setup: workbook fixture (regional revenue workbook for pivoting)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 861], ["South", 415], ["East", 461], ["West", 836]]:
    ws.append(r)

wb.save("task_000477_wb.xlsx")
print("ok")
