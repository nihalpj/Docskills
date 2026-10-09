# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 321], ["South", 573], ["East", 752], ["West", 122]]:
    ws.append(r)

wb.save("task_000266_wb.xlsx")
print("ok")
