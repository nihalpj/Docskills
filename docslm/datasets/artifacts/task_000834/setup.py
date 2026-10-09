# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 877], ["South", 636], ["East", 329], ["West", 199]]:
    ws.append(r)

wb.save("task_000834_wb.xlsx")
print("ok")
