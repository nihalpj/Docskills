# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 335], ["South", 698], ["East", 184], ["West", 794]]:
    ws.append(r)

wb.save("task_000655_wb.xlsx")
print("ok")
