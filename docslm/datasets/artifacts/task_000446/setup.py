# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 418], ["South", 553], ["East", 864], ["West", 455]]:
    ws.append(r)

wb.save("task_000446_wb.xlsx")
print("ok")
