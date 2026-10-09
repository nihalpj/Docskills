# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 116], ["South", 419], ["East", 626], ["West", 793]]:
    ws.append(r)

wb.save("task_000206_wb.xlsx")
print("ok")
