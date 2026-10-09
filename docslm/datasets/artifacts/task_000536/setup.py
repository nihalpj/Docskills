# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 382], ["South", 515], ["East", 225], ["West", 622]]:
    ws.append(r)

wb.save("task_000536_wb.xlsx")
print("ok")
