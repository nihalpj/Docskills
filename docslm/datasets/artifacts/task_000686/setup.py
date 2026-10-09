# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 369], ["South", 602], ["East", 103], ["West", 381]]:
    ws.append(r)

wb.save("task_000686_wb.xlsx")
print("ok")
