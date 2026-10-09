# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 896], ["South", 645], ["East", 132], ["West", 762]]:
    ws.append(r)

wb.save("task_000175_wb.xlsx")
print("ok")
