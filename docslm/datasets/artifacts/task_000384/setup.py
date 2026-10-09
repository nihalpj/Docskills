# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 409], ["South", 308], ["East", 177], ["West", 695]]:
    ws.append(r)

wb.save("task_000384_wb.xlsx")
print("ok")
