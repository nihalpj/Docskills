# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 361], ["South", 229], ["East", 540], ["West", 464]]:
    ws.append(r)

wb.save("task_000026_wb.xlsx")
print("ok")
