# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 494], ["South", 800], ["East", 763], ["West", 346]]:
    ws.append(r)

wb.save("task_000205_wb.xlsx")
print("ok")
