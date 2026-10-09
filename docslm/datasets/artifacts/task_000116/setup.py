# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 518], ["South", 394], ["East", 537], ["West", 532]]:
    ws.append(r)

wb.save("task_000116_wb.xlsx")
print("ok")
