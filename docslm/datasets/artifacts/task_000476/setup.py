# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 615], ["South", 537], ["East", 833], ["West", 785]]:
    ws.append(r)

wb.save("task_000476_wb.xlsx")
print("ok")
