# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 127], ["South", 274], ["East", 844], ["West", 479]]:
    ws.append(r)

wb.save("task_000506_wb.xlsx")
print("ok")
