# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 542], ["South", 315], ["East", 312], ["West", 819]]:
    ws.append(r)

wb.save("task_000326_wb.xlsx")
print("ok")
