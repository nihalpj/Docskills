# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 315], ["South", 249], ["East", 805], ["West", 446]]:
    ws.append(r)

wb.save("task_000144_wb.xlsx")
print("ok")
