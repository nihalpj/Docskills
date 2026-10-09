# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 180], ["South", 739], ["East", 702], ["West", 266]]:
    ws.append(r)

wb.save("task_000386_wb.xlsx")
print("ok")
