# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 422], ["South", 635], ["East", 549], ["West", 342]]:
    ws.append(r)

wb.save("task_000444_wb.xlsx")
print("ok")
