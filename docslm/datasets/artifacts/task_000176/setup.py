# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 889], ["South", 546], ["East", 312], ["West", 791]]:
    ws.append(r)

wb.save("task_000176_wb.xlsx")
print("ok")
