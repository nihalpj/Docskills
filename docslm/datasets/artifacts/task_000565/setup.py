# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 648], ["South", 767], ["East", 633], ["West", 292]]:
    ws.append(r)

wb.save("task_000565_wb.xlsx")
print("ok")
