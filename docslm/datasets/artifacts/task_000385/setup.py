# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 118], ["South", 603], ["East", 611], ["West", 251]]:
    ws.append(r)

wb.save("task_000385_wb.xlsx")
print("ok")
