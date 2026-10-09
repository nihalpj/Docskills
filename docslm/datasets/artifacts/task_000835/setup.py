# setup: workbook fixture (clean workbook for scanning)
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Region", "Revenue"])
for r in [["North", 785], ["South", 486], ["East", 232], ["West", 654]]:
    ws.append(r)

wb.save("task_000835_wb.xlsx")
print("ok")
