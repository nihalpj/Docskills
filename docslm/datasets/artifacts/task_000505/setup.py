# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 654], ["South", 712], ["East", 703], ["West", 384]]:
    ws.append(r)

wb.save("task_000505_wb.xlsx")
print("ok")
