# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 106], ["South", 128], ["East", 108], ["West", 293]]:
    ws.append(r)

wb.save("task_000056_wb.xlsx")
print("ok")
