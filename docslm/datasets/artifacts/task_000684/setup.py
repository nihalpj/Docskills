# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 773], ["South", 458], ["East", 291], ["West", 872]]:
    ws.append(r)

wb.save("task_000684_wb.xlsx")
print("ok")
