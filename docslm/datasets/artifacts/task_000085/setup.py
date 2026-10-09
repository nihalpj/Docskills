# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 244], ["South", 280], ["East", 573], ["West", 544]]:
    ws.append(r)

wb.save("task_000085_wb.xlsx")
print("ok")
