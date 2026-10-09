# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 755], ["South", 490], ["East", 582], ["West", 852]]:
    ws.append(r)

wb.save("task_000896_wb.xlsx")
print("ok")
