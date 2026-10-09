# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 771], ["South", 676], ["East", 344], ["West", 663]]:
    ws.append(r)

wb.save("task_000624_wb.xlsx")
print("ok")
