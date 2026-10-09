# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 804], ["South", 201], ["East", 496], ["West", 323]]:
    ws.append(r)

wb.save("task_000534_wb.xlsx")
print("ok")
