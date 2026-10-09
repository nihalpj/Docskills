# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 623], ["South", 205], ["East", 538], ["West", 152]]:
    ws.append(r)

wb.save("task_000594_wb.xlsx")
print("ok")
