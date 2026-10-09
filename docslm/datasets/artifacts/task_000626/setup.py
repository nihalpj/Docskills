# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 544], ["South", 282], ["East", 308], ["West", 457]]:
    ws.append(r)

wb.save("task_000626_wb.xlsx")
print("ok")
