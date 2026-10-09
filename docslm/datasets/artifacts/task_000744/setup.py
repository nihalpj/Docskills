# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 170], ["South", 668], ["East", 556], ["West", 847]]:
    ws.append(r)

wb.save("task_000744_wb.xlsx")
print("ok")
