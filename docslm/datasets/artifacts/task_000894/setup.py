# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 304], ["South", 182], ["East", 202], ["West", 604]]:
    ws.append(r)

wb.save("task_000894_wb.xlsx")
print("ok")
