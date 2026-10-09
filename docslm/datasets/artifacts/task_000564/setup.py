# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 273], ["South", 636], ["East", 282], ["West", 340]]:
    ws.append(r)

wb.save("task_000564_wb.xlsx")
print("ok")
