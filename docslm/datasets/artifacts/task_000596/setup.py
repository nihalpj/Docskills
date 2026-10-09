# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 724], ["South", 315], ["East", 762], ["West", 495]]:
    ws.append(r)

wb.save("task_000596_wb.xlsx")
print("ok")
