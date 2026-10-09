# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 153], ["South", 600], ["East", 264], ["West", 621]]:
    ws.append(r)

wb.save("task_000295_wb.xlsx")
print("ok")
