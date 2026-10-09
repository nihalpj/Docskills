# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 876], ["South", 809], ["East", 270], ["West", 206]]:
    ws.append(r)

wb.save("task_000805_wb.xlsx")
print("ok")
