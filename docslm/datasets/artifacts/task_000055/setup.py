# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 810], ["South", 367], ["East", 648], ["West", 657]]:
    ws.append(r)

wb.save("task_000055_wb.xlsx")
print("ok")
