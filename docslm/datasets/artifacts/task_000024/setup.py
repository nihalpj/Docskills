# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 123], ["South", 480], ["East", 198], ["West", 893]]:
    ws.append(r)

wb.save("task_000024_wb.xlsx")
print("ok")
