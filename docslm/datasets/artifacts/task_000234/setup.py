# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 652], ["South", 658], ["East", 514], ["West", 840]]:
    ws.append(r)

wb.save("task_000234_wb.xlsx")
print("ok")
