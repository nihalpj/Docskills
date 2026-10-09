# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 111], ["South", 567], ["East", 877], ["West", 282]]:
    ws.append(r)

wb.save("task_000836_wb.xlsx")
print("ok")
