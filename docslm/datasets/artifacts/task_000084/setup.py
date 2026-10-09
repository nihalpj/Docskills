# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 394], ["South", 365], ["East", 890], ["West", 501]]:
    ws.append(r)

wb.save("task_000084_wb.xlsx")
print("ok")
