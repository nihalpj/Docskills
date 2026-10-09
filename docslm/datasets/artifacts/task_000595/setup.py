# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 542], ["South", 421], ["East", 621], ["West", 428]]:
    ws.append(r)

wb.save("task_000595_wb.xlsx")
print("ok")
