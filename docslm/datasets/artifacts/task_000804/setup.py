# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 639], ["South", 109], ["East", 266], ["West", 351]]:
    ws.append(r)

wb.save("task_000804_wb.xlsx")
print("ok")
