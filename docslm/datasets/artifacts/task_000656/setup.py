# setup: workbook fixture (workbook for formula audit)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 331], ["South", 691], ["East", 730], ["West", 541]]:
    ws.append(r)

wb.save("task_000656_wb.xlsx")
print("ok")
