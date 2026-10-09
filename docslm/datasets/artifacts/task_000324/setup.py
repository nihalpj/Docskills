# setup: workbook fixture (workbook for inspection)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 117], ["South", 306], ["East", 627], ["West", 824]]:
    ws.append(r)

wb.save("task_000324_wb.xlsx")
print("ok")
