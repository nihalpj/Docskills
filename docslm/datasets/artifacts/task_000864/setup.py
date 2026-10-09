# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 691], ["South", 255], ["East", 397], ["West", 134]]:
    ws.append(r)

wb.save("task_000864_wb.xlsx")
print("ok")
