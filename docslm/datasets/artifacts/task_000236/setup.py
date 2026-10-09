# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 874], ["South", 629], ["East", 356], ["West", 641]]:
    ws.append(r)

wb.save("task_000236_wb.xlsx")
print("ok")
