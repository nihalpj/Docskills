# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 509], ["South", 441], ["East", 156], ["West", 101]]:
    ws.append(r)

wb.save("task_000535_wb.xlsx")
print("ok")
