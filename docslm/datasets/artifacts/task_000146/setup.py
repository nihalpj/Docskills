# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 828], ["South", 301], ["East", 321], ["West", 744]]:
    ws.append(r)

wb.save("task_000146_wb.xlsx")
print("ok")
