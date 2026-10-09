# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 828], ["South", 310], ["East", 628], ["West", 747]]:
    ws.append(r)

wb.save("task_000264_wb.xlsx")
print("ok")
