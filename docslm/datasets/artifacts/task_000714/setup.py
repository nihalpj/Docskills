# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 625], ["South", 362], ["East", 590], ["West", 625]]:
    ws.append(r)

wb.save("task_000714_wb.xlsx")
print("ok")
