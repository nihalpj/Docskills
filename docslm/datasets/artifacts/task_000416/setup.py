# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 552], ["South", 393], ["East", 113], ["West", 121]]:
    ws.append(r)

wb.save("task_000416_wb.xlsx")
print("ok")
