# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 286], ["South", 433], ["East", 495], ["West", 439]]:
    ws.append(r)

wb.save("task_000776_wb.xlsx")
print("ok")
