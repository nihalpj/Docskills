# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 841], ["South", 567], ["East", 153], ["West", 603]]:
    ws.append(r)

wb.save("task_000054_wb.xlsx")
print("ok")
