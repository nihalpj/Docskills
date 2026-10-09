# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 732], ["South", 412], ["East", 771], ["West", 691]]:
    ws.append(r)

wb.save("task_000354_wb.xlsx")
print("ok")
