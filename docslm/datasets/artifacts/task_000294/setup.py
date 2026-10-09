# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 348], ["South", 673], ["East", 823], ["West", 660]]:
    ws.append(r)

wb.save("task_000294_wb.xlsx")
print("ok")
