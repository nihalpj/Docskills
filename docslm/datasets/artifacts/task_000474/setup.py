# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 325], ["South", 313], ["East", 267], ["West", 137]]:
    ws.append(r)

wb.save("task_000474_wb.xlsx")
print("ok")
