# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 571], ["South", 460], ["East", 736], ["West", 209]]:
    ws.append(r)

wb.save("task_000924_wb.xlsx")
print("ok")
