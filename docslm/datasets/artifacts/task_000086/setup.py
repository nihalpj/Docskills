# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 538], ["South", 227], ["East", 481], ["West", 297]]:
    ws.append(r)

wb.save("task_000086_wb.xlsx")
print("ok")
