# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 147], ["South", 754], ["East", 240], ["West", 819]]:
    ws.append(r)

wb.save("task_000415_wb.xlsx")
print("ok")
