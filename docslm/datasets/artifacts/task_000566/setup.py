# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 654], ["South", 794], ["East", 210], ["West", 262]]:
    ws.append(r)

wb.save("task_000566_wb.xlsx")
print("ok")
