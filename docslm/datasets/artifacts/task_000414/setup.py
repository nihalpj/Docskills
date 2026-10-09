# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 655], ["South", 436], ["East", 538], ["West", 101]]:
    ws.append(r)

wb.save("task_000414_wb.xlsx")
print("ok")
