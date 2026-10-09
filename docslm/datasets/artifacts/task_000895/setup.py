# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 862], ["South", 334], ["East", 525], ["West", 866]]:
    ws.append(r)

wb.save("task_000895_wb.xlsx")
print("ok")
