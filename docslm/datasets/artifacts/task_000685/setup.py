# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 295], ["South", 842], ["East", 465], ["West", 522]]:
    ws.append(r)

wb.save("task_000685_wb.xlsx")
print("ok")
