# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 535], ["South", 442], ["East", 412], ["West", 319]]:
    ws.append(r)

wb.save("task_000325_wb.xlsx")
print("ok")
