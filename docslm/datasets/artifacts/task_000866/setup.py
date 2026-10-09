# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 663], ["South", 735], ["East", 829], ["West", 478]]:
    ws.append(r)

wb.save("task_000866_wb.xlsx")
print("ok")
